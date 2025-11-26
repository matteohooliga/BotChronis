# 🇫🇷 **Chronis Bot – Gestion de Service RP & RDV**

![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)
![Discord.py](https://img.shields.io/badge/discord.py-2.0%2B-5865F2)
![Database](https://img.shields.io/badge/database-MySQL-orange)

**Chronis** est un bot Discord avancé et optimisé pour les communautés Roleplay (Police, EMS, Mécaniciens, etc.). Il gère automatiquement les temps de service, centralise les demandes de rendez-vous, gère les absences et génère des statistiques visuelles détaillées.

---

## 🚀 **Nouveautés & Fonctionnalités**

### ⏱️ **Gestion de Service (Time Tracking)**

- **Interface Fluide** : Boutons persistants (Début / Pause / Fin).
- **Temps Réel** : Panneau mis à jour automatiquement toutes les **10 secondes**.
- **Calculs Précis** : Prise en compte des pauses et du temps effectif.
- **Sécurité** : Redémarrage automatique à **04h00 (Heure France)** pour clôturer les sessions oubliées.

### 🏥 **Système de Rendez-Vous (RDV) [NOUVEAU]**

- **Configuration Personnalisée** : Créez vos propres motifs de RDV via `/config_rdv`.
- **Prise de RDV** : Menu déroulant interactif pour les joueurs.
- **Gestion Staff** : Accepter ou refuser une demande en un clic.
- **Tickets Automatiques** : Création d'un salon privé avec le patient.
- **Transcripts** : Génération automatique d'un fichier `.txt` de la conversation à la fermeture.

### 📊 **Statistiques & Graphiques [NOUVEAU]**

- **Personnelles** (`/sum`) : Temps total, moyenne, date de premier et dernier service.
- **Globales** (`/sumall`) : Classement (Leaderboard) complet du serveur.
- **Audit Serveur** (`/server_stats`) : **Graphiques générés dynamiquement** (Activité hebdo, moyenne par jour/heure).
- **Historique** (`/details`) : Liste paginée des 10 dernières sessions avec dates exactes.

### 🛠️ **Architecture Technique Optimisée**

- **MySQL (aiomysql)** : Base de données robuste avec pool de connexions asynchrone.
- **Index SQL** : Recherches instantanées même avec beaucoup de données.
- **Données Lisibles** : La BDD stocke désormais les durées en format texte (`1h 30m`) en plus du format brut pour faciliter la maintenance.
- **Auto-Repair** : Scripts de mise à jour automatique de la structure BDD inclus.

---

## ⚙️ **Installation & Configuration**

### 1. Prérequis

- Python 3.9 ou supérieur.
- Un serveur **MySQL** (local ou distant/VPS).
- Un Bot créé sur le [Portail Développeur Discord](https://discord.com/developers/applications).

### 2. Installation

Clonez le dépôt et installez les dépendances :

```bash
git clone [https://github.com/votre-repo/chronis-bot.git](https://github.com/votre-repo/chronis-bot.git)
cd chronis-bot
pip install -r requirements.txt
```

### 3\. Configuration (.env)

Créez un fichier `.env` à la racine et remplissez-le :

```env
DISCORD_TOKEN=votre_token_discord
DB_HOST=ip_de_votre_bdd
DB_PORT=3306
DB_USER=utilisateur_bdd
DB_PASSWORD=mot_de_passe_bdd
DB_NAME=nom_de_la_base
```

### 4\. Démarrage

Le bot initialise automatiquement les tables et les index SQL au premier lancement.

**Windows :**
Lancez simplement `start_bot.bat`.

**Linux :**
Utilisez le script fourni pour que le bot redémarre en cas de crash :

```bash
chmod +x start.sh
./start.sh
```

_(Astuce : Utilisez `screen` pour laisser le bot tourner en arrière-plan)._

---

## 📚 **Liste Complète des Commandes**

### 👤 **Commandes Publiques (Tout le monde)**

_Accessibles à tous les membres._

| Commande          | Description                                                                         |
| :---------------- | :---------------------------------------------------------------------------------- |
| **/sum** `[user]` | Affiche les statistiques personnelles (Temps, Moyenne, Dates) ou celles d'un autre. |
| **/sumall**       | Affiche le classement global (Leaderboard) du serveur.                              |
| **/absence**      | Déclarer une absence officielle (Date début/fin + Raison).                          |
| **/feedback**     | Envoyer un avis ou signaler un bug au développeur.                                  |
| **/help**         | Affiche le menu d'aide interactif.                                                  |
| **/about**        | Affiche les informations techniques et statistiques du bot.                         |

### 👮 **Commandes Staff / Direction**

_Nécessite la permission "Gérer le serveur" ou un rôle spécifique._

| Commande                 | Description                                                |
| :----------------------- | :--------------------------------------------------------- |
| **/forcestart** `[user]` | Démarre de force la prise de service d'un joueur.          |
| **/pause** `[user]`      | Met en pause (ou reprend) de force le service d'un joueur. |
| **/details** `[user]`    | Historique détaillé des 10 dernières sessions d'un joueur. |
| **/edittime** `[user]`   | Ajouter ou retirer manuellement du temps à un joueur.      |
| **/pauselist**           | Affiche la liste des agents actuellement en pause.         |

### 👑 **Commandes Administrateur**

_Nécessite la permission "Administrateur"._

| Commande                  | Description                                                     |
| :------------------------ | :-------------------------------------------------------------- |
| **/setup**                | Panneau de configuration principal (Salons, Rôles, Langue).     |
| **/config_rdv**           | Configurer le système de Rendez-Vous et les motifs.             |
| **/server_stats**         | Audit complet du serveur avec graphiques d'activité.            |
| **/presence** `[channel]` | Liste des agents en service ou recensement des réactions.       |
| **/close** `[user]`       | Ferme de force la session d'un joueur (sauvegarde le temps).    |
| **/cancel** `[user]`      | Annule une session en cours **sans** sauvegarder (suppression). |
| **/remove_user** `[user]` | Supprime définitivement toutes les données d'un joueur.         |
| **/reset_server**         | Réinitialise les données (Semaine/Mois/Tout).                   |
| **/auto_role** `[user]`   | Attribue manuellement les rôles automatiques configurés.        |

### 🛠️ **Commandes Système (Préfixe +)**

_Réservées au Propriétaire (Owner) ou aux Admins pour la maintenance._

| Commande          | Permission | Description                                                         |
| :---------------- | :--------- | :------------------------------------------------------------------ |
| **+sync**         | Admin      | Synchronise les commandes Slash (`/`) sur le serveur.               |
| **+restart**      | Admin      | Redémarre le bot (utile après une mise à jour).                     |
| **+fix_doublons** | Owner      | Nettoie et resynchronise les commandes pour supprimer les doublons. |
| **+maintenance**  | Owner      | Active/Désactive le mode maintenance (bloque les boutons).          |
| **+debug**        | Owner      | Recharge l'extension `cogs` sans éteindre le bot.                   |
| **+infos**        | Owner      | Affiche la liste des serveurs où le bot est présent.                |
| **+stop**         | Owner      | Arrête complètement le processus du bot.                            |
| **+start**        | Owner      | Envoie un message de confirmation "Bot en ligne".                   |

---

---

# 🇬🇧 **Chronis Bot – RP Service & Appointment Manager**

**Chronis** is a powerful and optimized Discord bot designed for Roleplay communities (Police, EMS, Mechanics, etc.). It automatically manages on-duty time, appointment booking, leaves of absence, and generates detailed statistics with graphs.

---

## 🚀 **Key Features**

### ⏱️ **Service Management (Time Tracking)**

- **Interactive Interface**: Persistent buttons (Start / Pause / End).
- **Real-time**: Panel auto-refreshes every **10 seconds**.
- **Accurate**: Handles breaks and effective working time accurately.
- **Safety**: Auto-restart at **04:00 AM (French Time)** to close forgotten sessions.

### 🏥 **Appointment System (RDV) [NEW]**

- **Custom Config**: Define your own appointment reasons via `/config_rdv`.
- **Booking**: Players select a reason via a dropdown menu.
- **Staff Management**: Accept or refuse requests instantly.
- **Tickets**: Automatic creation of a private channel with the user.
- **Transcripts**: Generates a `.txt` file of the conversation when closed.

### 📊 **Advanced Statistics [NEW]**

- **Personal** (`/sum`): Total time, average, first and last shift dates.
- **Global** (`/sumall`): Full server leaderboard.
- **Server Audit** (`/server_stats`): **Dynamically generated graphs** (Weekly activity, daily averages).
- **History** (`/details`): Paged list of the last 10 sessions with exact timestamps.

### 🛠️ **Optimized Tech Stack**

- **MySQL (aiomysql)**: Robust database with async connection pooling.
- **SQL Indexes**: Instant queries even with large datasets.
- **Human-Readable DB**: Data is stored with human-readable formats (e.g., `1h 30m`) alongside raw milliseconds for easier maintenance.
- **Auto-Repair**: Automatic DB structure update scripts included.

---

## ⚙️ **Installation & Setup**

### 1\. Prerequisites

- Python 3.9 or higher.
- A **MySQL** server (local or remote/VPS).
- A Bot created on the [Discord Developer Portal](https://www.google.com/url?sa=E&source=gmail&q=https://discord.com/developers/applications).

### 2\. Installation

Clone the repository and install dependencies:

```bash
git clone [https://github.com/your-repo/chronis-bot.git](https://github.com/your-repo/chronis-bot.git)
cd chronis-bot
pip install -r requirements.txt
```

### 3\. Configuration (.env)

Create a `.env` file at the root folder:

```env
DISCORD_TOKEN=your_discord_token
DB_HOST=your_db_ip
DB_PORT=3306
DB_USER=db_user
DB_PASSWORD=db_password
DB_NAME=db_name
```

### 4\. Start

The bot automatically initializes SQL tables and indexes on the first run.

**Windows:**
Just run `start_bot.bat`.

**Linux:**
Use the provided script to keep the bot running:

```bash
chmod +x start.sh
./start.sh
```

_(Tip: Use `screen` to keep it running in the background)._

---

## 📚 **Complete Command List**

### 👤 **Public Commands (Everyone)**

_Available to all server members._

| Command           | Description                                                      |
| :---------------- | :--------------------------------------------------------------- |
| **/sum** `[user]` | Display personal stats (Time, Avg, Dates) or check another user. |
| **/sumall**       | Display the server leaderboard.                                  |
| **/absence**      | Declare an official absence (Dates + Reason).                    |
| **/feedback**     | Send feedback or report a bug to the developer.                  |
| **/help**         | Show the interactive help menu.                                  |
| **/about**        | Display bot technical info and stats.                            |

### 👮 **Staff / Management Commands**

_Requires "Manage Server" permission or specific role._

| Command                  | Description                                 |
| :----------------------- | :------------------------------------------ |
| **/forcestart** `[user]` | Force start a player's service session.     |
| **/pause** `[user]`      | Force pause (or resume) a player's service. |
| **/details** `[user]`    | Detailed history of the last 10 sessions.   |
| **/edittime** `[user]`   | Manually add or remove time from a player.  |
| **/pauselist**           | Show the list of agents currently on pause. |

### 👑 **Admin Commands**

_Requires "Administrator" permission._

| Command                   | Description                                           |
| :------------------------ | :---------------------------------------------------- |
| **/setup**                | Main configuration panel (Channels, Roles, Language). |
| **/config_rdv**           | Configure the Appointment system and reasons.         |
| **/server_stats**         | Full server audit with activity graphs.               |
| **/presence** `[channel]` | List of on-duty agents or reaction census.            |
| **/close** `[user]`       | Force close a session (saves time).                   |
| **/cancel** `[user]`      | Cancel a session **without** saving (deletion).       |
| **/remove_user** `[user]` | Permanently delete all data for a user.               |
| **/reset_server**         | Wipe data (Weekly/Monthly/Total).                     |
| **/auto_role** `[user]`   | Manually assign configured auto-roles.                |

### 🛠️ **System Commands (Prefix +)**

_Reserved for Bot Owner or Admins for maintenance._

| Command           | Permission | Description                                      |
| :---------------- | :--------- | :----------------------------------------------- |
| **+sync**         | Admin      | Sync Slash commands (`/`) on the current server. |
| **+restart**      | Admin      | Restart the bot (useful after updates).          |
| **+fix_doublons** | Owner      | Clean and resync commands to fix duplicates.     |
| **+maintenance**  | Owner      | Toggle maintenance mode (locks buttons).         |
| **+debug**        | Owner      | Reload the `cogs` extension without stopping.    |
| **+infos**        | Owner      | Show the list of servers using the bot.          |
| **+stop**         | Owner      | Completely stop the bot process.                 |
| **+start**        | Owner      | Send a "Bot Online" confirmation message.        |

```

```
