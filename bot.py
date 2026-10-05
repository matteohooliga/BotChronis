"""Point d'entrée de Chronis : démarrage, tâches planifiées et commandes +."""

import asyncio
import csv
import datetime as dt
import io
import json
import logging
import os
from pathlib import Path
from zoneinfo import ZoneInfo

import discord
from discord import app_commands
from discord.ext import commands, tasks
from dotenv import load_dotenv

import config
from database import ChronosDatabase
from faq import answer_question
from premium import entitlement_is_active
from schedule import latest_due_weekly
from utils import create_service_embed, format_duration
from views import AbsenceView, LogPaginationView, RdvPatientView, RdvStaffView, RdvTicketView, ServiceButtonsView

load_dotenv(Path(__file__).with_name('.env'))
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s: %(message)s')
logger = logging.getLogger('chronis')
STATE_FILE = Path(__file__).with_name('restart_context.json')
PROJECT_DIR = Path(__file__).resolve().parent
PARIS = ZoneInfo('Europe/Paris')
UTC = dt.timezone.utc


def find_commands_extension():
    """Accepte les deux arborescences déjà utilisées pour déployer Chronis."""
    if (PROJECT_DIR / 'commands.py').is_file():
        return 'commands'
    if (PROJECT_DIR / 'cogs' / 'commands.py').is_file():
        return 'cogs.commands'
    raise FileNotFoundError(
        'commands.py introuvable : attendu dans /home/container/cogs/ ou /home/container/'
    )


def save_restart_state(data):
    temporary = STATE_FILE.with_suffix('.tmp')
    temporary.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
    temporary.replace(STATE_FILE)


def get_channel_id(value):
    try:
        return int(value) if value else None
    except (TypeError, ValueError):
        return None


class ChronisTree(app_commands.CommandTree):
    async def interaction_check(self, interaction):
        if getattr(interaction.client, 'maintenance_mode', False) and str(interaction.user.id) != str(config.OWNER_ID):
            await interaction.response.send_message(
                config.TRANSLATIONS['fr']['maint_block_msg'], ephemeral=True
            )
            return False
        return True


class DMReplyModal(discord.ui.Modal):
    def __init__(self, bot, user_id):
        super().__init__(title='Répondre au message privé')
        self.bot = bot
        self.user_id = user_id
        self.reply_text = discord.ui.TextInput(
            label='Réponse à envoyer', style=discord.TextStyle.paragraph,
            required=True, max_length=1800
        )
        self.add_item(self.reply_text)

    async def on_submit(self, interaction):
        if str(interaction.user.id) != str(config.OWNER_ID):
            return await interaction.response.send_message('⛔ Réservé au propriétaire du bot.', ephemeral=True)
        try:
            user = self.bot.get_user(self.user_id) or await self.bot.fetch_user(self.user_id)
            await user.send(
                self.reply_text.value,
                allowed_mentions=discord.AllowedMentions.none()
            )
        except discord.DiscordException:
            logger.exception('Réponse MP impossible pour %s', self.user_id)
            return await interaction.response.send_message(
                '❌ Impossible d’envoyer le MP. Le destinataire bloque peut-être les messages du bot.',
                ephemeral=True
            )
        await interaction.response.send_message('✅ Réponse envoyée.', ephemeral=True)


class DMReplyView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label='Répondre', style=discord.ButtonStyle.primary,
                       custom_id='chronis:dm_reply')
    async def reply(self, interaction, button):
        if str(interaction.user.id) != str(config.OWNER_ID):
            return await interaction.response.send_message('⛔ Réservé au propriétaire du bot.', ephemeral=True)
        embed = interaction.message.embeds[0] if interaction.message.embeds else None
        field = next((item for item in embed.fields if item.name == 'Utilisateur'), None) if embed else None
        user_id = str(field.value).rsplit('(', 1)[-1].rstrip(')') if field else ''
        if not user_id.isdigit():
            return await interaction.response.send_message('❌ Identifiant du destinataire introuvable.', ephemeral=True)
        await interaction.response.send_modal(DMReplyModal(self.bot, int(user_id)))


class ChronosBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix=commands.when_mentioned_or('+'), intents=intents, help_command=None, tree_cls=ChronisTree)
        self.db = ChronosDatabase()
        self.maintenance_mode = False
        self._restart_requested = False
        self._ready_initialized = False
        self._last_reminders = set()
        self._panel_failures = {}
        self._paid_premium_cache = {}
        self._restart_state_lock = asyncio.Lock()
        self.commands_extension = find_commands_extension()

    async def setup_hook(self):
        await self.db.initialize_database()
        self.maintenance_mode = await self.db.get_global_maintenance()
        logger.info('Chargement des commandes depuis %s', self.commands_extension)
        await self.load_extension(self.commands_extension)
        logger.info('Commandes préfixées enregistrées : %s', ', '.join(sorted(c.name for c in self.commands)))
        self.add_view(DMReplyView(self))
        self.add_view(ServiceButtonsView(self))
        self.add_view(RdvStaffView(self))
        self.add_view(RdvTicketView(self))
        self.add_view(AbsenceView(self))
        for data in await self.db.get_all_guild_configs():
            if not data.get('rdv_message_id') or not data.get('rdv_types'):
                continue
            try:
                types = json.loads(data['rdv_types'])
                self.add_view(RdvPatientView(self, types, data.get('language') or 'fr'),
                              message_id=int(data['rdv_message_id']))
            except (ValueError, TypeError, KeyError):
                logger.exception('Panneau RDV invalide pour %s', data['guild_id'])
        self.status_task.start()
        self.scheduled_restart.start()
        self.auto_purge_task.start()
        self.quota_reminder_task.start()
        self.restart_recovery_task.start()

    async def close(self):
        for loop in (self.status_task, self.scheduled_restart,
                     self.auto_purge_task, self.quota_reminder_task,
                     self.restart_recovery_task):
            if loop.is_running() and loop.get_task() is not asyncio.current_task():
                loop.cancel()
        await self.db.close_pool()
        await super().close()

    async def on_ready(self):
        logger.info('Connecté en tant que %s (%s)', self.user, self.user.id)
        if not self._ready_initialized:
            try:
                self.maintenance_mode = await self.db.get_global_maintenance()
            except Exception:
                logger.exception('Lecture du mode maintenance impossible ; conservation de l’état chargé au démarrage')
            self._ready_initialized = True
            await self.update_status()
            await self._handle_restart_context()
            # La boucle de rafraîchissement du Cog met les panneaux à jour.
            # Éviter ici une deuxième vague de requêtes Discord au démarrage.
        else:
            await self.update_status()
            await self._handle_restart_context()

    async def on_guild_join(self, guild):
        txt = config.TRANSLATIONS['fr']
        await self.send_system_log(
            txt['log_guild_join_title'], txt['log_guild_join_desc'], discord.Color.green(),
            [(txt['log_guild_join_name'], guild.name), (txt['log_guild_join_id'], str(guild.id)),
             (txt['log_guild_join_owner'], str(guild.owner)),
             (txt['log_guild_join_members'], str(guild.member_count))]
        )

    async def get_guild_lang(self, guild_id):
        data = await self.db.get_guild_config(str(guild_id)) if guild_id else None
        return data.get('language', 'fr') if data else 'fr'

    async def _channel(self, channel_id):
        channel_id = get_channel_id(channel_id)
        if not channel_id:
            return None
        return self.get_channel(channel_id) or await self.fetch_channel(channel_id)

    async def send_log(self, guild_id, title, description, color, fields=None):
        data = await self.db.get_guild_config(str(guild_id))
        if not data or not data.get('log_channel_id'):
            return None
        return await self._send_embed(data['log_channel_id'], title, description, color, fields)

    async def send_system_log(self, title, description, color, fields=None, view=None):
        if not config.DEV_LOG_CHANNEL_ID:
            return None
        return await self._send_embed(config.DEV_LOG_CHANNEL_ID, title, description, color, fields, view)

    async def _send_embed(self, channel_id, title, description, color, fields=None, view=None):
        try:
            channel = await self._channel(channel_id)
            embed = discord.Embed(title=title, description=description, color=color,
                                  timestamp=dt.datetime.now(UTC))
            for name, value in fields or []:
                embed.add_field(name=str(name), value=str(value), inline=True)
            embed.set_footer(text='Chronis')
            return await channel.send(embed=embed, view=view)
        except (discord.DiscordException, ValueError):
            logger.exception('Envoi du log impossible dans %s', channel_id)
            return None

    def _remember_panel_issue(self, guild_id, signature, reason, description, cooldown=600):
        key = str(guild_id)
        previous = self._panel_failures.get(key)
        if not previous or previous[0] != signature or previous[1] != reason:
            logger.warning('Panneau %s : %s', guild_id, description)
        self._panel_failures[key] = (
            signature, reason, asyncio.get_running_loop().time() + cooldown
        )

    async def update_service_message(self, guild_id, config_data=None, active_sessions=None):
        data = config_data or await self.db.get_guild_config(str(guild_id))
        if not data or not data.get('channel_id') or not data.get('message_id'):
            return False
        guild = self.get_guild(int(guild_id))
        if guild is None:
            # Ancienne configuration d'un serveur que le bot a quitté.
            return False
        signature = (str(data['channel_id']), str(data['message_id']))
        previous = self._panel_failures.get(str(guild_id))
        if previous and previous[0] == signature and asyncio.get_running_loop().time() < previous[2]:
            return False
        try:
            channel = guild.get_channel(int(data['channel_id'])) or await self._channel(data['channel_id'])
            if channel is None or channel.guild.id != guild.id:
                raise ValueError('Salon de service absent ou associé à un autre serveur')
            active = active_sessions if active_sessions is not None else await self.db.get_all_active_sessions(str(guild_id))
            embed = create_service_embed(active, guild, data.get('language') or 'fr',
                                         self.maintenance_mode)
            await channel.get_partial_message(int(data['message_id'])).edit(embed=embed)
        except discord.Forbidden:
            self._remember_panel_issue(
                guild_id, signature, 'forbidden',
                'accès refusé au salon. Donnez au bot Voir le salon et les droits de message, ou reconfigurez /setup.'
            )
            return False
        except discord.NotFound:
            self._remember_panel_issue(
                guild_id, signature, 'not_found',
                'salon ou message supprimé. Relancez /setup pour créer un nouveau panneau.'
            )
            return False
        except (ValueError, TypeError, AttributeError) as error:
            self._remember_panel_issue(guild_id, signature, 'invalid', str(error))
            return False
        except discord.HTTPException as error:
            self._remember_panel_issue(guild_id, signature, 'http', f'erreur Discord temporaire : {error}', 60)
            return False
        self._panel_failures.pop(str(guild_id), None)
        return True

    async def get_premium_sources(self):
        manual_ids = await self.db.get_manual_premium_guild_ids()
        paid_ids = set()
        paid_status_known = True
        try:
            async for entitlement in self.entitlements(
                skus=[discord.Object(id=config.PREMIUM_SKU_ID)],
                exclude_ended=True, limit=None
            ):
                if (entitlement.guild_id is not None
                        and entitlement_is_active(entitlement, config.PREMIUM_SKU_ID)):
                    paid_ids.add(int(entitlement.guild_id))
        except discord.DiscordException:
            logger.exception('Lecture des abonnements Chronis Premium impossible')
            paid_status_known = False
        return manual_ids, paid_ids, paid_status_known

    async def is_premium(self, interaction):
        if interaction.guild_id and await self.db.has_manual_premium(interaction.guild_id):
            return True
        return any(entitlement_is_active(entitlement, config.PREMIUM_SKU_ID)
                   for entitlement in interaction.entitlements)

    async def guild_has_premium(self, guild_id):
        if await self.db.has_manual_premium(guild_id):
            return True
        key = int(guild_id)
        now = asyncio.get_running_loop().time()
        cached = self._paid_premium_cache.get(key)
        if cached and cached[0] > now:
            return cached[1]
        try:
            active = False
            async for entitlement in self.entitlements(
                skus=[discord.Object(id=config.PREMIUM_SKU_ID)],
                guild=discord.Object(id=key), exclude_ended=True, limit=None
            ):
                if (entitlement.guild_id == key
                        and entitlement_is_active(entitlement, config.PREMIUM_SKU_ID)):
                    active = True
                    break
        except discord.DiscordException:
            logger.exception('Vérification Premium impossible pour le serveur %s', guild_id)
            return False
        self._paid_premium_cache[key] = (now + 300, active)
        return active

    async def refresh_all_service_panels(self):
        for data in await self.db.get_all_guild_configs():
            if self.get_guild(int(data['guild_id'])) is not None:
                await self.update_service_message(int(data['guild_id']), data)

    async def update_status(self):
        try:
            if self._restart_requested:
                await self.change_presence(status=discord.Status.dnd,
                                           activity=discord.Game(name='Redémarrage en cours'))
            elif self.maintenance_mode:
                await self.change_presence(status=discord.Status.dnd,
                                           activity=discord.Game(name='Maintenance en cours'))
            else:
                try:
                    total = await self.db.get_total_active_sessions_count()
                    activity_name = f'{total} agents actifs | {round(self.latency * 1000)}ms | /about'
                except Exception:
                    logger.exception('Nombre de sessions indisponible pour le statut Discord')
                    activity_name = 'Chronis en ligne | /about'
                activity = discord.Activity(type=discord.ActivityType.watching,
                                            name=activity_name)
                await self.change_presence(status=discord.Status.online, activity=activity)
        except (discord.DiscordException, ValueError):
            logger.exception('Statut Discord impossible à mettre à jour')

    @tasks.loop(seconds=30)
    async def status_task(self):
        await self.update_status()

    @status_task.before_loop
    async def before_status_task(self):
        await self.wait_until_ready()

    @tasks.loop(minutes=1)
    async def auto_purge_task(self):
        now = dt.datetime.now(UTC)
        try:
            configs = await self.db.get_all_guild_configs()
        except Exception:
            logger.exception('Lecture des réglages hebdomadaires impossible')
            return
        for data in configs:
            try:
                await self._run_weekly_report(data, now)
            except Exception:
                logger.exception('Bilan hebdomadaire échoué pour %s ; nouvel essai dans une minute', data['guild_id'])

    async def _run_weekly_report(self, data, now):
        guild_id = str(data['guild_id'])
        day = int(data.get('auto_purge_day') if data.get('auto_purge_day') is not None else -1)
        if day < 0:
            return
        due = latest_due_weekly(now, day, data.get('auto_purge_time') or '00:00')
        if due is None or not await self.guild_has_premium(guild_id):
            return
        # Si le réglage vient d'être créé après l'échéance, attendre la suivante.
        updated = int(data.get('updated_at') or 0)
        if updated and due.timestamp() < updated:
            return
        run_date = due.date()
        run = await self.db.get_weekly_run(guild_id, run_date)
        if run and run['status'] == 'done':
            return
        if run and run['status'] == 'sent':
            await self.db.reset_weekly_data(guild_id, run['cutoff_ms'])
            await self.db.set_weekly_run(guild_id, run_date, 'done', run['total_ms'], run['cutoff_ms'])
            await self.update_service_message(int(guild_id), data, [])
            return

        guild = self.get_guild(int(guild_id))
        if not guild:
            return
        log_channel = await self._channel(data.get('log_channel_id'))
        if not log_channel:
            logger.warning('Bilan %s impossible : salon des logs absent pour %s', run_date, guild_id)
            return
        for session in await self.db.get_all_active_sessions(guild_id):
            await self.db.end_session(session['user_id'], guild_id)
        cutoff_ms = int(dt.datetime.now(UTC).timestamp() * 1000)
        stats = await self.db.get_all_users_stats(guild_id)
        total_ms = sum(int(row['total_time'] or 0) for row in stats)
        previous_ms = await self.db.get_previous_weekly_total(guild_id, run_date)
        if previous_ms:
            variation = (total_ms - previous_ms) / previous_ms * 100
            trend = f'{"📈" if variation >= 0 else "📉"} {variation:+.1f} % par rapport au bilan précédent'
        else:
            trend = 'Premier bilan enregistré'
        output = io.StringIO()
        writer = csv.writer(output, delimiter=';')
        writer.writerow(['ID Utilisateur', 'Nom / Pseudo', 'Total Sessions', 'Temps Total'])
        for row in stats:
            writer.writerow([row['user_id'], row['username'], row['total_sessions'],
                             format_duration(int(row['total_time'] or 0))])
        file = discord.File(io.BytesIO(output.getvalue().encode('utf-8-sig')),
                            filename=f'bilan_{guild_id}_{run_date}.csv')
        embed = discord.Embed(title='📊 Bilan de performance hebdomadaire',
                              description=f'Période close le {due:%d/%m/%Y à %H:%M}.',
                              color=config.BOT_COLOR, timestamp=dt.datetime.now(UTC))
        embed.add_field(name='Temps total', value=format_duration(total_ms))
        embed.add_field(name='Tendance', value=trend)
        # L'envoi précède l'effacement. Si Discord est indisponible, les données restent.
        await log_channel.send(embed=embed, file=file)
        await self.db.set_weekly_run(guild_id, run_date, 'sent', total_ms, cutoff_ms)
        await self.db.reset_weekly_data(guild_id, cutoff_ms)
        await self.db.set_weekly_run(guild_id, run_date, 'done', total_ms, cutoff_ms)
        await self.update_service_message(int(guild_id), data, [])

    @auto_purge_task.before_loop
    async def before_auto_purge(self):
        await self.wait_until_ready()

    @tasks.loop(minutes=1)
    async def quota_reminder_task(self):
        now = dt.datetime.now(UTC)
        try:
            configs = await self.db.get_all_guild_configs()
        except Exception:
            logger.exception('Lecture des réglages de quota impossible')
            return
        for data in configs:
            try:
                await self._send_quota_reminders(data, now)
            except Exception:
                logger.exception('Rappels de quota échoués pour %s', data['guild_id'])

    async def _send_quota_reminders(self, data, now):
        day = int(data.get('auto_purge_day') if data.get('auto_purge_day') is not None else -1)
        goal = int(data.get('min_hours_goal') or 0)
        if day < 0 or goal <= 0:
            return
        due = latest_due_weekly(now, day, data.get('auto_purge_time') or '00:00')
        upcoming = due + dt.timedelta(days=7)
        local_now = now.astimezone(PARIS)
        if not dt.timedelta(hours=23) <= upcoming - local_now <= dt.timedelta(hours=24):
            return
        guild_id = str(data['guild_id'])
        if not await self.guild_has_premium(guild_id):
            return
        key = (guild_id, upcoming.date())
        if key in self._last_reminders:
            return
        guild = self.get_guild(int(guild_id))
        if not guild:
            return
        stats = await self.db.get_all_users_stats(guild_id)
        absent = set(await self.db.get_absent_users(guild_id))
        panel_url = f'https://discord.com/channels/{guild_id}/{data.get("channel_id")}/{data.get("message_id")}'
        for row in stats:
            if str(row['user_id']) in absent or int(row['total_time'] or 0) >= goal:
                continue
            try:
                user = self.get_user(int(row['user_id'])) or await self.fetch_user(int(row['user_id']))
                missing = format_duration(goal - int(row['total_time'] or 0))
                await user.send(f'⚠️ Il vous reste environ 24 heures pour atteindre votre objectif sur **{guild.name}**. '
                                f'Temps manquant : **{missing}**. {panel_url}')
            except discord.DiscordException:
                logger.info('MP de rappel non délivré à %s', row['user_id'])
        self._last_reminders.add(key)

    @quota_reminder_task.before_loop
    async def before_quota_reminder(self):
        await self.wait_until_ready()

    @tasks.loop(time=dt.time(hour=4, minute=0, tzinfo=PARIS))
    async def scheduled_restart(self):
        logger.info('Maintenance quotidienne de 04:00 Europe/Paris')
        await self.request_restart('daily')

    @scheduled_restart.before_loop
    async def before_scheduled_restart(self):
        await self.wait_until_ready()

    @tasks.loop(minutes=1)
    async def restart_recovery_task(self):
        if STATE_FILE.exists():
            await self._handle_restart_context()

    @restart_recovery_task.before_loop
    async def before_restart_recovery(self):
        await self.wait_until_ready()

    async def request_restart(self, reason):
        if self._restart_requested:
            return
        self._restart_requested = True
        state = {'logs': []}
        try:
            if reason == 'daily':
                for data in await self.db.get_all_guild_configs():
                    guild_id = str(data['guild_id'])
                    if self.get_guild(int(guild_id)) is None:
                        continue
                    try:
                        for session in await self.db.get_all_active_sessions(guild_id):
                            await self.db.end_session(session['user_id'], guild_id)
                        await self.update_service_message(int(guild_id), data, [])
                    except Exception:
                        logger.exception('Maintenance incomplète pour %s', guild_id)
            log = await self.send_system_log('🔄 Redémarrage Chronis', reason, discord.Color.gold(),
                                             [('État', 'En cours')])
            if log:
                state['logs'].append({'channel_id': log.channel.id, 'message_id': log.id})
            save_restart_state(state)
            await self.update_status()
            await asyncio.sleep(2)
            await self.close()
        except Exception:
            self._restart_requested = False
            await self.update_status()
            logger.exception('Redémarrage non déclenché')
            raise
        # Un gestionnaire de processus doit relancer le programme après sa sortie.

    async def _handle_restart_context(self):
        async with self._restart_state_lock:
            await self._apply_restart_context()

    async def _apply_restart_context(self):
        if not STATE_FILE.exists():
            return
        try:
            state = json.loads(STATE_FILE.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            logger.exception('Contexte de redémarrage illisible')
            return
        # Nettoie les anciennes annonces publiées dans les autres serveurs.
        messages = list(state.get('messages', []))
        if state.get('manual_channel_id') and state.get('manual_message_id'):
            messages.append({'channel_id': state['manual_channel_id'],
                             'message_id': state['manual_message_id']})
        logs = list(state.get('logs', state.get('log_messages', [])))
        pending = {'messages': [], 'logs': []}
        for item in messages:
            try:
                channel = await self._channel(item['channel_id'])
                original = await channel.fetch_message(int(item['message_id']))
                if original.author.id == self.user.id:
                    await original.delete()
            except discord.NotFound:
                logger.warning('Annonce de redémarrage supprimée : %s', item)
            except (discord.DiscordException, KeyError, ValueError, AttributeError):
                logger.exception('Ancienne annonce de redémarrage non supprimée : %s', item)
                pending['messages'].append(item)
        for item in logs:
            try:
                if get_channel_id(item['channel_id']) != get_channel_id(config.DEV_LOG_CHANNEL_ID):
                    logger.warning('Log de redémarrage hors serveur de développement ignoré : %s', item)
                    continue
                channel = await self._channel(item['channel_id'])
                original = await channel.fetch_message(int(item['message_id']))
                if original.embeds:
                    embed = discord.Embed.from_dict(original.embeds[0].to_dict())
                    embed.color = discord.Color.green()
                    embed.clear_fields()
                    embed.add_field(name='État', value='Terminé ✅')
                    embed.timestamp = dt.datetime.now(UTC)
                    await original.edit(embed=embed)
            except discord.NotFound:
                logger.warning('Log de redémarrage supprimé : %s', item)
            except (discord.DiscordException, KeyError, ValueError, AttributeError):
                logger.exception('Log de redémarrage non mis à jour : %s', item)
                pending['logs'].append(item)
        if pending['messages'] or pending['logs']:
            save_restart_state(pending)
        else:
            STATE_FILE.unlink(missing_ok=True)

    async def on_message(self, message):
        if message.author.bot:
            return
        if message.guild is None:
            await self._handle_dm(message)
        await self.process_commands(message)

    async def _handle_dm(self, message):
        if message.content.strip().startswith('+'):
            return
        answer = answer_question(message.content)
        if answer:
            try:
                await message.channel.send(answer)
            except discord.DiscordException:
                logger.exception('Réponse MP impossible pour %s', message.author.id)
        elif message.content.strip():
            try:
                await message.channel.send('Je n’ai pas de réponse fiable à cette question. Utilisez `/help` sur un serveur où Chronis est présent, ou contactez son administrateur.')
            except discord.DiscordException:
                logger.exception('Réponse MP impossible pour %s', message.author.id)
        if config.DEV_LOG_CHANNEL_ID:
            description = (message.content or '[pièce jointe]').strip()[:3900]
            await self.send_system_log('📩 Nouveau MP reçu', description, discord.Color.blue(),
                                       [('Utilisateur', f'{message.author} ({message.author.id})')],
                                       view=DMReplyView(self))


def main():
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        raise SystemExit('DISCORD_TOKEN manque dans .env ou dans l’environnement')
    bot = ChronosBot()

    @bot.check
    async def globally_block_blacklisted(ctx):
        return not await bot.db.is_blacklisted(str(ctx.author.id))

    @bot.command()
    async def help(ctx):
        await ctx.send('Commandes publiques : `+help`.\n'
                       'Administrateurs : `+sync`, `+restart`.\n'
                       'Propriétaire du bot : `+infos`, `+premium_list`, '
                       '`+add_premium <ID>`, `+remove_premium <ID>`, '
                       '`+maintenance [statut|on|off]`, `+sync_global`, '
                       '`+fix_doublons`, `+debug`, `+start`, `+stop`.')

    @bot.command(name='infos', aliases=['info'])
    @commands.check(lambda ctx: str(ctx.author.id) == str(config.OWNER_ID))
    async def infos(ctx):
        guilds = sorted(bot.guilds, key=lambda guild: guild.member_count if guild.member_count is not None else -1, reverse=True)
        if not guilds:
            return await ctx.send('Chronis n’est actuellement présent sur aucun serveur.')
        manual_ids, paid_ids, paid_status_known = await bot.get_premium_sources()
        rows = []
        for index, guild in enumerate(guilds, start=1):
            name = discord.utils.escape_markdown(guild.name)
            count = str(guild.member_count) if guild.member_count is not None else 'inconnu'
            owner = f'<@{guild.owner_id}>' if guild.owner_id else 'inconnu'
            premium = ('✅ Oui (manuel)' if guild.id in manual_ids else
                       '✅ Oui (Discord)' if guild.id in paid_ids else
                       '❌ Non' if paid_status_known else '⚠️ Inconnu')
            rows.append(f'**{index}. {name}** — **{count}** membres\n'
                        f'ID : `{guild.id}` • Owner : {owner}\n'
                        f'Chronis Premium : **{premium}**')
        view = LogPaginationView(rows, title='🌍 Serveurs de Chronis — du plus au moins de membres', items_per_page=10)
        view.update_buttons()
        await ctx.send(embed=view.create_embed(), view=view, allowed_mentions=discord.AllowedMentions.none())

    @bot.command(name='premium_list')
    @commands.check(lambda ctx: str(ctx.author.id) == str(config.OWNER_ID))
    async def premium_list(ctx):
        manual_ids, paid_ids, paid_status_known = await bot.get_premium_sources()
        guilds = sorted((guild for guild in bot.guilds
                         if guild.id in manual_ids or guild.id in paid_ids),
                        key=lambda guild: guild.member_count or 0, reverse=True)
        if not guilds:
            if not paid_status_known:
                return await ctx.send('⚠️ Aucun droit manuel trouvé ; abonnements Discord indisponibles.')
            return await ctx.send('Aucun serveur Chronis Premium actuellement.')
        rows = []
        for index, guild in enumerate(guilds, start=1):
            sources = []
            if guild.id in manual_ids:
                sources.append('manuel')
            if guild.id in paid_ids:
                sources.append('Discord')
            rows.append(f'**{index}. {discord.utils.escape_markdown(guild.name)}** — '
                        f'ID : `{guild.id}` • Premium : {" + ".join(sources)}')
        view = LogPaginationView(rows, title='💎 Serveurs Chronis Premium', items_per_page=10)
        view.update_buttons()
        if not paid_status_known:
            await ctx.send('⚠️ Discord est indisponible : seuls les droits manuels sont confirmés.')
        await ctx.send(embed=view.create_embed(), view=view,
                       allowed_mentions=discord.AllowedMentions.none())

    @bot.command(name='add_premium')
    @commands.check(lambda ctx: str(ctx.author.id) == str(config.OWNER_ID))
    async def add_premium(ctx, server_id: int):
        guild = bot.get_guild(server_id)
        if guild is None:
            return await ctx.send('❌ Chronis doit être présent sur ce serveur. Vérifie son ID.')
        await bot.db.grant_manual_premium(server_id, ctx.author.id)
        bot._paid_premium_cache.pop(server_id, None)
        await ctx.send(f'✅ Chronis Premium activé manuellement pour **{discord.utils.escape_markdown(guild.name)}** (`{server_id}`).')

    @bot.command(name='remove_premium')
    @commands.check(lambda ctx: str(ctx.author.id) == str(config.OWNER_ID))
    async def remove_premium(ctx, server_id: int):
        removed = await bot.db.revoke_manual_premium(server_id)
        bot._paid_premium_cache.pop(server_id, None)
        _, paid_ids, paid_status_known = await bot.get_premium_sources()
        if server_id in paid_ids:
            return await ctx.send(
                f'✅ Droit manuel {"retiré" if removed else "absent"} pour `{server_id}`. '
                'L’abonnement Discord est toujours actif et doit être géré dans Discord.'
            )
        if not paid_status_known:
            return await ctx.send(
                f'✅ Droit manuel {"retiré" if removed else "absent"} pour `{server_id}`. '
                '⚠️ Statut de l’abonnement Discord indisponible.'
            )
        await ctx.send(f'✅ Droit manuel {"retiré" if removed else "absent"} pour `{server_id}`. '
                       'Ce serveur n’a plus Chronis Premium.')

    @bot.command(name='maintenance')
    @commands.check(lambda ctx: str(ctx.author.id) == str(config.OWNER_ID))
    async def maintenance(ctx, etat: str = 'statut'):
        action = etat.casefold()
        if action in ('statut', 'status', 'etat', 'état'):
            state = 'activée' if bot.maintenance_mode else 'désactivée'
            return await ctx.send(f'Maintenance globale : **{state}**. Utilise `+maintenance on` ou `+maintenance off`.')
        if action in ('on', 'activer', 'active'):
            enabled = True
        elif action in ('off', 'desactiver', 'désactiver', 'inactive'):
            enabled = False
        else:
            return await ctx.send('Utilise `+maintenance statut`, `+maintenance on` ou `+maintenance off`.')
        await bot.db.set_global_maintenance(enabled)
        bot.maintenance_mode = enabled
        await bot.update_status()
        await ctx.send(f'🚧 Maintenance globale **{"activée" if enabled else "désactivée"}**. '
                       'Les panneaux et commandes `/` sont désormais réservés au propriétaire.' if enabled
                       else '✅ Maintenance globale désactivée : les panneaux sont de nouveau accessibles.')
        asyncio.create_task(bot.refresh_all_service_panels())

    @bot.command()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def sync(ctx):
        bot.tree.copy_global_to(guild=ctx.guild)
        synced = await bot.tree.sync(guild=ctx.guild)
        await ctx.send(f'✅ {len(synced)} commandes synchronisées sur ce serveur.')

    @bot.command()
    @commands.check(lambda ctx: str(ctx.author.id) == str(config.OWNER_ID))
    async def sync_global(ctx):
        synced = await bot.tree.sync()
        await ctx.send(f'✅ {len(synced)} commandes globales synchronisées.')

    @bot.command()
    @commands.check(lambda ctx: str(ctx.author.id) == str(config.OWNER_ID))
    async def fix_doublons(ctx):
        if ctx.guild is None:
            return await ctx.send('Commande disponible sur un serveur uniquement.')
        bot.tree.clear_commands(guild=ctx.guild)
        await bot.tree.sync(guild=ctx.guild)
        await ctx.send('✅ Commandes locales supprimées ; commandes globales conservées.')

    @bot.command()
    @commands.check(lambda ctx: str(ctx.author.id) == str(config.OWNER_ID))
    async def debug(ctx):
        await bot.reload_extension(bot.commands_extension)
        await ctx.send('✅ Extension rechargée.')

    @bot.command()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def restart(ctx):
        await ctx.send('🔄 Redémarrage demandé. La confirmation sera publiée sur le serveur de développement.')
        await bot.request_restart('manual')

    @bot.command(name='start')
    @commands.check(lambda ctx: str(ctx.author.id) == str(config.OWNER_ID))
    async def start(ctx):
        await ctx.send('✅ **Bot en ligne !**')

    @bot.command()
    @commands.check(lambda ctx: str(ctx.author.id) == str(config.OWNER_ID))
    async def stop(ctx):
        await ctx.send('🛑 Arrêt du bot.')
        await bot.close()

    @bot.event
    async def on_command_error(ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return await ctx.send('❓ Commande `+` inconnue. Utilise `+help` pour voir celles qui existent.')
        if isinstance(error, commands.MissingPermissions):
            return await ctx.send('⛔ Cette commande est réservée aux administrateurs.')
        if isinstance(error, (commands.NotOwner, commands.CheckFailure)):
            return await ctx.send('⛔ Cette commande est réservée au propriétaire du bot.')
        logger.error('Commande + échouée', exc_info=(type(error), error, error.__traceback__))
        await ctx.send('❌ La commande a échoué. Consultez les logs du bot.')

    bot.run(token)
    # Une sortie non nulle demande au gestionnaire de processus de relancer Chronis.
    if bot._restart_requested:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
