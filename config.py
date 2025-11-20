# Informations du bot
BOT_NAME = "Chronis"
BOT_COLOR = 0x00AFF4
BOT_VERSION = "2.7.0"
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
EMBED_FOOTER = f"Chronis V{BOT_VERSION} | By matteohooliga"

# Couleurs
COLOR_GREEN = 0x008000 
COLOR_BLUE = 0x3498DB
COLOR_ORANGE = 0xFF9d00
COLOR_RED = 0xF0000A
THRESHOLD_LOW = 5

# Boutons
BUTTONS = {
    "start": {"custom_id": "service_start", "emoji": "✨"},
    "pause": {"custom_id": "service_pause", "emoji": "🍎"},
    "stop": {"custom_id": "service_stop", "emoji": "🌙"}
}

# Traductions
TRANSLATIONS = {
    "fr": {
        # --- GENERAL ---
        "btn_invite": "Inviter le Bot", "btn_source": "Code Source", "btn_support": "Support",
        "btn_feedback": "Avis / Bug", "btn_refresh": "Actualiser",
        "btn_start": "Démarrer", "btn_pause": "Pause / Reprise", "btn_stop": "Fin de service",
        "btn_next": "Page Suivante >>", "btn_prev": "<< Page Précédente",

        # --- SETUP PANEL ---
        "setup_panel_title": "🛠️ Panneau de Configuration",
        "setup_panel_desc": "Configurez Chronis via les menus ci-dessous. Cliquez **Valider** lorsque vous avez terminé.",
        "setup_ph_lang": "🌍 Choisir la langue",
        "setup_ph_service": "📢 Salon Service (Actuel : {val})",
        "setup_ph_logs": "📜 Salon Logs (Actuel : {val})",
        "setup_ph_role": "👔 Rôle Direction (Actuel : {val})",
        "setup_ph_autorole": "🏆 Rôle Auto (Actuel : {val})",
        "setup_ph_goal": "🎯 Objectif Hebdo",
        "setup_btn_save": "Valider",
        "setup_err_no_service": "❌ Erreur : Salon Service requis !",
        "setup_success": "✅ **Sauvegardé !**\nPanneau envoyé dans {channel}.",
        "setup_complete": "✅ Config Terminée",
        "setup_logs": "\nLogs activés.",
        "log_setup_title": "✅ Logs Config",
        "log_setup_desc": "Ce salon recevra les logs.",
        "setup_role": "\nRôle Direction : {role}.",
        "setup_val_none": "Aucun",

        # --- SERVICE ---
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

        # --- STATS ---
        "stats_title": "📊 Statistiques de {name}",
        "stats_no_data": "Aucune donnée.",
        "global_title": "📊 Classement Global",
        "stats_fields": ["Sessions", "Temps total", "Moyenne", "Max", "Min"],
        "global_fields": ["Total Sessions", "Temps Cumulé", "Utilisateurs"],
        "goal_warning_title": "🚨 OBJECTIF NON ATTEINT",
        "goal_warning_desc": "Temps < Objectif ({goal}).",
        
        # --- DETAILS ---
        "det_title": "📄 Rapport Détaillé : {user}",
        "det_stats": "📊 Statistiques",
        "det_history": "📜 Historique Récent",
        "det_type_service": "🟢 Service",
        "det_type_adjust": "🔧 Ajustement Admin",

        # --- EDIT TIME ---
        "edit_success": "✅ Temps modifié pour {user}.",
        "edit_desc": "Le temps de service de {user} a été modifié manuellement.",
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

        # --- ADMIN PAUSE ---
        "admin_pause_success": "⏸️ Le service de {user} a été mis en pause par un administrateur.",
        "admin_resume_success": "▶️ Le service de {user} a été relancé par un administrateur.",
        "log_admin_pause_title": "⏸️ Pause Forcée",
        "log_admin_resume_title": "▶️ Reprise Forcée",

        # --- MAINTENANCE ---
        "maint_embed_title": "🚧 MAINTENANCE EN COURS",
        "maint_embed_desc": "Le système est temporairement verrouillé pour maintenance.\nLes prises de service sont impossibles.",
        "maint_enabled": "🟠 **Mode Maintenance ACTIVÉ**.\nL'embed a été mis à jour et les boutons sont bloqués.",
        "maint_disabled": "🟢 **Mode Maintenance DÉSACTIVÉ**.\nRetour à la normale.",
        "maint_block_msg": "⛔ **Maintenance** : Le système est verrouillé.",

        # --- LOGS ---
        "log_start_title": "🟢 Prise de Service", "log_start_desc": "L'agent {user} a pris son service.",
        "log_pause_title": "⏸️ Mise en Pause", "log_pause_desc": "L'agent {user} s'est mis en pause.",
        "log_resume_title": "▶️ Reprise de Service", "log_resume_desc": "L'agent {user} a repris son service.",
        "log_stop_title": "🛑 Fin de Service", "log_stop_desc": "L'agent {user} a terminé son service.",
        "log_force_close": "🔧 Fermeture Forcée", "log_edit_time": "📈 Temps Modifié",
        "log_reset": "⚠️ Reset Total", "log_cancel": "🗑️ Annulation", "log_remove": "👤 User Supprimé", 
        "log_autorole": "🏆 Rôle Auto", "log_maint_title": "🔄 Maintenance", "log_maint_desc": "Redémarrage auto.",
        "log_bot_stop_title": "🛑 Bot Stop", "log_bot_stop_desc": "Arrêt manuel.",
        "log_bot_start_title": "🟢 Bot Start", "log_bot_start_desc": "Bot en ligne.",
        
        # --- ADMIN COMMANDS ---
        "cmd_sync_start": "⏳ **Synchronisation en cours...**",
        "cmd_sync_end": "✅ **Synchronisation terminée !** ({count} commandes)",
        "cmd_restart_start": "👋 **Redémarrage en cours...**",
        "cmd_restart_end": "✅ **Redémarrage terminé !**",
        "log_sync_title": "🔄 Sync", "log_sync_desc": "Par {user}.",
        "log_restart_title": "🔄 Restart", "log_restart_desc": "Par {user}.",
        "log_stat_wip": "En cours...", "log_stat_done": "Terminé",
        "log_footer_done": "Fini le {date}",
        
        # --- FEEDBACK ---
        "feedback_modal_title": "Feedback", "feedback_subject": "Sujet", "feedback_label": "Message",
        "feedback_placeholder": "Détails...", "feedback_sent": "✅ Envoyé !", "feedback_error": "❌ Erreur.",
        "log_new_feedback": "📨 Feedback", "fb_select_placeholder": "Type...", "fb_opt_review": "Avis", "fb_opt_bug": "Bug",
        "fb_review_title": "Avis", "fb_review_subject": "Titre", "fb_review_rating": "Note (1-5)", "fb_review_comment": "Commentaire",
        "fb_log_review_title": "⭐ Avis Reçu", "fb_field_rating": "Note",
        "fb_bug_title": "Bug", "fb_bug_subject": "Titre", "fb_bug_desc": "Description", "fb_bug_media": "Lien image",
        "fb_log_bug_title": "🐛 Bug Reçu", "fb_field_media": "Preuve",

        # --- ABSENCE ---
        "abs_modal_title": "Déclarer une absence", 
        "abs_start_label": "Début", "abs_start_ph": "JJ/MM/AAAA",
        "abs_end_label": "Fin", "abs_end_ph": "JJ/MM/AAAA",
        "abs_reason_label": "Raison", "abs_reason_ph": "Motif...",
        "abs_embed_title": "📅 Absence de {user}", 
        "abs_field_dates": "Dates", "abs_field_duration": "Durée", "abs_field_reason": "Raison", 
        "abs_error_format": "❌ Date invalide.", "abs_error_logic": "❌ Fin < Début.",
        "abs_user_field": "👤 Agent",

        # --- HELP ---
        "help_title": "📚 Aide", "help_desc": "Choisir une catégorie.", "help_cat_user": "👤 Utilisateurs", "help_cat_admin": "🛡️ Administrateur",
        "help_back": "⬅️ Retour", "help_back_lang": "🌍 Langues",
        "help_user_desc": "Commandes publiques :", "help_admin_desc": "Commandes staff :",
        
        "help_cmds_user": (
            "**• `/sum`**\n└ Affiche vos statistiques personnelles.\n"
            "**• `/sumall`**\n└ Affiche le classement général du serveur.\n"
            "**• `/absence`**\n└ Formulaire pour déclarer une absence.\n"
            "**• `/feedback`**\n└ Envoyer un avis ou un bug.\n"
            "**• `/about`**\n└ Informations du bot."
        ),
        
        "help_cmds_admin": (
            "**• `/presence`**\n└ Liste instantanée des agents en service.\n"
            "**• `/details [joueur]`**\n└ Historique détaillé d'un agent.\n"
            "**• `/pause [joueur]`**\n└ Mettre en pause/reprendre un service.\n"
            "**• `/close [joueur]`**\n└ Forcer la fin de service d'un agent.\n"
            "**• `/edittime`**\n└ Corriger manuellement le temps.\n"
            "**• `/cancel [joueur]`**\n└ Annuler une session (suppression).\n"
            "**• `/remove_user`**\n└ Supprimer toutes les données d'un joueur.\n"
            "**• `/reset_server`**\n└ Réinitialisation (Hebdo/Mensuel).\n"
            "**• `/auto_role`**\n└ Attribuer les rôles auto.\n"
            "**• `/setup`**\n└ Panneau de configuration."
        ),
        
        # --- ERREURS ---
        "error_generic": "❌ Erreur système.", "error_perms": "⛔ Permission refusée.", "error_admin_only": "⛔ Admin seulement.",
        "error_invalid_input": "❌ Saisie invalide.", "error_db": "⚠️ Erreur DB.", "error_no_role": "⚠️ Pas de rôle auto.",
        "role_added": "✅ Rôle {role} ajouté à {user}."
    },
    "en": {
        # (Version EN)
        "btn_invite": "Invite", "btn_source": "Source", "btn_support": "Support", "btn_feedback": "Feedback", "btn_refresh": "Refresh",
        "btn_start": "Start", "btn_pause": "Pause", "btn_stop": "Stop", "btn_next": "Next >>", "btn_prev": "<< Prev",
        
        "setup_panel_title": "🛠️ Config", "setup_panel_desc": "Configure below.", "setup_ph_lang": "🌍 Language",
        "setup_ph_service": "📢 Service Channel", "setup_ph_logs": "📜 Logs Channel", "setup_ph_role": "👔 Direction Role",
        "setup_ph_goal": "🎯 Goal", "setup_ph_autorole": "🏆 Auto Role", "setup_btn_save": "Save",
        "setup_err_no_service": "❌ Service Channel required!", "setup_success": "✅ Saved!", "log_setup_title": "✅ Logs Config",
        "log_setup_desc": "Logs enabled.", "setup_complete": "✅ Setup Complete", "setup_logs": "\nLogs active.", "setup_role": "\nRole: {role}.", "setup_val_none": "None",
        
        "service_started": "✅ Started!", "service_already_started": "⚠️ Active!", "service_paused": "⏸️ Paused!",
        "service_resumed": "▶️ Resumed!", "service_not_started": "⚠️ Not started!", "service_stopped": "🛑 Ended!\nTotal: {duration}",
        "service_forced_stop": "🔧 Forced Stop.", "no_active_session": "❌ No session.",
        "embed_title": "🔍 Users on Duty", "embed_empty": "No users...", "embed_since": "• Since",

        "stats_title": "📊 Stats: {name}", "stats_no_data": "No data.", "global_title": "📊 Leaderboard",
        "stats_fields": ["Sessions", "Total", "Avg", "Max", "Min"], "global_fields": ["Sessions", "Total Time", "Users"],
        "goal_warning_title": "🚨 GOAL MISSED", "goal_warning_desc": "Under {goal}.",
        
        "det_title": "📄 Report: {user}", "det_stats": "📊 Stats", "det_history": "📜 History", "det_type_service": "🟢 Service",
        "det_type_adjust": "🔧 Adjustment",
        
        "edit_title": "⏱️ Time Edited", "edit_success": "✅ Edited for {user}.", "edit_desc": "Manual adjustment.",
        "edit_field_action": "Action", "edit_field_amount": "Amount", "edit_field_new_total": "New Total",
        "edit_field_old": "Old Total", "edit_field_admin": "Admin", "edit_field_target": "User",
        "time_added": "Added (+)", "time_removed": "Removed (-)",
        "et_view_title": "⏱️ Edit Time", "et_view_desc": "Choose action for {user}.", "et_btn_add": "Add (+)", "et_btn_remove": "Remove (-)",
        "et_modal_add": "Add Time", "et_modal_remove": "Remove Time", "et_label_hours": "Hours", "et_label_minutes": "Minutes", "et_label_seconds": "Seconds", "et_placeholder": "0",
        
        "admin_pause_success": "⏸️ Paused by admin.", "admin_resume_success": "▶️ Resumed by admin.", "log_admin_pause_title": "⏸️ Forced Pause", "log_admin_resume_title": "▶️ Forced Resume",

        "log_force_close": "🔧 Force Close", "log_edit_time": "📈 Time Edited", "log_reset": "⚠️ Reset", "log_cancel": "🗑️ Cancelled",
        "log_remove": "👤 User Deleted", "log_autorole": "🏆 Role Added", 
        "log_bot_stop_title": "🛑 Bot Stop", "log_bot_stop_desc": "Manual stop.", "log_bot_start_title": "🟢 Bot Start", "log_bot_start_desc": "Online.",
        "log_start_title": "🟢 Service Start", "log_start_desc": "Agent {user} started service.", "log_pause_title": "⏸️ Pause", "log_pause_desc": "Agent {user} paused.",
        "log_resume_title": "▶️ Resume", "log_resume_desc": "Agent {user} resumed.", "log_stop_title": "🛑 Service End", "log_stop_desc": "Agent {user} ended service.",
        "log_maint_title": "🔄 Maintenance", "log_maint_desc": "Auto restart.",
        "maint_embed_title": "🚧 MAINTENANCE", "maint_embed_desc": "System locked.", "maint_enabled": "🟠 **Maintenance ON**.", "maint_disabled": "🟢 **Maintenance OFF**.", "maint_block_msg": "⛔ **Maintenance** : Locked.",

        "cmd_sync_start": "⏳ Syncing...", "cmd_sync_end": "✅ Synced.", "cmd_restart_start": "👋 Restarting...", "cmd_restart_end": "✅ Online.",
        "log_sync_title": "🔄 Sync", "log_restart_title": "🔄 Restart", "log_sync_desc": "By {user}.", "log_restart_desc": "By {user}.",
        "log_stat_wip": "WIP...", "log_stat_done": "Done", "log_footer_done": "Done at {date}",

        "feedback_modal_title": "Feedback", "feedback_subject": "Subject", "feedback_label": "Details", "feedback_placeholder": "...",
        "feedback_sent": "✅ Sent!", "feedback_error": "❌ Error.", "log_new_feedback": "📨 Feedback", "fb_select_placeholder": "Type...",
        "fb_opt_review": "Review", "fb_opt_bug": "Bug", "fb_review_title": "Review", "fb_bug_title": "Bug",
        "fb_field_rating": "Rating", "fb_field_media": "Proof",
        
        "abs_modal_title": "Absence", "abs_start_label": "Start", "abs_end_label": "End", "abs_reason_label": "Reason",
        "abs_start_ph": "DD/MM/YYYY", "abs_end_ph": "DD/MM/YYYY", "abs_reason_ph": "Reason...",
        "abs_embed_title": "📅 Absence: {user}", "abs_field_dates": "Dates", "abs_field_duration": "Duration", "abs_field_reason": "Reason",
        "abs_error_format": "❌ Bad Date.", "abs_error_logic": "❌ End < Start.", "abs_user_field": "👤 Agent",

        "help_title": "📚 Help", "help_desc": "Select category.", "help_cat_user": "👤 Users", "help_cat_admin": "🛡️ Administrator",
        "help_back": "⬅️ Back", "help_back_lang": "🌍 Language",
        
        "help_user_desc": "**Public:**", 
        "help_cmds_user": (
            "• `/sum`\n  └ Stats.\n"
            "• `/sumall`\n  └ Leaderboard.\n"
            "• `/about`\n  └ Info.\n"
            "• `/feedback`\n  └ Report.\n"
            "• `/absence`\n  └ Absence."
        ),
        
        "help_admin_desc": "**Staff:**",
        "help_cmds_admin": (
            "• `/presence`\n  └ Live list.\n"
            "• `/details`\n  └ History.\n"
            "• `/close`\n  └ Force close.\n"
            "• `/edittime`\n  └ Edit time.\n"
            "• `/cancel`\n  └ Cancel session.\n"
            "• `/remove_user`\n  └ Delete user.\n"
            "• `/reset_server`\n  └ Reset.\n"
            "• `/setup`\n  └ Config.\n"
            "• `/auto_role`\n  └ Auto Role.\n"
            "• `/pause`\n  └ Force pause."
        ),
        
        "error_generic": "❌ Error.", "error_perms": "⛔ Denied.", "error_admin_only": "⛔ Admin only.", "error_invalid_input": "❌ Invalid.",
        "error_db": "⚠️ DB Error.", "error_no_role": "⚠️ No role.", "role_added": "✅ Role added."
    }
}

DATABASE_NAME = "chronos.db"