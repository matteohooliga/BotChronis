# Informations du bot
BOT_NAME = "Chronis"
BOT_COLOR = 0x00AFF4
BOT_VERSION = "2.5.2"
OWNER_ID = "820572214750871573"

# --- CONFIGURATION FEEDBACK ---
DEV_FEEDBACK_CHANNEL_ID = 1441031492061892670
DEV_FEEDBACK_ROLE_ID = 1106286037568860311

# Liens
GITHUB_LINK = "https://github.com/matteohooliga/BotChronis"
SUPPORT_LINK = "" 

# Configuration des embeds
EMBED_TITLE = "🔍 Utilisateur(s) en service"
EMBED_DESCRIPTION_EMPTY = "Aucun utilisateur n'est en service… 😢"
EMBED_SINCE = "• Depuis"
# FOOTER UNIFIÉ
EMBED_FOOTER = f"Chronis V{BOT_VERSION} | By matteohooliga"

# Boutons
BUTTONS = {
    "start": {"custom_id": "service_start", "emoji": "✨"},
    "pause": {"custom_id": "service_pause", "emoji": "🍎"},
    "stop": {"custom_id": "service_stop", "emoji": "🌙"}
}

# Traductions
TRANSLATIONS = {
    "fr": {
        # Boutons Généraux
        "btn_invite": "Inviter le Bot", "btn_source": "Code Source", "btn_support": "Support",
        "btn_feedback": "Avis / Bug", "btn_refresh": "Actualiser",
        
        # Boutons Service
        "btn_start": "Démarrer", "btn_pause": "Pause / Reprise", "btn_stop": "Fin de service",
        
        # SETUP PANEL
        "setup_panel_title": "🛠️ Panneau de Configuration",
        "setup_panel_desc": "Utilisez les menus ci-dessous pour configurer Chronis.\nUne fois vos choix faits, cliquez sur **Valider**.",
        "setup_ph_lang": "🌍 Choisir la langue",
        "setup_ph_service": "📢 Choisir Salon Service",
        "setup_ph_logs": "📜 Choisir Salon Logs",
        "setup_ph_role": "👔 Choisir Rôle Direction",
        "setup_btn_save": "Valider la configuration",
        "setup_err_no_service": "❌ Erreur : Vous devez sélectionner un salon pour le Service !",
        "setup_success": "✅ **Configuration sauvegardée !**\nLe panneau a été envoyé dans {channel}.",
        "setup_complete": "✅ **Configuration terminée**",
        "setup_logs": "\nLogs configurés dans {channel}.",
        "log_setup_title": "✅ Configuration des Logs",
        "log_setup_desc": "Ce salon recevra les logs du bot Chronis.",
        "setup_role": "\nRôle Direction configuré : {role}.",

        # Messages Service
        "service_started": "✅ **Service démarré** !",
        "service_already_started": "⚠️ Vous êtes déjà en service !",
        "service_paused": "⏸️ **Pause démarrée** !",
        "service_resumed": "▶️ **Service repris** !",
        "service_not_started": "⚠️ Vous devez d'abord démarrer votre service !",
        "service_stopped": "🛑 **Service terminé** !\n\n**Total** : {duration}\n**Pause** : {pause}\n**Effectif** : {effective}",
        "service_forced_stop": "🔧 **Fermeture forcée** pour {user}.\n**Durée** : {duration}",
        "no_active_session": "❌ Aucune session active.",
        "embed_title": "🔍 Utilisateur(s) en service",
        "embed_empty": "Aucun utilisateur n'est en service… 😢",
        "embed_since": "• Depuis",

        # Stats
        "stats_title": "📊 Statistiques de {name}",
        "stats_no_data": "Aucune donnée.",
        "global_title": "📊 Statistiques Globales – {guild}",
        "stats_fields": ["Sessions", "Temps total", "Moyenne", "Max", "Min"],
        "global_fields": ["Total sessions", "Temps cumulé", "Utilisateurs"],

        # Logs Titres
        "log_force_close": "🔧 Service Fermé (Force)",
        "log_edit_time": "📈 Temps Modifié",
        "log_reset": "⚠️ Réinitialisation Totale",
        "log_cancel": "🗑️ Service Annulé",
        "log_remove": "👤 Utilisateur Supprimé",
        "log_maint_title": "🔄 Maintenance Quotidienne",
        "log_maint_desc": "Redémarrage automatique.",
        
        # Actions / Edit Time
        "time_added": "ajouté", "time_removed": "retiré", "new_total": "Nouveau total",
        "edit_success": "✅ Temps modifié pour {user}.\n**{action}** : {value}\n**Nouveau Total** : {new_total}",
        
        # Feedback
        "feedback_modal_title": "Envoyer un Feedback",
        "feedback_subject": "Sujet / Bug",
        "feedback_label": "Détails",
        "feedback_placeholder": "Expliquez votre idée ou le bug...",
        "feedback_sent": "✅ Merci ! Retour transmis.",
        "feedback_error": "❌ Erreur envoi feedback.",
        "log_new_feedback": "📨 Nouveau Feedback",
        "fb_select_placeholder": "Type de retour...",
        "fb_opt_review": "Avis ⭐", "fb_opt_bug": "Bug 🐛",
        "fb_review_title": "⭐ Laisser un avis", "fb_review_subject": "Titre", "fb_review_rating": "Note (1-5)", "fb_review_comment": "Commentaire", "fb_log_review_title": "⭐ Avis Reçu", "fb_field_rating": "Note",
        "fb_bug_title": "🐛 Signaler un Bug", "fb_bug_subject": "Titre", "fb_bug_desc": "Description", "fb_bug_media": "Lien image (Optionnel)", "fb_log_bug_title": "🐛 Bug Reçu", "fb_field_media": "Preuve",

        # Absence
        "abs_modal_title": "Déclarer une absence",
        "abs_start_label": "Début (JJ/MM/AAAA)",
        "abs_end_label": "Fin (JJ/MM/AAAA)",
        "abs_reason_label": "Raison",
        "abs_embed_title": "📅 Absence de {user}",
        "abs_field_dates": "Dates", "abs_field_duration": "Durée", "abs_field_reason": "Raison",
        "abs_error_format": "❌ Date invalide (JJ/MM/AAAA).",
        "abs_error_logic": "❌ Fin avant début.",

        # Help
        "help_title": "📚 Menu d'Aide",
        "help_desc": "Sélectionnez une catégorie.",
        "help_cat_user": "👤 Utilisateur", "help_cat_admin": "🛡️ Admin", "help_back": "⬅️ Retour", "help_back_lang": "🌍 Langues",
        "help_user_desc": "**Pour tous :**", "help_admin_desc": "**Pour le staff :**",
        "help_cmds_user": "• `/sum` : Stats perso.\n• `/sumall` : Classement.\n• `/about` : Infos.\n• `/feedback` : Avis/Bug.\n• `/absence` : Absence.",
        "help_cmds_admin": "• `/presence` : Liste agents.\n• `/details` : Historique.\n• `/close` : Fin forcée.\n• `/edittime` : Modif temps.\n• `/cancel` : Annuler.\n• `/remove_user` : Suppr user.\n• `/reset_server` : Reset.\n• `/setup` : Configurer.",

        # System Logs (NEW for +start/+stop)
        "cmd_restart_end": "✅ **Redémarrage terminé !**",
        "log_stat_done": "Terminé ✅",
        "log_footer_done": "Fini le {date}",
        
        "log_bot_stop_title": "🛑 Arrêt du Bot",
        "log_bot_stop_desc": "Le bot a été éteint manuellement par un administrateur.",
        "log_bot_start_title": "🟢 Démarrage du Bot",
        "log_bot_start_desc": "Le bot est de nouveau en ligne.",
        
        "cmd_sync_start": "⏳ **Synchronisation en cours...**",
        "cmd_sync_end": "✅ **Synchronisation terminée !** ({count} commandes)",
        "log_sync_title": "🔄 Synchronisation Commandes",
        "log_sync_desc": "Mise à jour effectuée par {user}.",
        "cmd_restart_start": "👋 **Redémarrage en cours...**",
        "log_restart_title": "🔄 Redémarrage Manuel",
        "log_restart_desc": "Déclenché par {user}.",
        "log_stat_wip": "En cours... ⏳"
    },
    "en": {
        "btn_invite": "Invite Bot", "btn_source": "Source Code", "btn_support": "Support",
        "btn_feedback": "Feedback", "btn_refresh": "Refresh",
        "btn_start": "Start Service", "btn_pause": "Pause / Resume", "btn_stop": "End Service",
        
        "setup_panel_title": "🛠️ Configuration Panel",
        "setup_panel_desc": "Use menus below to configure Chronis.\nClick **Validate** when done.",
        "setup_ph_lang": "🌍 Select Language",
        "setup_ph_service": "📢 Select Service Channel",
        "setup_ph_logs": "📜 Select Logs Channel",
        "setup_ph_role": "👔 Select Direction Role",
        "setup_btn_save": "Save Configuration",
        "setup_err_no_service": "❌ Error: Service Channel is required!",
        "setup_success": "✅ **Configuration saved!**\nPanel sent to {channel}.",
        "setup_complete": "✅ **Setup complete**",
        "setup_logs": "\nLogs enabled in {channel}.",
        "log_setup_title": "✅ Logs Configured",
        "log_setup_desc": "This channel will receive logs.",
        "setup_role": "\nDirection role: {role}.",

        "service_started": "✅ **Service started** !",
        "service_already_started": "⚠️ You are already on duty!",
        "service_paused": "⏸️ **Paused** !",
        "service_resumed": "▶️ **Resumed** !",
        "service_not_started": "⚠️ You must start service first!",
        "service_stopped": "🛑 **Service ended** !\n\n**Total** : {duration}\n**Pause** : {pause}\n**Effective** : {effective}",
        "service_forced_stop": "🔧 **Force closed by admin** for {user}.\n**Duration** : {duration}",
        "no_active_session": "❌ No active session.",

        "embed_title": "🔍 Users on Duty",
        "embed_empty": "No users on duty… 😢",
        "embed_since": "• Since",

        "stats_title": "📊 Statistics for {name}",
        "stats_no_data": "No data.",
        "global_title": "📊 Global Stats – {guild}",
        "stats_fields": ["Sessions", "Total Time", "Average", "Max", "Min"],
        "global_fields": ["Total Sessions", "Cumulative Time", "Users"],

        "log_force_close": "🔧 Force Close",
        "log_edit_time": "📈 Time Edited",
        "log_reset": "⚠️ Total Reset",
        "log_cancel": "🗑️ Cancelled",
        "log_remove": "👤 User Deleted",
        "log_maint_title": "🔄 Daily Maintenance",
        "log_maint_desc": "Auto restart.",

        "time_added": "added", "time_removed": "removed", "new_total": "New Total",
        "edit_success": "✅ Edited for {user}.\n**{action}** : {value}\n**New Total** : {new_total}",
        
        "feedback_modal_title": "Send Feedback",
        "feedback_subject": "Subject / Bug",
        "feedback_label": "Details",
        "feedback_placeholder": "Explain...",
        "feedback_sent": "✅ Sent!",
        "feedback_error": "❌ Error sending.",
        "log_new_feedback": "📨 New Feedback",
        "fb_select_placeholder": "Select type...",
        "fb_opt_review": "Review ⭐", "fb_opt_bug": "Bug 🐛",
        "fb_review_title": "⭐ Review", "fb_review_subject": "Title", "fb_review_rating": "Rating", "fb_review_comment": "Comment", "fb_log_review_title": "⭐ New Review", "fb_field_rating": "Rating",
        "fb_bug_title": "🐛 Bug Report", "fb_bug_subject": "Title", "fb_bug_desc": "Description", "fb_bug_media": "Image Link", "fb_log_bug_title": "🐛 Bug Report", "fb_field_media": "Proof",

        "abs_modal_title": "Declare Absence",
        "abs_start_label": "Start (DD/MM/YYYY)",
        "abs_end_label": "End (DD/MM/YYYY)",
        "abs_reason_label": "Reason",
        "abs_embed_title": "📅 Absence: {user}",
        "abs_field_dates": "Dates", "abs_field_duration": "Duration", "abs_field_reason": "Reason",
        "abs_error_format": "❌ Invalid date.",
        "abs_error_logic": "❌ End before Start.",

        "help_title": "📚 Help Menu",
        "help_desc": "Select a category.",
        "help_cat_user": "👤 User", "help_cat_admin": "🛡️ Admin", "help_back": "⬅️ Back", "help_back_lang": "🌍 Languages",
        "help_user_desc": "**For everyone:**", "help_admin_desc": "**For staff:**",
        "help_cmds_user": "• `/sum` : Stats.\n• `/sumall` : Leaderboard.\n• `/about` : Info.\n• `/feedback` : Feedback.\n• `/absence` : Absence.",
        "help_cmds_admin": "• `/presence` : List.\n• `/details` : History.\n• `/close` : Force close.\n• `/edittime` : Edit time.\n• `/cancel` : Cancel.\n• `/remove_user` : Delete user.\n• `/reset_server` : Reset.\n• `/setup` : Config.",

        "cmd_restart_end": "✅ **Restart complete!**",
        "log_stat_done": "Done ✅",
        "log_footer_done": "Finished on {date}",

        "log_bot_stop_title": "🛑 Bot Stopped",
        "log_bot_stop_desc": "Bot was manually shut down by an administrator.",
        "log_bot_start_title": "🟢 Bot Started",
        "log_bot_start_desc": "Bot is back online.",
        
        "cmd_sync_start": "⏳ **Sync in progress...**",
        "cmd_sync_end": "✅ **Sync complete!** ({count} commands)",
        "log_sync_title": "🔄 Commands Sync",
        "log_sync_desc": "Update triggered by {user}.",
        "cmd_restart_start": "👋 **Restarting...**",
        "log_restart_title": "🔄 Manual Restart",
        "log_restart_desc": "Triggered by {user}.",
        "log_stat_wip": "In progress... ⏳"
    }
}

DATABASE_NAME = "chronos.db"