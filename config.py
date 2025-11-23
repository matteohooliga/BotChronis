# ==============================================================================
#                            FICHIER DE CONFIGURATION
# ==============================================================================

# Informations du bot
BOT_NAME = "Chronis"
BOT_COLOR = 0x6100bd  # VIOLET (Couleur principale)
BOT_VERSION = "2.10.1"
OWNER_ID = "820572214750871573"

# --- CONFIGURATION FEEDBACK & LOGS ---
# Salon où VOUS recevez les feedbacks (Avis/Bugs)
DEV_FEEDBACK_CHANNEL_ID = 1441031492061892670
# Rôle à mentionner lors d'un feedback
DEV_FEEDBACK_ROLE_ID = 1106286037568860311
# Salon où VOUS recevez les logs techniques (+stop, +restart...)
DEV_LOG_CHANNEL_ID = 1441382041831739526

# Liens
GITHUB_LINK = "https://github.com/matteohooliga/BotChronis"
SUPPORT_LINK = "" 

# Configuration des embeds
EMBED_TITLE = "🔍 Utilisateur(s) en service"
EMBED_DESCRIPTION_EMPTY = "Aucun utilisateur n'est en service… 😢"
EMBED_SINCE = "• Depuis"
EMBED_FOOTER = f"Chronis V{BOT_VERSION} | By matteohooliga"

# --- COULEURS DYNAMIQUES ---
COLOR_GREEN = 0x00FF00     # Vert (Activité normale > 5 personnes)
COLOR_ORANGE = 0xF39C12    # Orange (Maintenance / Activité faible)
COLOR_RED = 0xFF0000       # Rouge (Vide / Erreur / Arrêt)
COLOR_PURPLE = 0x6100bd    # Violet (Couleur par défaut)
COLOR_DARK_BLUE = 0x00008B # Bleu Foncé (PAUSE)

# Alias pour le code (Pause pointe vers Bleu Foncé)
COLOR_BLUE = COLOR_DARK_BLUE 

# Seuil pour passer l'embed en vert (5 personnes ou plus)
THRESHOLD_LOW = 5

# Boutons (IDs fixes pour le code)
BUTTONS = {
    "start": {"custom_id": "service_start", "emoji": "✨"},
    "pause": {"custom_id": "service_pause", "emoji": "🍎"},
    "stop": {"custom_id": "service_stop", "emoji": "🌙"}
}

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

        # --- PANNEAU SETUP (/setup) ---
        "setup_panel_title": "🛠️ Panneau de Configuration",
        "setup_panel_desc": "Configurez Chronis via les menus ci-dessous. Cliquez **Valider** lorsque vous avez terminé.",
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
        "det_history": "📜 Historique Récent",
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

        # --- ADMIN PAUSE ---
        "admin_pause_success": "⏸️ Le service de {user} a été mis en pause par un administrateur.",
        "admin_resume_success": "▶️ Le service de {user} a été relancé par un administrateur.",
        "log_admin_pause_title": "⏸️ Pause Forcée",
        "log_admin_resume_title": "▶️ Reprise Forcée",
        "paused_list_title": "⏸️ Agents en Pause", 
        "paused_list_empty": "✅ Aucun agent n'est actuellement en pause.",

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
        
        # --- ADMIN COMMANDS (+) ---
        "cmd_sync_start": "⏳ **Synchronisation en cours...**",
        "cmd_sync_end": "✅ **Synchronisation terminée !** ({count} commandes)",
        "cmd_restart_start": "👋 **Redémarrage en cours...**",
        "cmd_restart_end": "✅ **Redémarrage terminé !**",
        "log_sync_title": "🔄 Sync", "log_sync_desc": "Par {user}.",
        "log_restart_title": "🔄 Restart", "log_restart_desc": "Par {user}.",
        "log_stat_wip": "En cours...", "log_stat_done": "Terminé",
        "log_footer_done": "Fini le {date}",
        
        # --- FEEDBACK ---
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

        # --- ABSENCE ---
        "abs_modal_title": "Déclarer une absence", 
        "abs_start_label": "Début", "abs_start_ph": "JJ/MM/AAAA",
        "abs_end_label": "Fin", "abs_end_ph": "JJ/MM/AAAA",
        "abs_reason_label": "Raison", "abs_reason_ph": "Motif...",
        "abs_embed_title": "📅 Absence de {user}", 
        "abs_field_dates": "Dates", "abs_field_duration": "Durée", "abs_field_reason": "Raison", 
        "abs_error_format": "❌ Date invalide.", "abs_error_logic": "❌ Fin < Début.",
        "abs_user_field": "👤 Agent",

        # --- INFO AUTOMATIQUE ---
        "about_maint_title": "🔄 Maintenance Automatique",
        "about_maint_desc": "🕒 **04h00** : Redémarrage journalier.\n⚠️ Tous les services actifs sont fermés automatiquement.",

        # --- SERVER STATS (Statistiques Avancées) ---
        "srv_stats_title": "📈 Audit d'Activité Serveur",
        "srv_stats_desc": "Analyse sur une période de **{days}** jours actifs.",
        "srv_field_global": "🌍 Données Globales",
        "srv_val_total_time": "• Temps Cumulé : `{val}`",
        "srv_val_sessions": "• Sessions Totales : `{val}`",
        "srv_field_daily": "📅 Moyennes Journalières",
        "srv_val_people_day": "• Effectif Moyen : `{val} agents/jour`",
        "srv_val_time_day": "• Temps Moyen : `{val}/agent/jour`",
        "srv_field_weekly": "🗓️ Moyennes Hebdomadaires",
        "srv_val_time_week": "• Temps Moyen : `{val}/agent/semaine`",

        # --- HELP DÉTAILLÉ FR ---
        "help_title": "📚 Aide", "help_desc": "Choisir une catégorie.",
        "help_cat_user": "Utilisateurs", "help_cat_admin": "Administrateur",
        "help_back": "Retour", "help_back_lang": "Langues",
        "help_user_desc": "Commandes publiques :", "help_admin_desc": "Commandes staff :",
        
        "help_cmds_user": (
            "**• `/sum`**\n"
            "└ Affiche vos statistiques personnelles (Temps total, moyenne).\n\n"
            "**• `/sumall`**\n"
            "└ Affiche le classement général du serveur.\n\n"
            "**• `/absence`**\n"
            "└ Formulaire pour déclarer une absence officielle.\n\n"
            "**• `/feedback`**\n"
            "└ Envoyer une suggestion ou signaler un bug au développeur.\n\n"
            "**• `/about`**\n"
            "└ Informations techniques du bot.\n\n"
            "**• `/help`**\n"
            "└ Affiche ce menu d'aide."
        ),
        
        "help_cmds_admin": (
            "**• `/presence [salon]`**\n"
            "└ Liste instantanée des agents en service.\n"
            "└ Si un salon est précisé : Recensement des réactions.\n\n"
            "**• `/pauselist`**\n"
            "└ Affiche la liste spécifique des agents en pause.\n\n"
            "**• `/details [joueur]`**\n"
            "└ Historique détaillé des 10 dernières sessions.\n\n"
            "**• `/close [joueur]`**\n"
            "└ Forcer la fin de service d'un agent.\n\n"
            "**• `/pause [joueur]`**\n"
            "└ Forcer la mise en pause d'un agent.\n\n"
            "**• `/edittime`**\n"
            "└ Corriger manuellement le temps (Ajout/Retrait).\n\n"
            "**• `/cancel [joueur]`**\n"
            "└ Annuler une session en cours sans sauvegarde.\n\n"
            "**• `/remove_user`**\n"
            "└ Supprimer définitivement le dossier d'un agent.\n\n"
            "**• `/reset_server`**\n"
            "└ Réinitialisation globale des stats (Hebdo/Mensuel).\n\n"
            "**• `/auto_role`**\n"
            "└ Attribuer les rôles configurés.\n\n"
            "**• `/setup`**\n"
            "└ Panneau de configuration générale."
        ),
        
        # --- ERREURS ---
        "error_generic": "❌ Erreur système.", "error_perms": "⛔ Permission refusée.", "error_admin_only": "⛔ Admin seulement.",
        "error_invalid_input": "❌ Saisie invalide.", "error_db": "⚠️ Erreur DB.", "error_no_role": "⚠️ Pas de rôle auto.",
        "role_added": "✅ Rôle {role} ajouté à {user}."
    },
    "en": {
        # --- GENERAL ---
        "btn_invite": "Invite", "btn_source": "Source", "btn_support": "Support", "btn_feedback": "Feedback", "btn_refresh": "Refresh",
        "btn_start": "Start", "btn_pause": "Pause", "btn_stop": "Stop", "btn_next": "Next >>", "btn_prev": "<< Prev",
        
        # --- SETUP ---
        "setup_panel_title": "🛠️ Config Panel",
        "setup_panel_desc": "Configure below. Click **Validate** when done.",
        "setup_ph_lang": "🌍 Language",
        "setup_ph_service": "📢 Service Channel", "setup_ph_logs": "📜 Logs Channel", "setup_ph_role": "👔 Direction Role",
        "setup_ph_goal": "🎯 Goal", "setup_ph_autorole": "🏆 Auto Role", "setup_btn_save": "Save",
        "setup_err_no_service": "❌ Error: Service Channel required!", "setup_success": "✅ **Saved!**\nPanel sent to {channel}.",
        "log_setup_title": "✅ Config Saved", "log_setup_desc": "Logs enabled.", "setup_complete": "✅ Complete",
        "setup_logs": "\nLogs active.", "setup_role": "\nRole: {role}.", "setup_val_none": "None",
        
        # --- SERVICE ---
        "service_started": "✅ **Service started!**",
        "service_already_started": "⚠️ You are already on duty!",
        "service_paused": "⏸️ **Paused!**",
        "service_resumed": "▶️ **Resumed!**",
        "service_not_started": "⚠️ You must start service first!",
        "service_stopped": "🛑 **Ended!**\n\n**Total**: {duration}\n**Pause**: {pause}\n**Effective**: {effective}",
        "service_forced_stop": "🔧 **Force closed** for {user}.\n**Duration**: {duration}",
        "no_active_session": "❌ No active session.",
        "embed_title": "🔍 Users on Duty", "embed_empty": "No users on duty... 😢", "embed_since": "• Since",

        # --- STATS ---
        "stats_title": "📊 Statistics: {name}", "stats_no_data": "No data found.", "global_title": "📊 Global Leaderboard",
        "stats_fields": ["Sessions", "Total", "Avg", "Max", "Min"], "global_fields": ["Total Sessions", "Cumulative Time", "Users"],
        "goal_warning_title": "🚨 GOAL MISSED", "goal_warning_desc": "Warning: Time is under target ({goal}).",
        
        # --- DETAILS ---
        "det_title": "📄 Report: {user}", "det_stats": "📊 Statistics", "det_history": "📜 Recent History",
        "det_type_service": "🟢 Service", "det_type_adjust": "🔧 Adjustment",
        
        # --- EDIT TIME ---
        "edit_title": "⏱️ Time Edited", "edit_success": "✅ Edited for {user}.", "edit_desc": "Manual time adjustment.",
        "edit_field_action": "Action", "edit_field_amount": "Amount", "edit_field_new_total": "New Total",
        "edit_field_old": "Old Total", "edit_field_admin": "Admin", "edit_field_target": "User",
        "time_added": "Added", "time_removed": "Removed",
        "et_view_title": "⏱️ Edit Time", "et_view_desc": "Choose action for {user}.", "et_btn_add": "Add", "et_btn_remove": "Remove",
        "et_modal_add": "Add Time", "et_modal_remove": "Remove Time", "et_label_hours": "Hours", "et_label_minutes": "Minutes",
        "et_label_seconds": "Seconds", "et_placeholder": "0",

        # --- ADMIN PAUSE ---
        "admin_pause_success": "⏸️ Service of {user} paused by admin.",
        "admin_resume_success": "▶️ Service of {user} resumed by admin.",
        "log_admin_pause_title": "⏸️ Forced Pause", "log_admin_resume_title": "▶️ Forced Resume",
        "cancel_success": "🗑️ Session cancelled and deleted.",
        "paused_list_title": "⏸️ Paused Agents", "paused_list_empty": "✅ No one is paused.",

        # --- LOGS ---
        "log_start_title": "🟢 Service Start", "log_start_desc": "Agent {user} started service.",
        "log_pause_title": "⏸️ Pause", "log_pause_desc": "Agent {user} paused.",
        "log_resume_title": "▶️ Resume", "log_resume_desc": "Agent {user} resumed.",
        "log_stop_title": "🛑 Service End", "log_stop_desc": "Agent {user} ended service.",
        
        "log_force_close_title": "🔧 Force Close", "log_force_close_desc": "Session closed by {admin} for {user}.",
        "log_edit_time_title": "📈 Time Edited", "log_edit_time_desc": "Manual edit by {admin}.",
        "log_reset_title": "⚠️ Reset", "log_reset_desc": "Server reset by {admin}.",
        "log_cancel_title": "🗑️ Cancelled", "log_cancel_desc": "Session cancelled by {admin} for {user}.",
        "log_remove_title": "👤 Deleted", "log_remove_desc": "Data for {user} deleted by {admin}.",
        "log_autorole_title": "🏆 Role Added", "log_autorole_desc": "Roles given to {user} by {admin}.",
        "log_admin_pause_desc": "Paused by {admin}.", "log_admin_resume_desc": "Resumed by {admin}.",

        "log_maint_title": "🔄 Maintenance", "log_maint_desc": "Auto restart.",
        "log_bot_stop_title": "🛑 Bot Stop", "log_bot_stop_desc": "Manual stop.",
        "log_bot_start_title": "🟢 Bot Start", "log_bot_start_desc": "Bot online.",
        
        # --- ADMIN CMD ---
        "cmd_sync_start": "⏳ Syncing...", "cmd_sync_end": "✅ Synced ({count} cmds).",
        "cmd_restart_start": "👋 Restarting...", "cmd_restart_end": "✅ Online.",
        "log_sync_title": "🔄 Sync", "log_restart_title": "🔄 Restart", "log_sync_desc": "By {user}.",
        "log_restart_desc": "By {user}.", "log_stat_wip": "WIP...", "log_stat_done": "Done", "log_footer_done": "Done at {date}",

        # --- MAINTENANCE ---
        "maint_embed_title": "🚧 MAINTENANCE", "maint_embed_desc": "System locked.",
        "maint_enabled": "🟠 **Maintenance ON**.", "maint_disabled": "🟢 **Maintenance OFF**.",
        "maint_block_msg": "⛔ **Maintenance** : Locked.",

        # --- MISC LOGS ---
        "log_guild_join_title": "➕ New Guild", "log_guild_join_desc": "Bot added.", "log_guild_join_name": "Name", "log_guild_join_id": "ID",
        "log_guild_join_owner": "Owner", "log_guild_join_members": "Members",
        "bl_add_success": "⛔ **{user}** Blacklisted.", "bl_remove_success": "✅ **{user}** Unblacklisted.",
        "bl_already": "⚠️ Already listed.", "bl_not_found": "⚠️ Not found.", "bl_error": "⛔ **Access Denied**.",
        "infos_title": "📊 Infos", "infos_desc": "On **{count}** guilds.",
        
        # --- PRESENCE ---
        "pres_react_title": "📊 Census", "pres_react_desc": "Reactions in {channel}.", "pres_react_empty": "⚠️ None.",
        "error_no_message": "❌ No message.", "error_channel_type": "❌ Not text channel.",

        # --- MODALS ---
        "feedback_modal_title": "Feedback", "feedback_subject": "Subject", "feedback_label": "Details",
        "feedback_placeholder": "...", "feedback_sent": "✅ Sent!", "feedback_error": "❌ Error.",
        "log_new_feedback": "📨 Feedback", "fb_select_placeholder": "Type...", "fb_opt_review": "Review", "fb_opt_bug": "Bug",
        "fb_review_title": "Review", "fb_bug_title": "Bug", "fb_field_rating": "Rating", "fb_field_media": "Proof",
        
        "abs_modal_title": "Absence", "abs_start_label": "Start", "abs_end_label": "End", "abs_reason_label": "Reason",
        "abs_start_ph": "DD/MM/YYYY", "abs_end_ph": "DD/MM/YYYY", "abs_reason_ph": "...", "abs_embed_title": "📅 Absence",
        "abs_field_dates": "Dates", "abs_field_duration": "Duration", "abs_field_reason": "Reason",
        "abs_error_format": "❌ Bad Date.", "abs_error_logic": "❌ End < Start.", "abs_user_field": "👤 Agent",

        # --- SERVER STATS ---
        "srv_stats_title": "📈 Server Activity Audit",
        "srv_stats_desc": "Analysis over **{days}** active days.",
        "srv_field_global": "🌍 Global Data",
        "srv_val_total_time": "• Total Time: `{val}`",
        "srv_val_sessions": "• Total Sessions: `{val}`",
        "srv_field_daily": "📅 Daily Averages",
        "srv_val_people_day": "• Avg Staff: `{val} agents/day`",
        "srv_val_time_day": "• Avg Time: `{val}/agent/day`",
        "srv_field_weekly": "🗓️ Weekly Averages",
        "srv_val_time_week": "• Avg Time: `{val}/agent/week`",

        # --- INFO ---
        "about_maint_title": "🔄 Auto Maintenance",
        "about_maint_desc": "🕒 **04:00 AM**: Daily restart.\n⚠️ All active sessions are closed automatically.",

        # --- HELP DETAILED (EN) ---
        "help_title": "📚 Help", "help_desc": "Select category.", "help_cat_user": "Users", "help_cat_admin": "Admin", "help_back": "Back", "help_back_lang": "Language",
        
        "help_user_desc": "**Public Commands:**", 
        "help_cmds_user": (
            "**• `/sum`**\n"
            "└ Displays your personal statistics.\n\n"
            "**• `/sumall`**\n"
            "└ Displays the server leaderboard.\n\n"
            "**• `/absence`**\n"
            "└ Form to declare an absence.\n\n"
            "**• `/feedback`**\n"
            "└ Send a suggestion or report a bug.\n\n"
            "**• `/about`**\n"
            "└ Bot information.\n\n"
            "**• `/help`**\n"
            "└ Shows this help menu."
        ),
        
        "help_admin_desc": "**Staff Commands:**",
        "help_cmds_admin": (
            "**• `/presence [channel]`**\n"
            "└ Live list of agents (or reaction census).\n\n"
            "**• `/pauselist`**\n"
            "└ List of paused agents.\n\n"
            "**• `/details [player]`**\n"
            "└ Detailed history of last 10 sessions.\n\n"
            "**• `/close [player]`**\n"
            "└ Force close an agent's session.\n\n"
            "**• `/pause [player]`**\n"
            "└ Force pause an agent.\n\n"
            "**• `/edittime`**\n"
            "└ Manually adjust time (Add/Remove).\n\n"
            "**• `/cancel [player]`**\n"
            "└ Cancel a session without saving.\n\n"
            "**• `/remove_user`**\n"
            "└ Permanently delete a player's data.\n\n"
            "**• `/reset_server`**\n"
            "└ Global reset (Weekly/Monthly).\n\n"
            "**• `/auto_role`**\n"
            "└ Assign configured roles.\n\n"
            "**• `/setup`**\n"
            "└ General configuration panel."
        ),
        
        # --- ERREURS ---
        "error_generic": "❌ Error.", "error_perms": "⛔ Denied.", "error_admin_only": "⛔ Admin only.", "error_invalid_input": "❌ Invalid input.",
        "error_db": "⚠️ DB Error.", "error_no_role": "⚠️ No role.", "role_added": "✅ Role added."
    }
}

DATABASE_NAME = "chronos.db"