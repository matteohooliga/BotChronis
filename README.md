````markdown
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
````

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

*(Astuce : Utilisez `screen` pour laisser le bot tourner en arrière-plan).*

-----

## 🖥️ **Liste des Commandes**

| Commande | Description | Permission |
| :--- | :--- | :--- |
| `/setup` | Panneau de configuration (Salons, Rôles, Langue). | Admin |
| `/config_rdv` | Configurer le système de Rendez-Vous et les motifs. | Admin |
| `/sum` | Vos statistiques personnelles (Temps, Dates, Moyenne). | Tous |
| `/sumall` | Classement général du serveur. | Tous |
| `/absence` | Déclarer une absence (Dates + Raison). | Tous |
| `/presence` | Liste des agents en service (ou recensement réactions). | Admin |
| `/server_stats` | Affiche les graphiques d'activité du serveur. | Admin |
| `/details [user]` | Historique détaillé des sessions d'un joueur. | Staff |
| `/edittime` | Ajouter/Retirer du temps manuellement. | Staff |
| `/forcestart` | Forcer la prise de service d'un joueur. | Staff |
| `/close` | Forcer la fin de service d'un joueur. | Admin |
| `/reset_server` | Réinitialiser les données (Semaine/Mois/Tout). | Admin |

-----

-----

# 🇬🇧 **Chronis Bot – RP Service & Appointment Manager**

**Chronis** is a powerful and optimized Discord bot designed for Roleplay communities (Police, EMS, Mechanics, etc.). It automatically manages on-duty time, appointment booking, leaves of absence, and generates detailed statistics with graphs.

-----

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

-----

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

*(Tip: Use `screen` to keep it running in the background).*

-----

## 🖥️ **Main Commands**

| Command | Description | Permission |
| :--- | :--- | :--- |
| `/setup` | Configure the bot (Channels, Roles, Language). | Admin |
| `/config_rdv` | Configure the Appointment system and reasons. | Admin |
| `/sum` | Display your personal stats (Time, Dates, Avg). | Everyone |
| `/sumall` | Display the server leaderboard. | Everyone |
| `/absence` | Declare an absence (Dates + Reason). | Everyone |
| `/presence` | Show the list of agents currently on duty. | Admin |
| `/server_stats` | Display server activity graphs. | Admin |
| `/details [user]` | Detailed history of a player's sessions. | Staff |
| `/edittime` | Manually add/remove time. | Staff |
| `/forcestart` | Force start a session for a player. | Staff |
| `/close` | Force close a player's session. | Admin |
| `/reset_server` | Wipe data (Weekly/Monthly/Total). | Admin |

```
```
