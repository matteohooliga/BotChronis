import os
from dotenv import load_dotenv

# Chargement des variables d'environnement
load_dotenv()

# Informations du bot
BOT_NAME = "Chronis"
BOT_COLOR = 0x6100bd  # VIOLET (Couleur principale)
BOT_VERSION = "3.2.0"
OWNER_ID = "820572214750871573"

# --- CONFIGURATION FEEDBACK & LOGS ---
DEV_FEEDBACK_CHANNEL_ID = 1441031492061892670
DEV_FEEDBACK_ROLE_ID = 1442965292119757037
DEV_LOG_CHANNEL_ID = 1441382041831739526

# --- CONFIGURATION BASE DE DONNÉES (Sécurisée via .env) ---
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "chronos")

# Liens
GITHUB_LINK = "https://github.com/matteohooliga/BotChronis"
SUPPORT_LINK = "" 
VOTE_LINK = "https://top.gg/bot/1440743920953725118/vote"

# --- MARKETING & AFFILIATION ---
INVITE_LINK = "https://discord.com/api/oauth2/authorize?client_id=1440743920953725118&permissions=8&scope=bot%20applications.commands"
AFFILIATE_LINK = "https://www.hosterfy.com/?a=chronisbot"
AFFILIATE_TEXT = "🚀 Hébergez votre serveur avec -5% de réduction chez notre partenaire Hosterfy avec le code promo **CHRONISBOT** !"

# Configuration des embeds
EMBED_TITLE = "🔍 Utilisateur(s) en service"
EMBED_DESCRIPTION_EMPTY = "Aucun utilisateur n'est en service… 😢"
EMBED_SINCE = "• Depuis"
EMBED_FOOTER = f"Chronis V{BOT_VERSION} | By matteohooliga"

# --- COULEURS DYNAMIQUES ---
COLOR_GREEN = 0x00FF00
COLOR_ORANGE = 0xF39C12
COLOR_RED = 0xFF0000
COLOR_PURPLE = 0x6100bd
COLOR_DARK_BLUE = 0x00008B
COLOR_BLUE = COLOR_DARK_BLUE 

THRESHOLD_LOW = 5
BUTTONS = {
    "start": {"custom_id": "service_start", "emoji": "✨"},
    "pause": {"custom_id": "service_pause", "emoji": "🍎"},
    "stop": {"custom_id": "service_stop", "emoji": "🌙"}
}

# --- CONFIGURATION PREMIUM ---
PREMIUM_SKU_ID = 1480905473665536182
FREE_RDV_LIMIT = 3

# ==============================================================================
#                            TRADUCTIONS (FR / EN)
# ==============================================================================
TRANSLATIONS = {
    "fr": {
        # --- BOUTONS GÉNÉRAUX ---
        "btn_invite": "Inviter le Bot",
        "btn_source": "Code Source",
        "btn_support": "Support",
        "btn_feedback": "Avis / Bug",
        "btn_refresh": "Actualiser",
        "btn_start": "Démarrer son service",
        "btn_pause": "Pause / Reprise de service",
        "btn_stop": "Fin de service",
        "btn_next": "Page Suivante >>",
        "btn_prev": "<< Page Précédente",
        "btn_vote": "Voter pour le bot",

        # --- PANNEAU SETUP (/setup) ---
        "setup_panel_title": "🛠️ Panneau de Configuration",
        "setup_panel_desc": "Configurez Chronis via les menus ci-dessous. Cliquez **Valider** lorsque vous avez terminé.",
        "setup_panel_desc_1": "PAGE 1/3 : **Général**\nConfigurez la langue et les salons.",
        "setup_panel_desc_2": "PAGE 2/3 : **Rôles**\nConfigurez les rôles spéciaux.",
        "setup_panel_desc_3": "PAGE 3/3 : **Tâches Automatiques (Premium)**\nChoisissez le jour de la purge automatique.\n*(L'heure exacte sera demandée en cliquant sur Valider)*",
        "setup_btn_next": "Suivant ➡️", 
        "setup_btn_back": "⬅️ Retour",
        "setup_ph_lang": "🌍 Choisir la langue",
        "setup_ph_service": "📢 Salon  Prise de Service (Actuel : {val})",
        "setup_ph_logs": "📜 Salon Logs (Actuel : {val})",
        "setup_ph_role": "👔 Rôle Direction (Actuel : {val})",
        "setup_ph_autorole": "🏆 Rôle Auto (Actuel : {val})",
        "setup_ph_goal": "🎯 Objectif Hebdo",
        "setup_btn_save": "Valider la configuration",
        "setup_err_no_service": "❌ Erreur : Vous devez obligatoirement sélectionner un salon pour la Prise de Service !",
        "setup_success": "✅ **Configuration sauvegardée !**\nLe panneau de service a été envoyé dans {channel}.",
        "setup_complete": "✅ Config Terminée",
        "setup_logs": "\nLogs activés.",
        "log_setup_title": "✅ Logs Config",
        "log_setup_desc": "Ce salon recevra désormais les logs d'activité.",
        "setup_role": "\nRôle Direction : {role}.",
        "setup_val_none": "Aucun",

        # --- MESSAGES DE SERVICE ---
        "service_started": "✅ **Service démarré** ! Bon courage.",
        "service_already_started": "⚠️ Vous êtes déjà en service !",
        "service_paused": "⏸️ **Pause démarrée** !",
        "service_resumed": "▶️ **Service repris** !",
        "service_not_started": "⚠️ Vous devez d'abord démarrer votre service !",
        "service_stopped": "🛑 **Service terminé** !\n\n**Total** : {duration}\n**Pause** : {pause}\n**Effectif** : {effective}",
        "service_forced_stop": "🔧 **Fermeture forcée** pour {user}.\n**Durée** : {duration}",
        "no_active_session": "❌ Aucune session active trouvée.",
        "embed_title": "🔍 Utilisateur(s) en service",
        "embed_empty": "Aucun utilisateur n'est en service… 😢",
        "embed_since": "• Depuis",

        # --- STATISTIQUES ---
        "stats_title": "📊 Statistiques de {name}",
        "stats_no_data": "Aucune donnée enregistrée.",
        "global_title": "📊 Classement Global du Serveur",
        "stats_fields": ["Sessions", "Temps total", "Moyenne", "Max", "Min"],
        "global_fields": ["Total Sessions", "Temps Cumulé", "Utilisateurs"],
        "goal_warning_title": "🚨 OBJECTIF NON ATTEINT",
        "goal_warning_desc": "Attention : Votre temps est inférieur à l'objectif ({goal}).",
        
        # --- DETAILS ---
        "det_title": "📄 Rapport Détaillé : {user}",
        "det_stats": "📊 Statistiques",
        "det_history": "📜 Historique des Sessions ({count})",
        "det_range": "🗓️ **Période d'activité**\n**Premier service** : {first}\n**Dernier service** : {last}\n\n",
        "det_type_service": "🟢 Service",
        "det_type_adjust": "🔧 Ajustement Admin",

        # --- ÉDITION DE TEMPS ---
        "edit_success": "✅ Temps modifié pour {user}.",
        "edit_desc": "Le temps de service a été modifié manuellement.",
        "edit_field_action": "Action",
        "edit_field_amount": "Montant",
        "edit_field_new_total": "Nouveau Total",
        "edit_field_old": "Ancien Total",
        "edit_field_admin": "Modérateur",
        "edit_field_target": "Cible",
        "time_added": "Ajout (+)", 
        "time_removed": "Retrait (-)",
        "et_view_title": "⏱️ Modification de Temps",
        "et_view_desc": "Que souhaitez-vous faire pour le temps de service de {user} ?",
        "et_btn_add": "Ajouter (+)",
        "et_btn_remove": "Retirer (-)",
        "et_modal_add": "Ajouter du temps",
        "et_modal_remove": "Retirer du temps",
        "et_label_hours": "Heures",
        "et_label_minutes": "Minutes",
        "et_label_seconds": "Secondes",
        "et_placeholder": "0",

        # --- ADMIN PAUSE & START ---
        "admin_pause_success": "⏸️ Le service de {user} a été mis en pause par un administrateur.",
        "admin_resume_success": "▶️ Le service de {user} a été relancé par un administrateur.",
        "admin_start_success": "▶️ Le service de {user} a été démarré de force par un administrateur.", 
        "log_admin_pause_title": "⏸️ Pause Forcée",
        "log_admin_resume_title": "▶️ Reprise Forcée",
        "log_admin_start_title": "▶️ Démarrage Forcé", 
        "log_admin_start_desc": "Service forcé par {admin} pour {user}.", 

        # --- MAINTENANCE ---
        "maint_embed_title": "🚧 MAINTENANCE EN COURS",
        "maint_embed_desc": "Le système est temporairement verrouillé pour maintenance.\nLes prises de service sont impossibles.",
        "maint_enabled": "🟠 **Mode Maintenance ACTIVÉ**.",
        "maint_disabled": "🟢 **Mode Maintenance DÉSACTIVÉ**.",
        "maint_block_msg": "⛔ **Maintenance** : Le système est verrouillé.",

        # --- LOGS SERVEUR ---
        "log_guild_join_title": "➕ Nouveau Serveur",
        "log_guild_join_desc": "Le bot a été ajouté à un serveur.",
        "log_guild_join_name": "Nom",
        "log_guild_join_id": "ID",
        "log_guild_join_owner": "Propriétaire",
        "log_guild_join_members": "Membres",
        
        # --- BLACKLIST ---
        "bl_add_success": "⛔ **{user}** a été ajouté à la Blacklist.",
        "bl_remove_success": "✅ **{user}** a été retiré de la Blacklist.",
        "bl_already": "⚠️ Cet utilisateur est déjà blacklisté.",
        "bl_not_found": "⚠️ Cet utilisateur n'est pas dans la blacklist.",
        "bl_error": "⛔ **Accès Interdit** : Vous êtes blacklisté.",
        "infos_title": "📊 Informations Bot", "infos_desc": "Le bot est présent sur **{count}** serveurs.",

        # --- PRESENCE REACTION ---
        "pres_react_title": "📊 Liste des Réactions",
        "pres_react_desc": "Liste des utilisateurs ayant réagi au dernier message dans {channel}.",
        "pres_react_empty": "⚠️ Aucune réaction trouvée sur le dernier message.",
        "error_no_message": "❌ Aucun message trouvé dans ce salon.",
        "error_channel_type": "❌ Ce salon n'est pas textuel.",

        # --- DELROLE & LOGS ---
        "setup_ph_citizen": "👤 Rôle Citoyen",
        "log_delrole_title": "🧹 Razzia des Rôles (Wipe)",
        "log_delrole_desc": "Tous les rôles de {user} ont été retirés par {admin}.\n**Rôle conservé :** <@&{citizen}>",
        "delrole_success": "✅ **Wipe effectué** sur {user}.\n🗑️ **{count}** rôles retirés.",
        "delrole_error_config": "❌ Erreur : Le **Rôle Citoyen** n'est pas configuré dans `/setup` (Page 2).",
        "delrole_no_roles": "⚠️ Cet utilisateur n'avait aucun rôle à retirer.",
        
        # --- ADMIN COMMANDS (+) ---
        "cmd_sync_start": "⏳ **Synchronisation en cours...**",
        "cmd_sync_end": "✅ **Synchronisation terminée !** ({count} commandes)",
        "cmd_restart_start": "👋 **Redémarrage en cours...**",
        "cmd_restart_end": "✅ **Redémarrage terminé !**",
        "log_sync_title": "🔄 Sync", "log_sync_desc": "Par {user}.",
        "log_restart_title": "🔄 Restart", "log_restart_desc": "Par {user}.",
        "log_stat_wip": "En cours...", "log_stat_done": "Terminé",
        "log_footer_done": "Fini le {date}",
        
        # --- FEEDBACK & VOTE ---
        "feedback_modal_title": "Envoyer un Feedback",
        "feedback_subject": "Sujet",
        "feedback_label": "Message",
        "feedback_placeholder": "Détails...",
        "feedback_sent": "✅ Envoyé !",
        "feedback_error": "❌ Erreur.",
        "log_new_feedback": "📨 Nouveau Rapport",
        "fb_select_placeholder": "Type...",
        "fb_opt_review": "Avis",
        "fb_opt_bug": "Bug",
        "fb_review_title": "Avis",
        "fb_review_subject": "Titre",
        "fb_review_rating": "Note (1-5)",
        "fb_review_comment": "Commentaire",
        "fb_log_review_title": "⭐ Avis Reçu",
        "fb_field_rating": "Note",
        "fb_bug_title": "Bug",
        "fb_bug_subject": "Titre",
        "fb_bug_desc": "Description",
        "fb_bug_media": "Lien image",
        "fb_log_bug_title": "🐛 Bug Reçu",
        "fb_field_media": "Preuve",
        "vote_msg": "Merci de soutenir le bot ! Cliquez ci-dessous pour voter :",
        
        # --- RDV SYSTEM ---
        "rdv_setup_title": "🏥 Config Rendez-Vous",
        "rdv_setup_desc": "Configurez les salons et le rôle.\n\n**Motifs actuels :**\n{types}", 
        "rdv_ph_public": "Salon Public (Affichage Panel)",
        "rdv_ph_staff": "Salon Staff (Réception demandes)",
        "rdv_ph_transcript": "Salon Logs/Transcripts (Staff)", 
        "rdv_ph_role": "Rôle Médecin/Staff",
        "rdv_btn_add": "Ajouter Motif",
        "rdv_btn_del": "Supprimer Motif",
        "rdv_modal_type_title": "Nouveau Motif",
        "rdv_modal_type_label": "Nom (ex: Consultation)",
        "rdv_panel_title": "📅 Prise de Rendez-Vous",
        "rdv_panel_desc": "Sélectionnez un motif ci-dessous pour prendre RDV.",
        "rdv_select_ph": "Choisir le motif...",
        "rdv_modal_book_title": "Formulaire RDV",
        "rdv_modal_book_label": "Disponibilités / Raison",
        "rdv_new_req_title": "📩 Nouvelle Demande",
        "rdv_btn_accept": "Accepter",
        "rdv_btn_refuse": "Refuser",
        "rdv_accepted": "✅ Dossier créé : {channel}",
        "rdv_refused": "❌ Refusé par {user}.",
        "rdv_ticket_welcome": "👋 Bonjour {user} !\nUn {role} va prendre en charge votre demande de **{type}**.\n\n**Infos :** {info}",
        "rdv_btn_close": "Fermer le dossier",
        "rdv_err_config": "⚠️ Configuration incomplète.",
        "rdv_err_perms": "⛔ Vous n'avez pas le rôle requis pour gérer ce RDV.",
        "rdv_modal_close_title": "Fermeture du Dossier", 
        "rdv_modal_close_label": "Raison / Conclusion", 
        
        # LOGS RDV
        "rdv_log_closed_title": "🔒 RDV Fermé",
        "rdv_log_closed_desc": "Le ticket de {patient} a été fermé.",
        "rdv_log_accepted_title": "✅ RDV Accepté",
        "rdv_log_accepted_desc": "Ticket accepté par {staff} pour {patient}.",
        "rdv_transcript_dm": "📄 Voici le transcript de votre ticket RDV.",

        # --- ABSENCE ---
        "abs_modal_title": "Déclarer une absence", 
        "abs_start_label": "Début", "abs_start_ph": "JJ/MM/AAAA",
        "abs_end_label": "Fin", "abs_end_ph": "JJ/MM/AAAA",
        "abs_reason_label": "Raison", "abs_reason_ph": "Motif...",
        "abs_embed_title": "📅 Absence de {user}", 
        "abs_field_dates": "Dates", "abs_field_duration": "Durée", "abs_field_reason": "Raison", 
        "abs_error_format": "❌ Date invalide.", "abs_error_logic": "❌ Fin < Début.",
        "abs_user_field": "👤 Agent",
        "sumall_tag_absence": "🚫 **Absence**",
        "abs_btn_end": "✅ Fin de l'absence",
        "abs_ended": "✅ Absence terminée (Retour anticipé).",
        "abs_err_owner": "⛔ Seul l'auteur peut terminer l'absence.",

        # --- INFO & ABOUT ---
        "about_stats_title": "📊 Statistiques",
        "about_tech_title": "🛠️ Technique",
        "about_val_servers": "**Serveurs** : `{val}`",
        "about_val_users": "**Utilisateurs** : `{val}`",
        "about_val_version": "**Python** : `{py}` | **D.py** : `{dpy}`",
        "about_maint_title": "🔄 Maintenance Automatique",
        "about_maint_desc": "🕒 **03h00 UTC** : Redémarrage journalier.\n⚠️ Tous les services actifs sont fermés automatiquement.",

        # --- SERVER STATS (Statistiques Avancées) ---
        "srv_stats_title": "📈 Audit d'Activité Serveur",
        "srv_stats_desc": "Analyse sur une période de **{days}** jours actifs.",
        "srv_field_global": "🌍 Données Globales",
        "srv_val_total_time": "• Temps Cumulé : `{val}`",
        "srv_val_sessions": "• Sessions Totales : `{val}`",
        "srv_val_total_agents": "• Agents Uniques : `{val}`", 
        "srv_field_daily": "📅 Moyennes Journalières",
        "srv_val_people_day": "• Effectif Moyen : `{val} agents/jour`",
        "srv_val_time_day": "• Temps Moyen : `{val}/agent/jour`",
        "srv_field_weekly": "🗓️ Moyennes Hebdomadaires",
        "srv_val_time_week": "• Temps Moyen : `{val}/agent/semaine`",

        # --- SERVER STATS INTERACTIF ---
        "srv_select_placeholder": "Choisir la vue (Hebdo/Journalier)",
        "srv_opt_weekly": "Vue Hebdomadaire (7 jours)",
        "srv_opt_daily": "Vue Journalière (24 heures)",
        "srv_btn_next_graph": "Graphique Suivant ➡️",
        
        "srv_title_weekly_hours": "📊 Heures Cumulées (7j)",
        "srv_title_weekly_staff": "👥 Effectif Unique (7j)",
        "srv_title_weekly_avg": "⏱️ Temps Moyen (7j)",
        
        "srv_title_daily_activity": "📈 Activité par Heure (00h-23h)",
        "srv_title_daily_avg": "⏱️ Temps Moyen par Session (00h-23h)",
        "srv_title_daily_starts": "🚀 Prises de service par Heure",
        "srv_title_daily_sessions": "🔄 Sessions Lancées (7j)",
        
        "srv_label_hours": "Heures",
        "srv_label_agents": "Agents",
        "srv_label_activity": "Présence Cumulée",

        # --- COMMANDES DYNAMIQUES (Employees, Presence, etc.) ---
        "emp_title": "👥 Effectif ({count})",
        "emp_roles_target": "**Rôles ciblés :** {roles}\n\n",
        "emp_no_config": "⚠️ Aucun rôle 'Auto' n'est configuré dans `/setup`.",
        "emp_list_empty": "⚠️ La liste des rôles auto est vide.",
        "emp_roles_not_found": "⚠️ Les rôles configurés n'existent plus sur le serveur.",
        "emp_no_members": "❌ Aucun membre trouvé avec les rôles : {roles}",
        
        "pres_title": "📊 Présence Réaction",
        "pres_desc": "Analyse du message : {url}",
        "pres_no_react_msg": "⚠️ Aucun message avec des réactions trouvé dans les 50 derniers messages.",
        "pres_no_users": "⚠️ Des réactions existent mais aucun utilisateur trouvé.",
        "pres_footer": "Message du {date}",
        
        "abs_list_title": "📅 Absences en cours",
        "abs_list_empty": "✅ **Aucune absence en cours.**\nTout le monde est disponible.",
        "abs_reason_title": "📝 **Raison :** {reason}",
        "abs_footer": "Total : {count} absent(s)",
        
        "pause_list_title": "⏸️ En Pause",
        "pause_list_empty": "Personne n'est en pause.",
        
        "msg_truncated": "\n... *(liste tronquée)*",
        
        # --- MP FERMETURE TICKET ---
        "dm_close_title": "🔒 Ticket Fermé",
        "dm_close_guild": "Serveur",
        "dm_close_date": "Généré le",
        "dm_close_staff": "Fermé par",
        "dm_close_reason": "Raison",


        # --- HELP DÉTAILLÉ FR ---
        "help_title": "📚 Menu d'Aide", 
        "help_desc": "Veuillez choisir une catégorie ci-dessous pour voir les commandes disponibles.",
        "help_contact_dm": "💬 Besoin de plus d'aide ? Envoie un message privé à Chronis : le propriétaire du bot recevra ton message et pourra te répondre.",
        "help_cat_user": "Utilisateurs", 
        "help_cat_admin": "Administrateurs",
        "help_cat_premium": "Premium",
        "help_back": "Retour", 
        "help_back_lang": "Changer la Langue",
        "help_user_desc": "Commandes accessibles à tous les membres :", 
        "help_admin_desc": "Commandes réservées au Staff :",
        "help_premium_desc": "✨ **Fonctionnalités et commandes exclusives à l'abonnement :**",
        
        "help_cmds_user": (
            "**• `/about`**\n"
            "└ Informations techniques du bot.\n\n"
            "**• `/absence`**\n"
            "└ Formulaire pour déclarer une absence.\n\n"
            "**• `/absences_list`**\n"
            "└ Voir la liste des personnes actuellement absentes.\n\n"
            "**• `/feedback`**\n"
            "└ Envoyer une suggestion ou signaler un bug.\n\n"
            "**• `/help`**\n"
            "└ Affiche ce menu d'aide.\n\n"
            "**• `/sum`**\n"
            "└ Affiche vos statistiques personnelles.\n\n"
            "**• `/sumall`**\n"
            "└ Affiche le classement général du serveur.\n\n"
            "**• `/vote`**\n"
            "└ Lien pour voter pour le bot."
        ),
        
        "help_cmds_admin_1": (
            "**• `/auto_role`**\n"
            "└ Attribuer manuellement les rôles configurés.\n\n"
            "**• `/cancel [joueur]`**\n"
            "└ Annuler une session sans sauvegarde.\n\n"
            "**• `/close [joueur]`**\n"
            "└ Forcer la fin de service d'un agent (sauvegarde).\n\n"
            "**• `/config_rdv`**\n"
            "└ Configurer le système de rendez-vous.\n\n"
            "**• `/delrole [joueur]`**\n"
            "└ Retirer tous les rôles sauf Citoyen.\n\n"
            "**• `/edittime`**\n"
            "└ Modifier manuellement le temps (Ajout/Retrait).\n\n"
            "**• `/employees`**\n"
            "└ Liste des membres ayant le rôle auto."
        ),

        "help_cmds_admin_2": (
            "**• `/forcestart [joueur]`**\n"
            "└ Forcer le début de service d'un agent.\n\n"
            "**• `/pause [joueur]`**\n"
            "└ Forcer la pause d'un agent.\n\n"
            "**• `/pauselist`**\n"
            "└ Affiche la liste des agents en pause.\n\n"
            "**• `/reaction_list [salon]`**\n"
            "└ Liste des agents actifs/absents via réactions.\n\n"
            "**• `/remove_user`**\n"
            "└ Supprimer définitivement le dossier d'un agent.\n\n"
            "**• `/reset_server`**\n"
            "└ Réinitialisation globale (Hebdo/Mensuel).\n\n"
            "**• `/server_stats`**\n"
            "└ Statistiques et graphiques avancés du serveur.\n\n"
            "**• `/setup`**\n"
            "└ Panneau de configuration générale du bot."
        ),

        "help_cmds_premium": (
            "**• `/defcon`**\n"
            "└ Diffuser une alerte d'urgence personnalisée.\n\n"
            "**• `/details [joueur]`**\n"
            "└ Accéder à l'historique détaillé des sessions.\n\n"
            "**• `/export`**\n"
            "└ Télécharger les statistiques globales en format Excel.\n\n"
            "**• `/premium`**\n"
            "└ Gérer ou découvrir l'abonnement du serveur.\n\n"
            "**🌟 Avantages Inclus :**\n"
            "• 📊 **Analytics Comparatifs** : Rapport hebdo avec progression de l'activité (%).\n"
            "• 🔔 **Relance Quota Auto** : MP automatique aux retardataires 24h avant la purge.\n"
            "• 🏷️ Rôle `En Service` automatique.\n"
            "• 🎨 Personnalisation de la couleur (Embeds).\n"
            "• ⏰ Purge automatique paramétrable.\n"
            "• 🏥 Motifs de RDV illimités.\n"
            "• 🔕 Aucune publicité partenaire dans Chronis."
        ),

        # --- LOGS GÉNÉRAUX ---
        "log_start_title": "🟢 Prise de Service", "log_start_desc": "L'agent {user} a pris son service.",
        "log_pause_title": "⏸️ Mise en Pause", "log_pause_desc": "L'agent {user} s'est mis en pause.",
        "log_resume_title": "▶️ Reprise de Service", "log_resume_desc": "L'agent {user} a repris son service.",
        "log_stop_title": "🛑 Fin de Service", "log_stop_desc": "L'agent {user} a terminé son service.",
        
        "log_force_close_title": "🔧 Fermeture Forcée", 
        "log_force_close_desc": "La session de {user} a été fermée par {admin}.",
        
        "log_edit_time_title": "📈 Temps Modifié", 
        "log_edit_time_desc": "Modification manuelle par {admin}.",
        
        "log_reset_title": "⚠️ Réinitialisation Totale", 
        "log_reset_desc": "Serveur réinitialisé par {admin}.",
        
        "log_cancel_title": "🗑️ Annulation de Service", 
        "log_cancel_desc": "Session annulée par {admin} pour {user}.",
        
        "log_remove_title": "👤 Dossier Supprimé", 
        "log_remove_desc": "Données de {user} supprimées par {admin}.",
        
        "log_autorole_title": "🏆 Attribution Rôle", 
        "log_autorole_desc": "Rôles donnés à {user} par {admin}.",
        
        "log_admin_pause_desc": "Pause forcée par {admin}.",
        "log_admin_resume_desc": "Reprise forcée par {admin}.",
        
        "cancel_success": "🗑️ Session annulée et supprimée.",

        "log_maint_title": "🔄 Maintenance", "log_maint_desc": "Redémarrage auto.",
        "log_bot_stop_title": "🛑 Bot Stop", "log_bot_stop_desc": "Arrêt manuel.",
        "log_bot_start_title": "🟢 Bot Start", "log_bot_start_desc": "Bot en ligne.",
        
        # --- ERREURS ---
        "error_generic": "❌ Erreur système.", "error_perms": "⛔ Permission refusée.", "error_admin_only": "⛔ Admin seulement.",
        "error_invalid_input": "❌ Saisie invalide.", "error_db": "⚠️ Erreur DB.", "error_no_role": "⚠️ Pas de rôle auto.",
        "role_added": "✅ Rôle {role} ajouté à {user}."
    },
    "en": {
        # --- GENERAL BUTTONS ---
        "btn_invite": "Invite Bot",
        "btn_source": "Source Code",
        "btn_support": "Support",
        "btn_feedback": "Review / Bug",
        "btn_refresh": "Refresh",
        "btn_start": "Start Service",
        "btn_pause": "Pause / Resume Service",
        "btn_stop": "End Service",
        "btn_next": "Next Page >>",
        "btn_prev": "<< Previous Page",
        "btn_vote": "Vote for Bot", 

        # --- SETUP PANEL (/setup) ---
        "setup_panel_title": "🛠️ Configuration Panel",
        "setup_panel_desc": "Configure Chronis via the menus below. Click **Validate** when finished.",
        "setup_panel_desc_1": "PAGE 1/3: **General**\nConfigure language and channels.",
        "setup_panel_desc_2": "PAGE 2/3: **Roles**\nConfigure special roles.",
        "setup_panel_desc_3": "PAGE 3/3: **Tasks (Premium)**\nSelect purge day.\n*(Exact time will be asked upon validation)*",
        "setup_btn_next": "Next ➡️", 
        "setup_btn_back": "⬅️ Back",
        "setup_ph_lang": "🌍 Choose Language",
        "setup_ph_service": "📢 Service Channel (Current: {val})",
        "setup_ph_logs": "📜 Logs Channel (Current: {val})",
        "setup_ph_role": "👔 Direction Role (Current: {val})",
        "setup_ph_autorole": "🏆 Auto Role (Current: {val})",
        "setup_ph_goal": "🎯 Weekly Goal",
        "setup_btn_save": "Validate Configuration",
        "setup_err_no_service": "❌ Error: You must select a Service Channel!",
        "setup_success": "✅ **Configuration saved!**\nThe service panel has been sent to {channel}.",
        "setup_complete": "✅ Config Complete",
        "setup_logs": "\nLogs enabled.",
        "log_setup_title": "✅ Logs Config",
        "log_setup_desc": "This channel will now receive activity logs.",
        "setup_role": "\nDirection Role: {role}.",
        "setup_val_none": "None",

        # --- SERVICE MESSAGES ---
        "service_started": "✅ **Service started!** Good luck.",
        "service_already_started": "⚠️ You are already on duty!",
        "service_paused": "⏸️ **Pause started!**",
        "service_resumed": "▶️ **Service resumed!**",
        "service_not_started": "⚠️ You must start your service first!",
        "service_stopped": "🛑 **Service ended!**\n\n**Total**: {duration}\n**Pause**: {pause}\n**Effective**: {effective}",
        "service_forced_stop": "🔧 **Force closed** for {user}.\n**Duration**: {duration}",
        "no_active_session": "❌ No active session found.",
        "embed_title": "🔍 Users on Duty",
        "embed_empty": "No users on duty... 😢",
        "embed_since": "• Since",

        # --- STATISTICS ---
        "stats_title": "📊 Statistics: {name}",
        "stats_no_data": "No data recorded.",
        "global_title": "📊 Global Server Leaderboard",
        "stats_fields": ["Sessions", "Total Time", "Average", "Max", "Min"],
        "global_fields": ["Total Sessions", "Cumulative Time", "Users"],
        "goal_warning_title": "🚨 GOAL MISSED",
        "goal_warning_desc": "Warning: Your time is under the target ({goal}).",
        
        # --- DETAILS ---
        "det_title": "📄 Detailed Report: {user}",
        "det_stats": "📊 Statistics",
        "det_history": "📜 Session History ({count})",
        "det_range": "🗓️ **Activity Period**\n**First Shift**: {first}\n**Last Shift**: {last}\n\n",
        "det_type_service": "🟢 Service",
        "det_type_adjust": "🔧 Admin Adjustment",

        # --- TIME EDITING ---
        "edit_success": "✅ Time modified for {user}.",
        "edit_desc": "Service time was modified manually.",
        "edit_field_action": "Action",
        "edit_field_amount": "Amount",
        "edit_field_new_total": "New Total",
        "edit_field_old": "Old Total",
        "edit_field_admin": "Moderator",
        "edit_field_target": "Target",
        "time_added": "Addition (+)", 
        "time_removed": "Deduction (-)",
        "et_view_title": "⏱️ Time Modification",
        "et_view_desc": "What do you want to do with {user}'s service time?",
        "et_btn_add": "Add (+)",
        "et_btn_remove": "Remove (-)",
        "et_modal_add": "Add Time",
        "et_modal_remove": "Remove Time",
        "et_label_hours": "Hours",
        "et_label_minutes": "Minutes",
        "et_label_seconds": "Seconds",
        "et_placeholder": "0",

        # --- ADMIN PAUSE & START ---
        "admin_pause_success": "⏸️ {user}'s service was paused by an administrator.",
        "admin_resume_success": "▶️ {user}'s service was resumed by an administrator.",
        "admin_start_success": "▶️ {user}'s service was force started by an administrator.",
        "log_admin_pause_title": "⏸️ Forced Pause",
        "log_admin_resume_title": "▶️ Forced Resume",
        "log_admin_start_title": "▶️ Forced Start",
        "log_admin_start_desc": "Service forced by {admin} for {user}.",

        # --- MAINTENANCE ---
        "maint_embed_title": "🚧 MAINTENANCE IN PROGRESS",
        "maint_embed_desc": "The system is temporarily locked for maintenance.\nService starts are disabled.",
        "maint_enabled": "🟠 **Maintenance Mode ON**.",
        "maint_disabled": "🟢 **Maintenance Mode OFF**.",
        "maint_block_msg": "⛔ **Maintenance**: System locked.",

        # --- SERVER LOGS ---
        "log_guild_join_title": "➕ New Server",
        "log_guild_join_desc": "Bot added to a server.",
        "log_guild_join_name": "Name",
        "log_guild_join_id": "ID",
        "log_guild_join_owner": "Owner",
        "log_guild_join_members": "Members",
        
        # --- BLACKLIST ---
        "bl_add_success": "⛔ **{user}** has been added to the Blacklist.",
        "bl_remove_success": "✅ **{user}** has been removed from the Blacklist.",
        "bl_already": "⚠️ This user is already blacklisted.",
        "bl_not_found": "⚠️ This user is not in the blacklist.",
        "bl_error": "⛔ **Access Denied**: You are blacklisted.",
        "infos_title": "📊 Bot Information", "infos_desc": "Bot is present on **{count}** servers.",

        # --- REACTION PRESENCE ---
        "pres_react_title": "📊 Reaction List",
        "pres_react_desc": "List of users who reacted to the last message in {channel}.",
        "pres_react_empty": "⚠️ No reactions found on the last message.",
        "error_no_message": "❌ No message found in this channel.",
        "error_channel_type": "❌ This is not a text channel.",

        # --- DELROLE & LOGS ---
        "setup_ph_citizen": "👤 Citizen Role",
        "log_delrole_title": "🧹 Role Wipe",
        "log_delrole_desc": "All roles from {user} were removed by {admin}.\n**Kept Role:** <@&{citizen}>",
        "delrole_success": "✅ **Wipe complete** for {user}.\n🗑️ **{count}** roles removed.",
        "delrole_error_config": "❌ Error: **Citizen Role** is not configured in `/setup` (Page 2).",
        "delrole_no_roles": "⚠️ This user had no roles to remove.",
        
        # --- ADMIN COMMANDS (+) ---
        "cmd_sync_start": "⏳ **Syncing in progress...**",
        "cmd_sync_end": "✅ **Sync complete!** ({count} commands)",
        "cmd_restart_start": "👋 **Restarting in progress...**",
        "cmd_restart_end": "✅ **Restart complete!**",
        "log_sync_title": "🔄 Sync", "log_sync_desc": "By {user}.",
        "log_restart_title": "🔄 Restart", "log_restart_desc": "By {user}.",
        "log_stat_wip": "In progress...", "log_stat_done": "Done",
        "log_footer_done": "Finished on {date}",
        
        # --- FEEDBACK & VOTE ---
        "feedback_modal_title": "Send Feedback",
        "feedback_subject": "Subject",
        "feedback_label": "Message",
        "feedback_placeholder": "Details...",
        "feedback_sent": "✅ Sent!",
        "feedback_error": "❌ Error.",
        "log_new_feedback": "📨 New Report",
        "fb_select_placeholder": "Type...",
        "fb_opt_review": "Review",
        "fb_opt_bug": "Bug",
        "fb_review_title": "Review",
        "fb_review_subject": "Title",
        "fb_review_rating": "Rating (1-5)",
        "fb_review_comment": "Comment",
        "fb_log_review_title": "⭐ Review Received",
        "fb_field_rating": "Rating",
        "fb_bug_title": "Bug",
        "fb_bug_subject": "Title",
        "fb_bug_desc": "Description",
        "fb_bug_media": "Image Link",
        "fb_log_bug_title": "🐛 Bug Received",
        "fb_field_media": "Proof",
        "vote_msg": "Thanks for supporting the bot! Click below to vote:", 
        
        # --- RDV SYSTEM ---
        "rdv_setup_title": "🏥 Appointment Config",
        "rdv_setup_desc": "Configure channels and role.\n\n**Current Reasons:**\n{types}",
        "rdv_ph_public": "Public Channel (Panel Display)",
        "rdv_ph_staff": "Staff Channel (Receive Requests)",
        "rdv_ph_transcript": "Logs/Transcript Channel (Staff)",
        "rdv_ph_role": "Doctor/Staff Role",
        "rdv_btn_add": "Add Reason",
        "rdv_btn_del": "Remove Reason",
        "rdv_modal_type_title": "New Reason",
        "rdv_modal_type_label": "Name (ex: Consultation)",
        "rdv_panel_title": "📅 Appointment Booking",
        "rdv_panel_desc": "Select a reason below to book an appointment.",
        "rdv_select_ph": "Choose reason...",
        "rdv_modal_book_title": "Appointment Form",
        "rdv_modal_book_label": "Availability / Reason",
        "rdv_new_req_title": "📩 New Request",
        "rdv_btn_accept": "Accept",
        "rdv_btn_refuse": "Refuse",
        "rdv_accepted": "✅ File created: {channel}",
        "rdv_refused": "❌ Refused by {user}.",
        "rdv_ticket_welcome": "👋 Hello {user}!\nA {role} will handle your request for **{type}**.\n\n**Info:** {info}",
        "rdv_btn_close": "Close File",
        "rdv_err_config": "⚠️ Incomplete configuration.",
        "rdv_err_perms": "⛔ You do not have the required role to manage this appointment.",
        "rdv_modal_close_title": "Closing Ticket", 
        "rdv_modal_close_label": "Reason / Conclusion", 
        
        # LOGS RDV
        "rdv_log_closed_title": "🔒 Appointment Closed",
        "rdv_log_closed_desc": "{patient}'s ticket has been closed.",
        "rdv_log_accepted_title": "✅ Appointment Accepted",
        "rdv_log_accepted_desc": "Ticket accepted by {staff} for {patient}.",
        "rdv_transcript_dm": "📄 Here is the transcript of your appointment ticket.",

        # --- ABSENCE ---
        "abs_modal_title": "Declare an Absence", 
        "abs_start_label": "Start", "abs_start_ph": "DD/MM/YYYY",
        "abs_end_label": "End", "abs_end_ph": "DD/MM/YYYY",
        "abs_reason_label": "Reason", "abs_reason_ph": "Reason...",
        "abs_embed_title": "📅 Absence of {user}", 
        "abs_field_dates": "Dates", "abs_field_duration": "Duration", "abs_field_reason": "Reason", 
        "abs_error_format": "❌ Invalid Date.", "abs_error_logic": "❌ End < Start.",
        "abs_user_field": "👤 Agent",
        "sumall_tag_absence": "🚫 **Absence**",
        "abs_btn_end": "✅ End Absence",
        "abs_ended": "✅ Absence ended (Early return).",
        "abs_err_owner": "⛔ Only the author can end the absence.",

        # --- INFO & ABOUT ---
        "about_stats_title": "📊 Statistics",
        "about_tech_title": "🛠️ Technical",
        "about_val_servers": "**Servers**: `{val}`",
        "about_val_users": "**Users**: `{val}`",
        "about_val_version": "**Python**: `{py}` | **D.py**: `{dpy}`",
        "about_maint_title": "🔄 Automatic Maintenance",
        "about_maint_desc": "🕒 **03:00 UTC**: Daily restart.\n⚠️ All active sessions are automatically closed.",

        # --- SERVER STATS (Advanced Stats) ---
        "srv_stats_title": "📈 Server Activity Audit",
        "srv_stats_desc": "Analysis over a period of **{days}** active days.",
        "srv_field_global": "🌍 Global Data",
        "srv_val_total_time": "• Cumulative Time: `{val}`",
        "srv_val_sessions": "• Total Sessions: `{val}`",
        "srv_val_total_agents": "• Unique Agents: `{val}`",
        "srv_field_daily": "📅 Daily Averages",
        "srv_val_people_day": "• Avg Staff: `{val} agents/day`",
        "srv_val_time_day": "• Avg Time: `{val}/agent/day`",
        "srv_field_weekly": "🗓️ Weekly Averages",
        "srv_val_time_week": "• Avg Time: `{val}/agent/week`",

        # --- INTERACTIVE SERVER STATS ---
        "srv_select_placeholder": "Select View (Weekly/Daily)",
        "srv_opt_weekly": "Weekly View (7 days)",
        "srv_opt_daily": "Daily View (24 hours)",
        "srv_btn_next_graph": "Next Graph ➡️",
        
        "srv_title_weekly_hours": "📊 Cumulative Hours (7d)",
        "srv_title_weekly_staff": "👥 Unique Staff (7d)",
        "srv_title_weekly_avg": "⏱️ Average Time (7d)",
        
        "srv_title_daily_activity": "📈 Hourly Activity (00h-23h)",
        "srv_title_daily_avg": "⏱️ Average Time per Session (00h-23h)",
        "srv_title_daily_starts": "🚀 Shifts Started per Hour",
        "srv_title_daily_sessions": "🔄 Sessions Started (7d)",
        
        "srv_label_hours": "Hours",
        "srv_label_agents": "Agents",
        "srv_label_activity": "Cumulative Presence",

        # --- DYNAMIC COMMANDS (Employees, Presence, etc.) ---
        "emp_title": "👥 Workforce ({count})",
        "emp_roles_target": "**Targeted Roles:** {roles}\n\n",
        "emp_no_config": "⚠️ No 'Auto' role configured in `/setup`.",
        "emp_list_empty": "⚠️ The auto role list is empty.",
        "emp_roles_not_found": "⚠️ Configured roles no longer exist on the server.",
        "emp_no_members": "❌ No members found with roles: {roles}",
        
        "pres_title": "📊 Reaction Presence",
        "pres_desc": "Message analysis: {url}",
        "pres_no_react_msg": "⚠️ No message with reactions found in the last 50 messages.",
        "pres_no_users": "⚠️ Reactions exist but no users found.",
        "pres_footer": "Message from {date}",
        
        "abs_list_title": "📅 Active Absences",
        "abs_list_empty": "✅ **No active absences.**\nEveryone is available.",
        "abs_reason_title": "📝 **Reason:** {reason}",
        "abs_footer": "Total: {count} absent(s)",
        
        "pause_list_title": "⏸️ On Break",
        "pause_list_empty": "No one is on break.",
        
        "msg_truncated": "\n... *(list truncated)*",
        
        # --- TICKET CLOSE DM ---
        "dm_close_title": "🔒 Ticket Closed",
        "dm_close_guild": "Server",
        "dm_close_date": "Generated on",
        "dm_close_staff": "Closed by",
        "dm_close_reason": "Reason",

        # --- DETAILED HELP EN ---
        "help_title": "📚 Help Menu", 
        "help_desc": "Please choose a category below to view the available commands.",
        "help_contact_dm": "💬 Need more help? Send Chronis a direct message: the bot owner will receive it and can reply to you.",
        "help_cat_user": "Users", 
        "help_cat_admin": "Administrators",
        "help_cat_premium": "Premium",
        "help_back": "Back", 
        "help_back_lang": "Change Language",
        "help_user_desc": "Commands available to all members:", 
        "help_admin_desc": "Commands restricted to Staff:",
        "help_premium_desc": "✨ **Exclusive commands and features:**",
        
        "help_cmds_user": (
            "**• `/about`**\n"
            "└ Bot technical information.\n\n"
            "**• `/absence`**\n"
            "└ Form to declare an absence.\n\n"
            "**• `/absences_list`**\n"
            "└ See the list of currently absent people.\n\n"
            "**• `/feedback`**\n"
            "└ Send a suggestion or report a bug.\n\n"
            "**• `/help`**\n"
            "└ Displays this help menu.\n\n"
            "**• `/sum`**\n"
            "└ Displays your personal statistics.\n\n"
            "**• `/sumall`**\n"
            "└ Displays the general server leaderboard.\n\n"
            "**• `/vote`**\n"
            "└ Link to vote for the bot."
        ),
        
        "help_cmds_admin_1": (
            "**• `/auto_role`**\n"
            "└ Manually assign configured roles.\n\n"
            "**• `/cancel [player]`**\n"
            "└ Cancel a session without saving.\n\n"
            "**• `/close [player]`**\n"
            "└ Force end an agent's service (save).\n\n"
            "**• `/config_rdv`**\n"
            "└ Configure the appointment system.\n\n"
            "**• `/delrole [player]`**\n"
            "└ Remove all roles except Citizen.\n\n"
            "**• `/edittime`**\n"
            "└ Manually modify time (Add/Remove).\n\n"
            "**• `/employees`**\n"
            "└ List members with the auto role."
        ),

        "help_cmds_admin_2": (
            "**• `/forcestart [player]`**\n"
            "└ Force start an agent's service.\n\n"
            "**• `/pause [player]`**\n"
            "└ Force pause an agent.\n\n"
            "**• `/pauselist`**\n"
            "└ Displays the list of paused agents.\n\n"
            "**• `/reaction_list [channel]`**\n"
            "└ List of active/absent agents via reactions.\n\n"
            "**• `/remove_user`**\n"
            "└ Permanently delete an agent's folder.\n\n"
            "**• `/reset_server`**\n"
            "└ Global reset (Weekly/Monthly).\n\n"
            "**• `/server_stats`**\n"
            "└ Advanced server statistics and graphs.\n\n"
            "**• `/setup`**\n"
            "└ General bot configuration panel."
        ),

        "help_cmds_premium": (
            "**• `/defcon`**\n"
            "└ Broadcast a custom emergency alert.\n\n"
            "**• `/details [player]`**\n"
            "└ Access detailed session history of a player.\n\n"
            "**• `/export`**\n"
            "└ Download global statistics as an Excel file (`.csv`).\n\n"
            "**• `/premium`**\n"
            "└ Manage or discover the server's subscription.\n\n"
            "**🌟 Included Perks:**\n"
            "• 📊 **Analytics** : Weekly comparative report.\n"
            "• 🔔 **Reminders** : Auto PM to late agents before purge.\n"
            "• 🏷️ Auto `On Duty` role.\n"
            "• 🎨 Custom global bot color.\n"
            "• ⏰ Configurable auto-purge.\n"
            "• 🏥 Create unlimited Appointment reasons.\n"
            "• 🔕 No partner ads in Chronis."
        ),

        # --- GENERAL LOGS ---
        "log_start_title": "🟢 Service Start", "log_start_desc": "Agent {user} started their service.",
        "log_pause_title": "⏸️ Paused", "log_pause_desc": "Agent {user} went on pause.",
        "log_resume_title": "▶️ Service Resumed", "log_resume_desc": "Agent {user} resumed their service.",
        "log_stop_title": "🛑 Service End", "log_stop_desc": "Agent {user} finished their service.",
        
        "log_force_close_title": "🔧 Forced Close", 
        "log_force_close_desc": "{user}'s session was closed by {admin}.",
        
        "log_edit_time_title": "📈 Time Modified", 
        "log_edit_time_desc": "Manual modification by {admin}.",
        
        "log_reset_title": "⚠️ Total Reset", 
        "log_reset_desc": "Server reset by {admin}.",
        
        "log_cancel_title": "🗑️ Service Cancellation", 
        "log_cancel_desc": "Session cancelled by {admin} for {user}.",
        
        "log_remove_title": "👤 File Deleted", 
        "log_remove_desc": "{user}'s data deleted by {admin}.",
        
        "log_autorole_title": "🏆 Role Assigned", 
        "log_autorole_desc": "Roles given to {user} by {admin}.",
        
        "log_admin_pause_desc": "Forced pause by {admin}.",
        "log_admin_resume_desc": "Forced resume by {admin}.",
        
        "cancel_success": "🗑️ Session cancelled and deleted.",

        "log_maint_title": "🔄 Maintenance", "log_maint_desc": "Auto restart.",
        "log_bot_stop_title": "🛑 Bot Stop", "log_bot_stop_desc": "Manual stop.",
        "log_bot_start_title": "🟢 Bot Start", "log_bot_start_desc": "Bot online.",
        
        # --- ERRORS ---
        "error_generic": "❌ System error.", "error_perms": "⛔ Permission denied.", "error_admin_only": "⛔ Admin only.",
        "error_invalid_input": "❌ Invalid input.", "error_db": "⚠️ DB Error.", "error_no_role": "⚠️ No auto role.",
        "role_added": "✅ Role {role} added to {user}."
    }
}
