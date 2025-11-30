import discord
import config
import json
import sys
import io
from datetime import datetime, timedelta
from utils import format_duration, check_permissions, create_all_stats_embed, create_graph, create_server_stats_embed, create_service_embed

# --- FONCTION UTILITAIRE (LOGS FEEDBACK DEV) ---
async def send_feedback_log(bot, interaction, title, color, fields):
    target_id = config.DEV_FEEDBACK_CHANNEL_ID
    channel = bot.get_channel(target_id)
    
    if channel is None:
        try:
            channel = await bot.fetch_channel(target_id)
        except:
            return False
            
    if channel:
        embed = discord.Embed(title=title, color=color, timestamp=datetime.now())
        embed.set_author(name=f"{interaction.user.name} ({interaction.user.id})", icon_url=interaction.user.display_avatar.url)
        
        for name, value in fields:
            embed.add_field(name=name, value=value, inline=False)
            
        embed.add_field(name="Source", value=f"{interaction.guild.name} (`{interaction.guild.id}`)", inline=False)
        embed.set_footer(text=config.EMBED_FOOTER)
        
        role_mention = f"<@&{config.DEV_FEEDBACK_ROLE_ID}>"
        try:
            await channel.send(content=role_mention, embed=embed)
            return True
        except:
            return False
    return False

# --- FONCTION TRANSCRIPT (TXT SIMPLE) ---
async def generate_transcript_file(channel: discord.TextChannel):
    """Génère un fichier TXT simple contenant l'historique du salon."""
    messages = [m async for m in channel.history(limit=None, oldest_first=True)]
    
    lines = []
    lines.append("---- LOG DE TICKET ----")
    lines.append(f"Salon : {channel.name}")
    lines.append(f"Généré le : {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    lines.append("-" * 30)
    lines.append("") 
    
    for msg in messages:
        timestamp = msg.created_at.strftime('%d/%m/%Y %H:%M')
        author = msg.author.display_name
        content = msg.content
        
        if msg.embeds:
            for embed in msg.embeds:
                title = embed.title if embed.title else (embed.description[:20] + "..." if embed.description else "Embed sans titre")
                content += f"\n<EMBED {title}>"
        
        if msg.attachments:
            for attachment in msg.attachments:
                content += f"\n{attachment.url}"
                
        lines.append(f"{timestamp} - {author}: {content}")
        lines.append("") 
        
    text_content = "\n".join(lines)
    return discord.File(io.BytesIO(text_content.encode('utf-8')), filename=f"transcript-{channel.name}.txt")

# ==============================================================================
#                            MODALES (FORMULAIRES)
# ==============================================================================

class ReviewModal(discord.ui.Modal):
    def __init__(self, bot, lang):
        self.bot = bot
        self.lang = lang
        texts = config.TRANSLATIONS[lang]
        super().__init__(title=texts['fb_review_title'])
        
        self.subject = discord.ui.TextInput(label=texts['feedback_subject'], style=discord.TextStyle.short, required=True, max_length=100)
        self.rating = discord.ui.TextInput(label=texts['fb_review_rating'], style=discord.TextStyle.short, placeholder="5", required=True, max_length=1)
        self.comment = discord.ui.TextInput(label=texts['fb_review_comment'], style=discord.TextStyle.paragraph, required=True, max_length=1000)
        
        self.add_item(self.subject)
        self.add_item(self.rating)
        self.add_item(self.comment)

    async def on_submit(self, interaction: discord.Interaction):
        texts = config.TRANSLATIONS[self.lang]
        try:
            stars = max(1, min(5, int(self.rating.value)))
            star_str = "⭐" * stars
        except:
            star_str = "❓"
            
        fields = [
            ("📌 Sujet", f"**{self.subject.value}**"),
            (texts['fb_field_rating'], f"{star_str} ({self.rating.value}/5)"),
            ("💬 Commentaire", self.comment.value)
        ]
        
        success = await send_feedback_log(self.bot, interaction, texts['fb_log_review_title'], config.COLOR_ORANGE, fields)
        
        if success:
            await interaction.response.send_message(texts['feedback_sent'], ephemeral=True)
        else:
            await interaction.response.send_message(texts['feedback_error'], ephemeral=True)

class BugReportModal(discord.ui.Modal):
    def __init__(self, bot, lang):
        self.bot = bot
        self.lang = lang
        texts = config.TRANSLATIONS[lang]
        super().__init__(title=texts['fb_bug_title'])
        
        self.subject = discord.ui.TextInput(label=texts['fb_bug_subject'], style=discord.TextStyle.short, required=True, max_length=100)
        self.description = discord.ui.TextInput(label=texts['fb_bug_desc'], style=discord.TextStyle.paragraph, required=True, max_length=2000)
        self.media = discord.ui.TextInput(label=texts['fb_bug_media'], style=discord.TextStyle.short, required=False, placeholder="https://...")
        
        self.add_item(self.subject)
        self.add_item(self.description)
        self.add_item(self.media)

    async def on_submit(self, interaction: discord.Interaction):
        texts = config.TRANSLATIONS[self.lang]
        fields = [
            ("📌 Sujet", f"**{self.subject.value}**"),
            ("📝 Description", self.description.value)
        ]
        if self.media.value:
            fields.append((texts['fb_field_media'], self.media.value))
            
        success = await send_feedback_log(self.bot, interaction, texts['fb_log_bug_title'], config.COLOR_RED, fields)
        
        if success:
            await interaction.response.send_message(texts['feedback_sent'], ephemeral=True)
        else:
            await interaction.response.send_message(texts['feedback_error'], ephemeral=True)

class AbsenceModal(discord.ui.Modal):
    def __init__(self, bot, lang, direction_role_id):
        self.bot = bot
        self.lang = lang
        self.direction_role_id = direction_role_id
        texts = config.TRANSLATIONS[lang]
        super().__init__(title=texts['abs_modal_title'])
        
        self.start_date = discord.ui.TextInput(label=texts['abs_start_label'], placeholder="JJ/MM/AAAA", max_length=10, required=True)
        self.end_date = discord.ui.TextInput(label=texts['abs_end_label'], placeholder="JJ/MM/AAAA", max_length=10, required=True)
        self.reason = discord.ui.TextInput(label=texts['abs_reason_label'], style=discord.TextStyle.paragraph, required=True)
        
        self.add_item(self.start_date)
        self.add_item(self.end_date)
        self.add_item(self.reason)

    async def on_submit(self, interaction: discord.Interaction):
        texts = config.TRANSLATIONS[self.lang]
        try:
            d1 = datetime.strptime(self.start_date.value, "%d/%m/%Y")
            d2 = datetime.strptime(self.end_date.value, "%d/%m/%Y")
            
            if d2 < d1:
                return await interaction.response.send_message(texts['abs_error_logic'], ephemeral=True)
            
            delta = d2 - d1
            days = delta.days
            if days == 0: days = 1
            
            duration_str = f"{days} jour(s)" if self.lang == 'fr' else f"{days} day(s)"
            
            embed = discord.Embed(title=texts['abs_embed_title'].format(user=interaction.user.display_name), color=config.COLOR_PURPLE, timestamp=datetime.now())
            embed.set_thumbnail(url=interaction.user.display_avatar.url)
            embed.add_field(name=texts['abs_user_field'], value=interaction.user.mention, inline=False)
            embed.add_field(name=texts['abs_field_dates'], value=f"📅 {self.start_date.value} ➔ {self.end_date.value}", inline=False)
            embed.add_field(name=texts['abs_field_duration'], value=f"⏱️ {duration_str}", inline=True)
            embed.add_field(name=texts['abs_field_reason'], value=f"📝 {self.reason.value}", inline=False)
            embed.set_footer(text=config.EMBED_FOOTER)
            
            content = ""
            if self.direction_role_id:
                try:
                    roles = json.loads(self.direction_role_id) if isinstance(self.direction_role_id, str) else self.direction_role_id
                    if isinstance(roles, int): roles = [str(roles)]
                    elif isinstance(roles, list): roles = [str(r) for r in roles]
                    mentions = []
                    for r in roles:
                        if r: mentions.append(f"<@&{r}>")
                    content = " ".join(mentions)
                except:
                    content = f"<@&{self.direction_role_id}>"
            
            msg = await interaction.channel.send(content=content, embed=embed)
            
            await self.bot.db.add_absence(
                str(interaction.user.id), 
                interaction.user.display_name,
                str(interaction.guild_id), 
                self.start_date.value, 
                self.end_date.value,   
                self.reason.value, 
                str(msg.id)
            )
            
            # MODIFIE: Utilisation de la nouvelle vue sans ID utilisateur
            view = AbsenceView(self.bot, self.lang)
            await msg.edit(view=view)
            try: await msg.add_reaction("✅")
            except: pass
            await interaction.response.send_message("✅", ephemeral=True)
            
        except ValueError:
            await interaction.response.send_message(texts['abs_error_format'], ephemeral=True)

class EditTimeModal(discord.ui.Modal):
    def __init__(self, bot, lang, target_user, operation):
        texts = config.TRANSLATIONS[lang]
        op_text = texts['time_added'] if operation == "add" else texts['time_removed']
        super().__init__(title=op_text)
        self.bot = bot
        self.lang = lang
        self.target_user = target_user
        self.operation = operation
        
        self.hours = discord.ui.TextInput(label=texts['et_label_hours'], placeholder="0", required=False, default="0", max_length=3)
        self.minutes = discord.ui.TextInput(label=texts['et_label_minutes'], placeholder="0", required=False, default="0", max_length=2)
        self.seconds = discord.ui.TextInput(label=texts['et_label_seconds'], placeholder="0", required=False, default="0", max_length=2)
        
        self.add_item(self.hours)
        self.add_item(self.minutes)
        self.add_item(self.seconds)

    async def on_submit(self, interaction: discord.Interaction):
        texts = config.TRANSLATIONS[self.lang]
        try:
            h = int(self.hours.value) if self.hours.value else 0
            m = int(self.minutes.value) if self.minutes.value else 0
            s = int(self.seconds.value) if self.seconds.value else 0
            
            total_sec = (h * 3600) + (m * 60) + s
            if total_sec <= 0: return await interaction.response.send_message(texts['error_invalid_input'], ephemeral=True)
            
            ms_diff = total_sec * 1000 * (1 if self.operation == "add" else -1)
            old_stats = await self.bot.db.get_user_stats(str(self.target_user.id), str(interaction.guild_id))
            old_total = format_duration(old_stats['total_time'] if old_stats else 0)
            
            await self.bot.db.add_time_adjustment(str(self.target_user.id), str(interaction.guild_id), self.target_user.display_name, ms_diff)
            new_stats = await self.bot.db.get_user_stats(str(self.target_user.id), str(interaction.guild_id))
            new_total = format_duration(new_stats['total_time'] or 0)
            
            action_str = texts['time_added'] if self.operation == "add" else texts['time_removed']
            val_fmt = format_duration(total_sec * 1000)
            
            embed = discord.Embed(title=texts['edit_success'].format(user=self.target_user.display_name, action="", value="", new_total="").split('\n')[0], color=config.COLOR_PURPLE)
            embed.description = texts['edit_desc'].format(user=self.target_user.mention)
            embed.add_field(name=texts['edit_field_action'], value=action_str, inline=True)
            embed.add_field(name=texts['edit_field_amount'], value=f"`{val_fmt}`", inline=True)
            embed.add_field(name="\u200b", value="\u200b", inline=True)
            embed.add_field(name=texts['edit_field_old'], value=f"`{old_total}`", inline=True)
            embed.add_field(name="➡️", value=" ", inline=True)
            embed.add_field(name=texts['edit_field_new_total'], value=f"`{new_total}`", inline=True)
            embed.set_footer(text=config.EMBED_FOOTER)
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            await self.bot.send_log(interaction.guild.id, texts['log_edit_time_title'], texts['log_edit_time_desc'].format(admin=interaction.user.mention), config.COLOR_BLUE, [(texts['edit_field_target'], self.target_user.mention), (texts['edit_field_action'], action_str), (texts['edit_field_amount'], val_fmt), (texts['edit_field_new_total'], new_total)])
        except Exception as e:
            await interaction.response.send_message(f"❌ Error: {e}", ephemeral=True)

class GoalModal(discord.ui.Modal):
    def __init__(self, parent_view, txt):
        super().__init__(title=txt['setup_ph_goal'])
        self.view = parent_view
        self.txt = txt
        val = str(int(parent_view.sel_goal / 3600000)) if parent_view.sel_goal else ""
        self.goal = discord.ui.TextInput(label="Heures / Hours", placeholder="0 = OFF", required=True, default=val)
        self.add_item(self.goal)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            hours = int(self.goal.value)
            ms_goal = hours * 3600000
        except:
            ms_goal = 0
            
        await interaction.response.defer()
        guild = interaction.guild
        
        try:
            chan_svc = guild.get_channel(int(self.view.sel_service))
            chan_log = guild.get_channel(int(self.view.sel_logs)) if self.view.sel_logs else None
            
            role_dir = json.dumps(self.view.sel_role) if self.view.sel_role else None
            role_auto = json.dumps(self.view.sel_autorole) if self.view.sel_autorole else None
            role_cit = str(self.view.sel_citizen) if self.view.sel_citizen else None 
            
            embed = create_service_embed([], guild, self.view.sel_lang)
            view = ServiceButtonsView(self.view.bot, self.view.sel_lang)
            
            msg = None
            if self.view.sel_service: 
                 msg = await chan_svc.send(embed=embed, view=view)
            
            await self.view.bot.db.set_guild_config(
                str(guild.id), 
                str(chan_svc.id), 
                str(msg.id), 
                str(chan_log.id) if chan_log else None, 
                self.view.sel_lang, 
                str(role_dir) if role_dir else None, 
                ms_goal, 
                role_auto,
                role_cit 
            )
            if chan_log:
                try: await chan_log.send(embed=discord.Embed(title=self.txt['log_setup_title'], description=self.txt['log_setup_desc'], color=config.COLOR_GREEN))
                except: pass
                
            await interaction.followup.send(self.txt['setup_success'].format(channel=chan_svc.mention), ephemeral=True)
            self.view.stop()
        except Exception as e:
            await interaction.followup.send(f"❌ Erreur: `{e}`", ephemeral=True)

class RdvTypeModal(discord.ui.Modal):
    def __init__(self, parent_view):
        txt = config.TRANSLATIONS[parent_view.lang]
        super().__init__(title=txt.get('rdv_modal_type_title', "Nouveau Motif"))
        self.parent = parent_view
        self.name = discord.ui.TextInput(label=txt.get('rdv_modal_type_label', "Nom"), max_length=30)
        self.add_item(self.name)
    
    async def on_submit(self, interaction: discord.Interaction):
        if self.name.value not in self.parent.types:
            self.parent.types.append(self.name.value)
            self.parent.update_components()
            await self.parent.update_embed(interaction) 
        else:
            await interaction.response.send_message("Ce motif existe déjà.", ephemeral=True)

class RdvBookingModal(discord.ui.Modal):
    def __init__(self, bot, rdv_type, lang):
        txt = config.TRANSLATIONS[lang]
        super().__init__(title=txt.get('rdv_modal_book_title', "RDV"))
        self.bot = bot
        self.rdv_type = rdv_type
        self.lang = lang
        self.info = discord.ui.TextInput(label=txt.get('rdv_modal_book_label', "Infos"), style=discord.TextStyle.paragraph)
        self.add_item(self.info)

    async def on_submit(self, interaction: discord.Interaction):
        txt = config.TRANSLATIONS[self.lang]
        conf = await self.bot.db.get_rdv_config(interaction.guild.id)
        if not conf or not conf['staff']: return await interaction.response.send_message(txt.get('rdv_err_config', "Erreur config."), ephemeral=True)
        channel = interaction.guild.get_channel(int(conf['staff']))
        if not channel: return await interaction.response.send_message(txt.get('rdv_err_config', "Erreur salon."), ephemeral=True)

        embed = discord.Embed(title=txt.get('rdv_new_req_title', "Nouvelle Demande"), color=discord.Color.blue())
        embed.description = f"**Patient**: {interaction.user.mention}\n**Type**: {self.rdv_type}\n**Info**: {self.info.value}"
        embed.set_footer(text=f"ID: {interaction.user.id}")
        
        view = RdvStaffView(self.bot, interaction.user.id, self.rdv_type, self.info.value, self.lang)
        content_role = f"<@&{conf['role']}>" if conf['role'] else ""
        await channel.send(content=content_role, embed=embed, view=view)
        await interaction.response.send_message("✅ Demande envoyée !", ephemeral=True)


# ==============================================================================
#                            VUES INTERACTIVES
# ==============================================================================

class AbsenceView(discord.ui.View):
    def __init__(self, bot, lang='fr'):
        super().__init__(timeout=None)
        self.bot = bot
        self.lang = lang
        txt = config.TRANSLATIONS.get(lang, config.TRANSLATIONS['fr'])
        
        # ID STATIC : "absence_end_btn"
        btn = discord.ui.Button(label=txt.get('abs_btn_end', "Fin"), style=discord.ButtonStyle.success, custom_id="absence_end_btn")
        btn.callback = self.end_absence
        self.add_item(btn)

    async def end_absence(self, interaction: discord.Interaction):
        # On récupère la langue du serveur
        conf_guild = await self.bot.db.get_guild_config(str(interaction.guild_id))
        lang = conf_guild.get('language', 'fr') if conf_guild else 'fr'
        txt = config.TRANSLATIONS.get(lang, config.TRANSLATIONS['fr'])
        
        msg_id = str(interaction.message.id)
        
        # 1. On cherche l'absence dans la DB via l'ID du message
        absence_data = await self.bot.db.get_absence_by_message_id(msg_id)
        
        if not absence_data:
            return await interaction.response.send_message("❌ Cette absence n'existe plus dans la base de données.", ephemeral=True)

        owner_id = absence_data['user_id']

        # 2. Vérification Permission (Propriétaire ou Admin)
        if str(interaction.user.id) != str(owner_id) and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message(txt.get('abs_err_owner', "Pas toi !"), ephemeral=True)
            
        # 3. Suppression
        await self.bot.db.end_absence(msg_id)
        
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.green()
        embed.set_footer(text=txt.get('abs_ended', "Terminée"))
        
        await interaction.message.edit(embed=embed, view=None)
        await interaction.response.send_message(txt.get('abs_ended', "Terminée"), ephemeral=True)

class RdvSetupView(discord.ui.View):
    def __init__(self, bot, config_data):
        super().__init__(timeout=300)
        self.bot = bot
        self.config = config_data or {}
        self.lang = 'fr'
        self.public_id = self.config.get('public')
        self.staff_id = self.config.get('staff')
        self.transcript_id = self.config.get('transcript')
        self.role_id = self.config.get('role')
        self.types = self.config.get('types', [])
        self.update_components()

    def update_components(self):
        self.clear_items()
        txt = config.TRANSLATIONS[self.lang]
        self.add_item(discord.ui.ChannelSelect(placeholder=txt.get('rdv_ph_public', "Salon Public"), custom_id="rdv_pub", channel_types=[discord.ChannelType.text]))
        self.add_item(discord.ui.ChannelSelect(placeholder=txt.get('rdv_ph_staff', "Salon Staff"), custom_id="rdv_stf", channel_types=[discord.ChannelType.text]))
        self.add_item(discord.ui.ChannelSelect(placeholder=txt.get('rdv_ph_transcript', "Salon Logs/Transcript"), custom_id="rdv_trs", channel_types=[discord.ChannelType.text])) 
        self.add_item(discord.ui.RoleSelect(placeholder=txt.get('rdv_ph_role', "Rôle Staff"), custom_id="rdv_rol"))
        
        btn_add = discord.ui.Button(label=txt.get('rdv_btn_add', "Ajouter Motif"), style=discord.ButtonStyle.success, custom_id="rdv_add", row=4)
        btn_add.callback = self.add_type
        self.add_item(btn_add)
        
        if self.types:
            btn_del = discord.ui.Button(label=txt.get('rdv_btn_del', "Supprimer Motif"), style=discord.ButtonStyle.danger, custom_id="rdv_del", row=4)
            btn_del.callback = self.remove_type_menu
            self.add_item(btn_del)
            
        btn_save = discord.ui.Button(label=txt.get('setup_btn_save', "Sauvegarder"), style=discord.ButtonStyle.primary, custom_id="rdv_save", row=4)
        btn_save.callback = self.save_config
        self.add_item(btn_save)

    async def update_embed(self, interaction):
        txt = config.TRANSLATIONS[self.lang]
        types_list = "\n".join([f"• {t}" for t in self.types]) if self.types else "Aucun"
        embed = interaction.message.embeds[0]
        embed.description = txt['rdv_setup_desc'].format(types=types_list)
        await interaction.response.edit_message(embed=embed, view=self)

    async def interaction_check(self, interaction: discord.Interaction):
        cid = interaction.data.get('custom_id')
        vals = interaction.data.get('values', [])
        if cid == "rdv_pub": self.public_id = vals[0]
        elif cid == "rdv_stf": self.staff_id = vals[0]
        elif cid == "rdv_trs": self.transcript_id = vals[0]
        elif cid == "rdv_rol": self.role_id = vals[0]
        if cid in ["rdv_pub", "rdv_stf", "rdv_trs", "rdv_rol"]: await interaction.response.defer(); return False
        return True

    async def add_type(self, interaction: discord.Interaction):
        await interaction.response.send_modal(RdvTypeModal(self))

    async def remove_type_menu(self, interaction: discord.Interaction):
        view = RdvDeleteTypeView(self)
        await interaction.response.send_message("Supprimer quel motif ?", view=view, ephemeral=True)

    async def save_config(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        txt = config.TRANSLATIONS[self.lang]
        msg_id = None
        if self.public_id and self.types:
            try:
                public_channel = interaction.guild.get_channel(int(self.public_id))
                if public_channel:
                    embed_panel = discord.Embed(title=txt['rdv_panel_title'], description=txt['rdv_panel_desc'], color=discord.Color.blue())
                    view_panel = RdvPatientView(self.bot, self.types, self.lang)
                    old_msg_id = self.config.get('message_id')
                    message_sent = False
                    if old_msg_id:
                        try:
                            msg = await public_channel.fetch_message(int(old_msg_id))
                            await msg.edit(embed=embed_panel, view=view_panel)
                            msg_id = str(msg.id)
                            message_sent = True
                        except: pass 
                    if not message_sent:
                        msg = await public_channel.send(embed=embed_panel, view=view_panel)
                        msg_id = str(msg.id)
            except Exception as e: print(f"Erreur panel auto: {e}")

        await self.bot.db.set_rdv_config(interaction.guild.id, self.public_id, self.staff_id, self.transcript_id, self.role_id, self.types, msg_id)
        await interaction.followup.send("✅ Configuration RDV sauvegardée et Panneau mis à jour !", ephemeral=True)

class RdvDeleteTypeView(discord.ui.View):
    def __init__(self, parent_view):
        super().__init__(timeout=60)
        self.parent = parent_view
        select = discord.ui.Select(placeholder="Choisir...", min_values=1, max_values=1)
        for t in parent_view.types[:25]: select.add_option(label=t, value=t)
        select.callback = self.callback
        self.add_item(select)

    async def callback(self, interaction: discord.Interaction):
        val = interaction.data['values'][0]
        if val in self.parent.types:
            self.parent.types.remove(val)
            self.parent.update_components()
            await interaction.response.edit_message(content=f"🗑️ Motif `{val}` supprimé.", view=None)
            try: await self.parent.update_embed(interaction) 
            except: pass

class RdvPatientView(discord.ui.View):
    def __init__(self, bot, types, lang):
        super().__init__(timeout=None)
        self.bot = bot
        self.lang = lang
        self.types = types 
        txt = config.TRANSLATIONS[lang]
        self.select = discord.ui.Select(placeholder=txt.get('rdv_select_ph', "Choisir..."), custom_id="rdv_patient_select", min_values=1, max_values=1)
        for t in types: self.select.add_option(label=t, value=t)
        self.select.callback = self.callback
        self.add_item(self.select)

    async def callback(self, interaction: discord.Interaction):
        rdv_type = self.select.values[0]
        await interaction.response.send_modal(RdvBookingModal(self.bot, rdv_type, self.lang))
        self.select.options.clear()
        for t in self.types: self.select.add_option(label=t, value=t, default=False)
        self.select.placeholder = config.TRANSLATIONS[self.lang].get('rdv_select_ph', "Choisir...")
        try: await interaction.message.edit(view=self)
        except: pass

class RdvStaffView(discord.ui.View):
    def __init__(self, bot, user_id=None, rdv_type=None, info=None, lang='fr'):
        super().__init__(timeout=None)
        self.bot = bot
        self.user_id = user_id
        self.rdv_type = rdv_type
        self.info = info
        self.lang = lang
        
        txt = config.TRANSLATIONS.get(lang, config.TRANSLATIONS['fr'])
        
        b_acc = discord.ui.Button(label=txt.get('rdv_btn_accept', "Accepter"), style=discord.ButtonStyle.success, custom_id="rdv_accept")
        b_acc.callback = self.accept
        self.add_item(b_acc)
        
        b_ref = discord.ui.Button(label=txt.get('rdv_btn_refuse', "Refuser"), style=discord.ButtonStyle.danger, custom_id="rdv_refuse")
        b_ref.callback = self.refuse
        self.add_item(b_ref)

    async def _get_data(self, interaction):
        if self.user_id and self.rdv_type:
            return self.user_id, self.rdv_type, self.info, self.lang

        try:
            conf_guild = await self.bot.db.get_guild_config(str(interaction.guild_id))
            lang = conf_guild.get('language', 'fr') if conf_guild else 'fr'

            embed = interaction.message.embeds[0]
            
            footer_text = embed.footer.text
            user_id = int(footer_text.replace("ID:", "").strip())
            
            desc = embed.description
            rdv_type = "Inconnu"
            info = "Non spécifié"
            
            for line in desc.split('\n'):
                if "**Type**" in line:
                    rdv_type = line.split(":", 1)[1].strip()
                if "**Info**" in line:
                    info = line.split(":", 1)[1].strip()
                    
            return user_id, rdv_type, info, lang
        except Exception as e:
            print(f"❌ Erreur récupération données RDV : {e}")
            return None, None, None, 'fr'

    async def accept(self, interaction: discord.Interaction):
        user_id, rdv_type, info, lang = await self._get_data(interaction)
        
        if not user_id:
            return await interaction.response.send_message("❌ Erreur : Impossible de retrouver le dossier (Données illisibles).", ephemeral=True)

        txt = config.TRANSLATIONS[lang]
        guild = interaction.guild
        try: 
            user = guild.get_member(user_id) or await guild.fetch_member(user_id)
        except: 
            return await interaction.response.send_message("⚠️ Utilisateur introuvable (a peut-être quitté le serveur).", ephemeral=True)
        
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True),
            interaction.user: discord.PermissionOverwrite(read_messages=True),
            interaction.guild.me: discord.PermissionOverwrite(read_messages=True)
        }
        
        conf = await self.bot.db.get_rdv_config(guild.id)
        role_mention = ""
        if conf and conf['role']:
            role = guild.get_role(int(conf['role']))
            if role:
                overwrites[role] = discord.PermissionOverwrite(read_messages=True)
                role_mention = role.mention

        cat = discord.utils.get(guild.categories, name="Rendez-Vous")
        if not cat: cat = await guild.create_category("Rendez-Vous")
        
        chan_name = f"rdv-{user.name}-{rdv_type}"
        chan_name = chan_name.replace(" ", "-").lower()[:99]
        topic_info = f"Patient: {user.id} | Staff: {interaction.user.id} | Type: {rdv_type}"
        
        channel = await guild.create_text_channel(chan_name, category=cat, overwrites=overwrites, topic=topic_info)
        
        welcome_msg = txt.get('rdv_ticket_welcome', "Bienvenue").format(user=user.mention, role=role_mention, type=rdv_type, info=info)
        await channel.send(welcome_msg, view=RdvTicketView(self.bot, lang))
        
        await interaction.message.edit(view=None, content=txt.get('rdv_accepted', "Accepté").format(staff=interaction.user.mention, channel=channel.mention), embed=interaction.message.embeds[0])

        if conf.get('transcript'):
            try:
                log_chan = guild.get_channel(int(conf['transcript']))
                if log_chan:
                    embed_log = discord.Embed(title=txt.get('rdv_log_accepted_title', "RDV Accepté"), color=discord.Color.green())
                    embed_log.description = txt.get('rdv_log_accepted_desc', "Accepté par {staff}").format(staff=interaction.user.mention, patient=user.mention)
                    embed_log.add_field(name="Type", value=rdv_type)
                    embed_log.timestamp = datetime.now()
                    await log_chan.send(embed=embed_log)
            except: pass

    async def refuse(self, interaction: discord.Interaction):
        _, _, _, lang = await self._get_data(interaction)
        txt = config.TRANSLATIONS[lang]
        await interaction.message.edit(view=None, content=txt.get('rdv_refused', "Refusé par {user}.").format(user=interaction.user.mention), embed=interaction.message.embeds[0])

class RdvTicketView(discord.ui.View):
    def __init__(self, bot, lang='fr'):
        super().__init__(timeout=None)
        self.bot = bot
        self.lang = lang
        txt = config.TRANSLATIONS.get(lang, config.TRANSLATIONS['fr'])
        btn = discord.ui.Button(label=txt.get('rdv_btn_close', "Fermer"), style=discord.ButtonStyle.danger, emoji="🔒", custom_id="rdv_ticket_close")
        btn.callback = self.close
        self.add_item(btn)

    async def close(self, interaction: discord.Interaction):
        txt = config.TRANSLATIONS[self.lang]
        await interaction.response.send_message("Génération du transcript et fermeture...", ephemeral=True)
        topic = interaction.channel.topic or ""
        patient_id = None
        staff_id = None
        if "Patient:" in topic:
            try:
                parts = topic.split("|")
                for p in parts:
                    if "Patient:" in p: patient_id = int(p.split(":")[1].strip())
                    if "Staff:" in p: staff_id = int(p.split(":")[1].strip())
            except: pass

        transcript_file = await generate_transcript_file(interaction.channel)
        if patient_id:
            try:
                patient = await self.bot.fetch_user(patient_id)
                await patient.send(content=txt.get('rdv_transcript_dm', "Votre transcript :"), file=transcript_file)
                transcript_file.fp.seek(0) 
            except: pass
            
        conf = await self.bot.db.get_rdv_config(interaction.guild.id)
        if conf and conf.get('transcript'):
            try:
                log_chan = interaction.guild.get_channel(int(conf['transcript']))
                if log_chan:
                    embed_log = discord.Embed(title=txt.get('rdv_log_closed_title', "RDV Fermé"), color=discord.Color.red())
                    pat_men = f"<@{patient_id}>" if patient_id else "Inconnu"
                    stf_men = f"<@{staff_id}>" if staff_id else "Inconnu"
                    embed_log.description = txt.get('rdv_log_closed_desc', "Fermé").format(patient=pat_men)
                    embed_log.add_field(name="Ouvert par (Staff)", value=stf_men, inline=True)
                    embed_log.add_field(name="Fermé par", value=interaction.user.mention, inline=True)
                    embed_log.timestamp = datetime.now()
                    transcript_file.fp.seek(0)
                    await log_chan.send(embed=embed_log, file=transcript_file)
            except Exception as e: print(f"Log error: {e}")

        await discord.utils.sleep_until(discord.utils.utcnow() + timedelta(seconds=2))
        await interaction.channel.delete()

class ServerStatsView(discord.ui.View):
    def __init__(self, bot, guild_id, sessions, stats, lang):
        super().__init__(timeout=300)
        self.bot = bot
        self.guild_id = guild_id
        self.sessions = sessions
        self.stats = stats
        self.lang = lang
        self.mode = 'weekly'
        self.graph_index = 0
        self.graphs_weekly = ['weekly_hours', 'weekly_staff', 'weekly_avg']
        self.graphs_daily = ['daily_activity', 'daily_sessions']
        self.update_components()

    def update_components(self):
        self.clear_items()
        txt = config.TRANSLATIONS[self.lang]
        select = discord.ui.Select(placeholder=txt['srv_select_placeholder'], min_values=1, max_values=1, custom_id="stats_mode")
        select.add_option(label=txt['srv_opt_weekly'], value='weekly', emoji="🗓️", default=(self.mode=='weekly'))
        select.add_option(label=txt['srv_opt_daily'], value='daily', emoji="📅", default=(self.mode=='daily'))
        select.callback = self.select_callback
        self.add_item(select)
        btn = discord.ui.Button(label=txt['srv_btn_next_graph'], style=discord.ButtonStyle.primary, custom_id="next_graph")
        btn.callback = self.button_callback
        self.add_item(btn)

    async def select_callback(self, interaction: discord.Interaction):
        self.mode = interaction.data['values'][0]
        self.graph_index = 0
        self.update_components()
        await interaction.response.defer()
        await self.update_message(interaction)

    async def button_callback(self, interaction: discord.Interaction):
        current_list = self.graphs_weekly if self.mode == 'weekly' else self.graphs_daily
        self.graph_index = (self.graph_index + 1) % len(current_list)
        await interaction.response.defer()
        await self.update_message(interaction)

    async def update_message(self, interaction: discord.Interaction):
        current_list = self.graphs_weekly if self.mode == 'weekly' else self.graphs_daily
        graph_type = current_list[self.graph_index]
        file = await create_graph(self.sessions, graph_type, self.lang)
        embed = create_server_stats_embed(self.stats, self.stats['days_analyzed'], self.lang)
        try: await interaction.edit_original_response(embed=embed, attachments=[file], view=self)
        except: await interaction.response.edit_message(embed=embed, attachments=[file], view=self)

class PaginationView(discord.ui.View):
    def __init__(self, bot, all_stats, guild, lang, goal=0, absent_users=None):
        super().__init__(timeout=300)
        self.bot = bot
        self.all_stats = all_stats
        self.guild = guild
        self.lang = lang
        self.goal = goal
        self.absent_users = absent_users if absent_users else []
        self.current_page = 1
        self.txt = config.TRANSLATIONS[lang]
        self.message = None
        self.update_buttons()

    def update_buttons(self):
        self.children[0].label = self.txt['btn_prev']
        self.children[1].label = self.txt['btn_next']
        import math
        total_pages = math.ceil(len(self.all_stats) / 10) or 1
        self.children[0].disabled = (self.current_page == 1)
        self.children[1].disabled = (self.current_page >= total_pages)

    @discord.ui.button(style=discord.ButtonStyle.secondary, disabled=True)
    async def prev_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page -= 1
        await self.update_embed(interaction)

    @discord.ui.button(style=discord.ButtonStyle.secondary)
    async def next_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page += 1
        await self.update_embed(interaction)

    async def update_embed(self, interaction):
        embed, total = create_all_stats_embed(self.all_stats, self.guild, self.lang, self.current_page, self.goal, self.absent_users)
        self.update_buttons()
        await interaction.response.edit_message(embed=embed, view=self)
        self.message = interaction.message

    async def on_timeout(self):
        for child in self.children: child.disabled = True
        if self.message:
            try: await self.message.edit(view=self)
            except: pass

class HistoryPaginationView(discord.ui.View):
    def __init__(self, sessions, user, first, last, lang):
        super().__init__(timeout=300)
        self.sessions = sessions
        self.user = user
        self.first = first
        self.last = last
        self.lang = lang
        self.current_page = 1
        self.items_per_page = 10
        self.txt = config.TRANSLATIONS[lang]
        self.update_buttons()

    def update_buttons(self):
        self.children[0].label = self.txt['btn_prev']
        self.children[1].label = self.txt['btn_next']
        import math
        total_pages = math.ceil(len(self.sessions) / self.items_per_page)
        total_pages = 1 if total_pages == 0 else total_pages
        self.children[0].disabled = (self.current_page == 1)
        self.children[1].disabled = (self.current_page >= total_pages)

    def get_embed(self):
        txt = self.txt
        import math
        total_pages = math.ceil(len(self.sessions) / self.items_per_page) or 1
        start = (self.current_page - 1) * self.items_per_page
        end = start + self.items_per_page
        current = self.sessions[start:end]
        
        embed = discord.Embed(title=txt['det_title'].format(user=self.user.display_name), color=config.BOT_COLOR)
        f_str = f"<t:{int(self.first/1000)}:D>" if self.first else "N/A"
        l_str = f"<t:{int(self.last/1000)}:D>" if self.last else "N/A"
        embed.description = txt.get('det_range', "").format(first=f_str, last=l_str)
        
        hist_text = ""
        for s in current:
            date = f"<t:{int(s['start_time']/1000)}:d>"
            dur = format_duration(s['total_duration'])
            if s['start_time'] == s['end_time']:
                icon = "🔧"
                t = txt['det_type_adjust']
                dur = f"+{dur}" if s['total_duration'] > 0 else dur
            else:
                icon = "🟢"
                t = txt['det_type_service']
            hist_text += f"{icon} **{date}** • {t} : `{dur}`\n"
            
        embed.add_field(name=txt['det_history'].format(count=len(self.sessions)), value=hist_text or "Vide", inline=False)
        embed.set_footer(text=f"Page {self.current_page}/{total_pages} | {config.EMBED_FOOTER}")
        return embed

    @discord.ui.button(style=discord.ButtonStyle.secondary, disabled=True)
    async def prev_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page -= 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

    @discord.ui.button(style=discord.ButtonStyle.secondary)
    async def next_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page += 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

class ServiceButtonsView(discord.ui.View):
    def __init__(self, bot, lang='fr'):
        super().__init__(timeout=None)
        self.bot = bot
        self.db = bot.db
        texts = config.TRANSLATIONS.get(lang, config.TRANSLATIONS['fr'])
        for c in self.children:
            if isinstance(c, discord.ui.Button):
                if c.custom_id == config.BUTTONS['start']['custom_id']:
                    c.label = texts['btn_start']
                    c.emoji = config.BUTTONS['start']['emoji']
                elif c.custom_id == config.BUTTONS['pause']['custom_id']:
                    c.label = texts['btn_pause']
                    c.emoji = config.BUTTONS['pause']['emoji']
                elif c.custom_id == config.BUTTONS['stop']['custom_id']:
                    c.label = texts['btn_stop']
                    c.emoji = config.BUTTONS['stop']['emoji']

    async def _check_access(self, interaction):
        cd = await self.db.get_guild_config(str(interaction.guild_id)) 
        if cd is None: cd = {}
        lang = cd.get('language', 'fr')
        if int(cd.get('is_maintenance', 0)) == 1:
            if str(interaction.user.id) == config.OWNER_ID: pass
            else: await interaction.response.send_message(config.TRANSLATIONS[lang]['maint_block_msg'], ephemeral=True); return False
        allowed = json.loads(cd.get('allowed_roles', '[]') or '[]')
        if not check_permissions(interaction.user, allowed): await interaction.response.send_message(config.TRANSLATIONS[lang]['error_perms'], ephemeral=True); return False
        return True

    @discord.ui.button(style=discord.ButtonStyle.success, custom_id=config.BUTTONS['start']['custom_id'])
    async def start_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_access(interaction): return
        await interaction.response.defer(ephemeral=True)
        lang = await self.bot.db.get_guild_config(str(interaction.guild_id))
        if lang is None: lang = {}
        lang = lang.get('language', 'fr')
        texts = config.TRANSLATIONS[lang]
        try:
            if await self.db.get_active_session(str(interaction.user.id), str(interaction.guild_id)): return await interaction.followup.send(texts['service_already_started'], ephemeral=True)
            await self.db.start_session(str(interaction.user.id), str(interaction.guild_id), interaction.user.display_name)
            await interaction.followup.send(texts['service_started'], ephemeral=True)
            await self.bot.send_log(interaction.guild.id, texts['log_start_title'], texts['log_start_desc'].format(user=interaction.user.mention), config.COLOR_GREEN)
            await self.bot.update_service_message(interaction.guild_id)
        except: await interaction.followup.send(texts['error_db'], ephemeral=True)

    @discord.ui.button(style=discord.ButtonStyle.primary, custom_id=config.BUTTONS['pause']['custom_id'])
    async def pause_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_access(interaction): return
        await interaction.response.defer(ephemeral=True)
        lang = await self.bot.db.get_guild_config(str(interaction.guild_id))
        if lang is None: lang = {}
        lang = lang.get('language', 'fr')
        texts = config.TRANSLATIONS[lang]
        try:
            act = await self.db.get_active_session(str(interaction.user.id), str(interaction.guild_id))
            if not act: return await interaction.followup.send(texts['service_not_started'], ephemeral=True)
            if act['is_paused']:
                await self.db.resume_session(str(interaction.user.id), str(interaction.guild_id))
                await interaction.followup.send(texts['service_resumed'], ephemeral=True)
                await self.bot.send_log(interaction.guild.id, texts['log_resume_title'], texts['log_resume_desc'].format(user=interaction.user.mention), config.COLOR_BLUE)
            else:
                await self.db.pause_session(str(interaction.user.id), str(interaction.guild_id))
                await interaction.followup.send(texts['service_paused'], ephemeral=True)
                await self.bot.send_log(interaction.guild.id, texts['log_pause_title'], texts['log_pause_desc'].format(user=interaction.user.mention), config.COLOR_ORANGE)
            await self.bot.update_service_message(interaction.guild_id)
        except: await interaction.followup.send(texts['error_db'], ephemeral=True)

    @discord.ui.button(style=discord.ButtonStyle.danger, custom_id=config.BUTTONS['stop']['custom_id'])
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_access(interaction): return
        await interaction.response.defer(ephemeral=True)
        lang = await self.bot.db.get_guild_config(str(interaction.guild_id))
        if lang is None: lang = {}
        lang = lang.get('language', 'fr')
        texts = config.TRANSLATIONS[lang]
        try:
            if not await self.db.get_active_session(str(interaction.user.id), str(interaction.guild_id)): return await interaction.followup.send(texts['service_not_started'], ephemeral=True)
            end = await self.db.end_session(str(interaction.user.id), str(interaction.guild_id))
            if end:
                tot = end['total_duration'] + end['pause_duration']
                msg = texts['service_stopped'].format(duration=format_duration(tot), pause=format_duration(end['pause_duration']), effective=format_duration(end['total_duration']))
                await interaction.followup.send(msg, ephemeral=True)
                await self.bot.send_log(interaction.guild.id, texts['log_stop_title'], texts['log_stop_desc'].format(user=interaction.user.mention), config.COLOR_RED, [("Total", format_duration(tot))])
                await self.bot.update_service_message(interaction.guild_id)
            else: await interaction.followup.send(texts['error_db'], ephemeral=True)
        except: await interaction.followup.send(texts['error_db'], ephemeral=True)

class EditTimeView(discord.ui.View):
    def __init__(self, bot, lang, target):
        super().__init__(timeout=60)
        self.bot=bot; self.lang=lang; self.target=target
        t=config.TRANSLATIONS[lang]
        self.add_item(discord.ui.Button(label=t['et_btn_add'], emoji="➕", custom_id="add", style=discord.ButtonStyle.success))
        self.add_item(discord.ui.Button(label=t['et_btn_remove'], emoji="➖", custom_id="remove", style=discord.ButtonStyle.danger))
    
    async def interaction_check(self, i):
        await i.response.send_modal(EditTimeModal(self.bot, self.lang, self.target, i.data['custom_id'])); return False

class HelpView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot=bot
        self.lang='fr' 
        
    def get_embed(self, cat=None):
        t = config.TRANSLATIONS.get(self.lang, config.TRANSLATIONS['fr'])
        if cat == 'root':
            return discord.Embed(title=t['help_title'], description=t['help_desc'], color=config.BOT_COLOR)
        if cat == 'user': 
            embed = discord.Embed(title=f"{t['help_title']} - Users", description=t['help_user_desc'], color=config.BOT_COLOR)
            embed.add_field(name="Liste", value=t['help_cmds_user'], inline=False)
            return embed
        elif cat == 'admin': 
            embed = discord.Embed(title=f"{t['help_title']} - Admin", description=t['help_admin_desc'], color=config.BOT_COLOR)
            embed.add_field(name="Liste", value=t['help_cmds_admin'], inline=False)
            return embed
        return discord.Embed(title=t['help_title'], description=t['help_desc'], color=config.BOT_COLOR)
        
    def update_buttons(self, state):
        self.clear_items()
        t = config.TRANSLATIONS.get(self.lang, config.TRANSLATIONS['fr'])
        if state == 'lang':
            self.add_item(discord.ui.Button(label="Français", emoji="🇫🇷", custom_id="fr", style=discord.ButtonStyle.primary))
            self.children[0].callback = self.cb_fr
            self.add_item(discord.ui.Button(label="English", emoji="🇬🇧", custom_id="en", style=discord.ButtonStyle.primary))
            self.children[1].callback = self.cb_en
        elif state == 'menu':
            self.add_item(discord.ui.Button(label=t['help_cat_user'], style=discord.ButtonStyle.success, emoji="👤"))
            self.children[0].callback = self.cb_user
            self.add_item(discord.ui.Button(label=t['help_cat_admin'], style=discord.ButtonStyle.danger, emoji="🛡️"))
            self.children[1].callback = self.cb_admin
            self.add_item(discord.ui.Button(label=t['btn_feedback'], style=discord.ButtonStyle.primary, emoji="📨", row=1))
            self.children[2].callback = self.cb_feed
            self.add_item(discord.ui.Button(label=t['help_back_lang'], emoji="🌍", style=discord.ButtonStyle.secondary, row=1))
            self.children[3].callback = self.cb_back
        elif state == 'sub':
            self.add_item(discord.ui.Button(label=t['help_back'], style=discord.ButtonStyle.secondary, emoji="↩️"))
            self.children[0].callback = self.cb_menu
            
    async def cb_fr(self, i): self.lang='fr'; self.update_buttons('menu'); await i.response.edit_message(embed=self.get_embed('root'), view=self)
    async def cb_en(self, i): self.lang='en'; self.update_buttons('menu'); await i.response.edit_message(embed=self.get_embed('root'), view=self)
    async def cb_back(self, i): self.update_buttons('lang'); await i.response.edit_message(embed=self.get_embed('root'), view=self)
    async def cb_menu(self, i): self.update_buttons('menu'); await i.response.edit_message(embed=self.get_embed('root'), view=self)
    async def cb_user(self, i): self.update_buttons('sub'); await i.response.edit_message(embed=self.get_embed('user'), view=self)
    async def cb_admin(self, i): self.update_buttons('sub'); await i.response.edit_message(embed=self.get_embed('admin'), view=self)
    async def cb_feed(self, i): await i.response.send_message(view=FeedbackView(self.bot, self.lang), ephemeral=True)

class AboutView(discord.ui.View):
    def __init__(self, bot, lang):
        super().__init__(timeout=None)
        self.bot=bot; self.lang=lang
        t=config.TRANSLATIONS[lang]
        p=discord.Permissions(administrator=True)
        inv=discord.utils.oauth_url(bot.user.id, permissions=p)
        self.add_item(discord.ui.Button(label=t['btn_invite'], url=inv, style=discord.ButtonStyle.link))
        self.add_item(discord.ui.Button(label=t['btn_source'], url=config.GITHUB_LINK, style=discord.ButtonStyle.url))
        self.add_item(discord.ui.Button(label=t['btn_refresh'], style=discord.ButtonStyle.secondary, emoji="🔄"))
        self.children[2].callback = self.refresh
        
    def get_embed(self):
        t = config.TRANSLATIONS.get(self.lang, config.TRANSLATIONS['fr'])
        e = discord.Embed(title=f"ℹ️ {config.BOT_NAME}", description="Service Bot", color=config.BOT_COLOR)
        e.add_field(name="Version", value=f"`{config.BOT_VERSION}`", inline=True)
        e.add_field(name="Dev", value=f"matteohooliga\n`({config.OWNER_ID})`", inline=True)
        e.add_field(name=t['about_maint_title'], value=t['about_maint_desc'], inline=False)
        server_count = len(self.bot.guilds)
        user_count = sum(g.member_count for g in self.bot.guilds)
        e.add_field(name=t['about_stats_title'], value=f"{t['about_val_servers'].format(val=server_count)}\n{t['about_val_users'].format(val=user_count)}", inline=False)
        py_ver = sys.version.split()[0]
        dpy_ver = discord.__version__
        e.add_field(name=t['about_tech_title'], value=t['about_val_version'].format(py=py_ver, dpy=dpy_ver), inline=False)
        e.add_field(name="Ping", value=f"`{round(self.bot.latency*1000)}ms`", inline=True)
        e.set_footer(text=config.EMBED_FOOTER)
        e.timestamp = datetime.now()
        return e
    
    async def refresh(self, i): e=self.get_embed(); await i.response.edit_message(embed=e, view=self)

class FeedbackTypeSelect(discord.ui.Select):
    def __init__(self, bot, lang):
        self.bot=bot; self.lang=lang
        t=config.TRANSLATIONS[lang]
        ops=[discord.SelectOption(label=t['fb_opt_review'], value="review", emoji="⭐"), discord.SelectOption(label=t['fb_opt_bug'], value="bug", emoji="🐛")]
        super().__init__(placeholder=t['fb_select_placeholder'], options=ops)
        
    async def callback(self, i): 
        if self.values[0]=="review": await i.response.send_modal(ReviewModal(self.bot, self.lang))
        elif self.values[0]=="bug": await i.response.send_modal(BugReportModal(self.bot, self.lang))

class FeedbackView(discord.ui.View):
    def __init__(self, bot, lang): super().__init__(timeout=60); self.add_item(FeedbackTypeSelect(bot, lang))

# ==============================================================================
#                 SETUP VIEW (PAGINÉE) - CORRIGÉE
# ==============================================================================

class SetupView(discord.ui.View):
    def __init__(self, bot, config_data=None):
        super().__init__(timeout=300)
        self.bot = bot
        self.page = 1 # Gestion des pages
        self.sel_lang = config_data.get('language','fr') if config_data else 'fr'
        self.sel_service = config_data.get('channel_id') if config_data else None
        self.sel_logs = config_data.get('log_channel_id') if config_data else None
        self.sel_role = json.loads(config_data.get('direction_role_id','[]')) if config_data else []
        self.sel_autorole = json.loads(config_data.get('auto_roles_list','[]')) if config_data else []
        self.sel_citizen = config_data.get('citizen_role_id') if config_data else None
        self.sel_goal = config_data.get('min_hours_goal',0) if config_data else 0
        self.update_components()
        
    def update_components(self):
        self.clear_items()
        t = config.TRANSLATIONS[self.sel_lang]
        
        # --- PAGE 1 : GENERAL ---
        if self.page == 1:
            # Choix Langue
            b1 = discord.ui.Button(label="FR", custom_id="fr", style=discord.ButtonStyle.primary if self.sel_lang=='fr' else discord.ButtonStyle.secondary); b1.callback=self.cb_fr; self.add_item(b1)
            b2 = discord.ui.Button(label="EN", custom_id="en", style=discord.ButtonStyle.primary if self.sel_lang=='en' else discord.ButtonStyle.secondary); b2.callback=self.cb_en; self.add_item(b2)
            
            # Selects Channels
            self.add_item(discord.ui.ChannelSelect(placeholder=t['setup_ph_service'], channel_types=[discord.ChannelType.text], min_values=1, max_values=1, custom_id="svc"))
            self.add_item(discord.ui.ChannelSelect(placeholder=t['setup_ph_logs'], channel_types=[discord.ChannelType.text], min_values=0, max_values=1, custom_id="log"))
            
            # Navigation
            btn_next = discord.ui.Button(label=t['setup_btn_next'], custom_id="next", style=discord.ButtonStyle.primary, row=4)
            btn_next.callback = self.cb_next
            self.add_item(btn_next)

        # --- PAGE 2 : ROLES ---
        elif self.page == 2:
            # Selects Rôles
            self.add_item(discord.ui.RoleSelect(placeholder=t['setup_ph_role'], min_values=0, max_values=20, custom_id="role"))
            self.add_item(discord.ui.RoleSelect(placeholder=t['setup_ph_autorole'], min_values=0, max_values=20, custom_id="autorole"))
            self.add_item(discord.ui.RoleSelect(placeholder=t['setup_ph_citizen'], min_values=0, max_values=1, custom_id="citizen"))

            # Navigation
            btn_back = discord.ui.Button(label=t['setup_btn_back'], custom_id="back", style=discord.ButtonStyle.secondary, row=4)
            btn_back.callback = self.cb_back
            self.add_item(btn_back)
            
            # Validation finale
            btn_save = discord.ui.Button(label=t['setup_btn_save'], custom_id="save", style=discord.ButtonStyle.success, row=4)
            btn_save.callback = self.cb_save
            self.add_item(btn_save)
        
    async def refresh(self, i):
        t = config.TRANSLATIONS[self.sel_lang]
        title = f"{t['setup_panel_title']} - Page {self.page}/2"
        desc_key = f"setup_panel_desc_{self.page}"
        desc = t.get(desc_key, t['setup_panel_desc']) + "\n\n" + self.get_desc(t)
        
        e = discord.Embed(title=title, description=desc, color=config.BOT_COLOR)
        e.set_footer(text=config.EMBED_FOOTER)
        
        # --- CORRECTION ICI ---
        # Si l'interaction a déjà eu une réponse (ou un defer), on utilise edit_original_response
        if i.response.is_done():
            await i.edit_original_response(embed=e, view=self)
        else:
            await i.response.edit_message(embed=e, view=self)
        
    def get_desc(self, t):
        # Résumé visuel en bas de l'embed
        svc = f"<#{self.sel_service}>" if self.sel_service else "❌"
        log = f"<#{self.sel_logs}>" if self.sel_logs else "❌"
        rol = f"{len(self.sel_role)} rôles" if self.sel_role else "❌"
        aut = f"{len(self.sel_autorole)} rôles" if self.sel_autorole else "❌"
        cit = f"<@&{self.sel_citizen}>" if self.sel_citizen else "❌"
        return f"**Config Actuelle :**\nLanguage: `{self.sel_lang}`\nService: {svc}\nLogs: {log}\nDirection: {rol}\nAuto-Role: {aut}\nCitoyen: {cit}"
        
    async def cb_fr(self, i): self.sel_lang='fr'; self.update_components(); await self.refresh(i)
    async def cb_en(self, i): self.sel_lang='en'; self.update_components(); await self.refresh(i)
    async def cb_next(self, i): self.page = 2; self.update_components(); await self.refresh(i)
    async def cb_back(self, i): self.page = 1; self.update_components(); await self.refresh(i)
    async def cb_save(self, i): t=config.TRANSLATIONS[self.sel_lang]; await i.response.send_modal(GoalModal(self, t))
    
    async def interaction_check(self, i):
        cid = i.data.get('custom_id'); vals = i.data.get('values', [])
        
        # Sauvegarde temporaire des choix dans l'objet view
        if cid == "svc" and vals: self.sel_service = vals[0]
        elif cid == "log" and vals: self.sel_logs = vals[0]
        elif cid == "role": self.sel_role = [int(v) for v in vals]
        elif cid == "autorole": self.sel_autorole = [int(v) for v in vals]
        elif cid == "citizen" and vals: self.sel_citizen = vals[0]
        
        # Si c'est un menu de sélection, on defer pour éviter "L'interaction a échoué"
        # et on refresh l'affichage
        if cid in ["svc", "log", "role", "autorole", "citizen"]: 
            await i.response.defer()
            await self.refresh(i)
            return False # On stop ici car on a géré l'affichage manuellement via refresh
            
        return True