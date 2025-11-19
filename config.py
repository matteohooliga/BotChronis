# Informations du bot
BOT_NAME = "Chronis"
BOT_COLOR = 0x00AFF4  # Couleur bleue en hexadécimal
BOT_VERSION = "2.1.0"
GITHUB_LINK = "https://github.com/matteohooliga/BotChronis"

# Configuration des embeds
EMBED_TITLE = "🔍 Utilisateur(s) en service"
EMBED_DESCRIPTION_EMPTY = "Aucun utilisateur n'est en service… 😢"
# Le footer affiche maintenant le lien GitHub pour être visible partout
EMBED_FOOTER = f"Chronis V{BOT_VERSION} | {GITHUB_LINK}"

# Configuration des boutons
BUTTONS = {
    "start": {
        "label": "Démarrer son service",
        "emoji": "✨",
        "custom_id": "service_start"
    },
    "pause": {
        "label": "Prendre / Terminer sa pause",
        "emoji": "🍎",
        "custom_id": "service_pause"
    },
    "stop": {
        "label": "Terminer son service",
        "emoji": "🌙",
        "custom_id": "service_stop"
    }
}

# Messages de réponse
MESSAGES = {
    "service_started": "✅ **Service démarré** !\nVotre temps de service est maintenant comptabilisé.",
    "service_already_started": "⚠️ Vous êtes déjà en service !",
    "service_paused": "⏸️ **Pause démarrée** !\nVotre temps de service est mis en pause.",
    "service_resumed": "▶️ **Service repris** !\nLe compteur de temps a repris.",
    "service_not_started": "⚠️ Vous devez d'abord démarrer votre service !",
    "service_stopped": "🛑 **Service terminé** !\n\n**Durée totale** : {duration}\n**Temps de pause** : {pause}\n**Temps effectif** : {effective}",
    "service_forced_stop": "🔧 **Service forcé à se terminer** pour {user}.\n**Durée** : {duration}",
    "no_active_session": "❌ Aucune session active trouvée pour cet utilisateur.",
    "setup_complete": "✅ **Configuration terminée** !\nLe système de service est maintenant opérationnel dans {channel}.",
    "setup_error": "❌ Erreur lors de la configuration. Vérifiez les permissions du bot.",
    "no_setup": "⚠️ Le système n'est pas encore configuré sur ce serveur. Utilisez `/setup` pour le configurer."
}

# Base de données
DATABASE_NAME = "chronos.db"