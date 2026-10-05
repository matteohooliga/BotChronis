# 🇫🇷 Chronis Bot – Gestion de Service RP & RDV

![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)
![Discord.py](https://img.shields.io/badge/discord.py-2.4%2B-5865F2)
![Database](https://img.shields.io/badge/database-MySQL-orange)

**Chronis** aide les communautés Roleplay (Police, EMS, mécaniciens et autres) à suivre les temps de service, gérer les rendez-vous et les absences, et consulter les statistiques de leurs équipes.

---

## 🚀 Nouveautés & Fonctionnalités

### ⏱️ Gestion de service

- Boutons persistants **Début / Pause / Fin** et panneau actualisé toutes les **10 secondes**.
- Calcul du temps effectif, pauses comprises, et statistiques individuelles ou globales.
- Maintenance quotidienne à **04 h, heure de Paris** : fermeture des sessions actives et redémarrage. La confirmation est publiée uniquement dans le salon de logs du serveur de développement.
- Mode maintenance global activable uniquement par le propriétaire avec `+maintenance on` ; il réserve les panneaux et commandes `/` au propriétaire.

### 🏥 Rendez-vous et absences

- Motifs de RDV configurables avec `/config_rdv`, demande par menu et traitement par le staff.
- Tickets privés avec transcription à la fermeture.
- Déclaration et consultation des absences.

### 📊 Statistiques et Chronis Premium

- `/sum`, `/sumall`, `/server_stats`, `/details` et `/presence` pour suivre l'activité.
- **Premium** : bilans hebdomadaires avec CSV dans le salon des logs, rappels d'objectifs, purge paramétrable, couleurs personnalisées, motifs de RDV illimités et alerte `/defcon`.
- L'export `/export` est accessible avec Premium ou après un vote Top.gg valide.
- Le propriétaire peut attribuer ou retirer un droit Premium manuel avec `+add_premium <ID>` et `+remove_premium <ID>` ; `+premium_list` affiche les serveurs Premium.
- Les serveurs Premium ne voient **aucune publicité partenaire**. Sur les serveurs gratuits, l'offre Hosterfy et le code **CHRONISBOT** apparaissent seulement dans `/about`, sur un bouton de `/help` et dans la confirmation privée du premier `/setup` réussi.

### 💬 Aide et messages privés

- `/help` présente les commandes et invite à envoyer un MP à Chronis pour obtenir de l'aide.
- Le bot répond aux questions reconnues dans `faq.json`. Chaque MP est aussi transmis au propriétaire, qui dispose d'un bouton **Répondre** pour répondre directement à l'utilisateur.
- Aucune publicité automatique pendant la maintenance de 04 h, les redémarrages, les rappels en MP ou les bilans.

### 🛠️ Architecture

- Python et `discord.py`, avec MySQL/MariaDB via `aiomysql`.
- Création des tables et ajout des colonnes ou index manquants au démarrage.
- Interface en français et en anglais.

---

## ⚙️ Installation & Configuration

### 1. Prérequis

- Python **3.9 ou plus récent** et une base **MySQL/MariaDB**.
- Un bot créé dans le [Portail Développeur Discord](https://discord.com/developers/applications).
- Les intents **Message Content** et **Server Members** activés pour les commandes `+`, les MP et les fonctions liées aux membres.

### 2. Installation

```bash
git clone https://github.com/matteohooliga/BotChronis.git
cd BotChronis
python3 -m pip install -r requirements.txt
```

`app.py`, `bot.py` et **`commands.py` doivent être à la racine** du dossier. Le bot accepte encore `cogs/commands.py` pour les anciens déploiements, mais donne la priorité à `commands.py` à la racine. Gardez une seule copie.

### 3. Configuration du `.env`

Le fichier `.env` fourni dans la copie locale est un **modèle sans identifiants**. Renseignez ses valeurs **sur le serveur** avant le démarrage :

```env
DISCORD_TOKEN=
TOPGG_TOKEN=

DB_HOST=""
DB_PORT=""
DB_USER=""
DB_PASSWORD=""
DB_NAME=""
```

`DISCORD_TOKEN` et les paramètres `DB_*` sont nécessaires. Renseignez `DB_PORT` avec un nombre, généralement `3306`. `TOPGG_TOKEN` sert à vérifier les votes Top.gg pour l'export gratuit ; il peut rester vide si cette possibilité n'est pas utilisée. **Ne publiez jamais un `.env` rempli de secrets.** Le fichier est ignoré par `.gitignore` : transmettez-le séparément à l'hébergeur. Si un ancien `.env` a déjà été publié, retirez-le du dépôt et remplacez les identifiants concernés.

### 4. Démarrage

```bash
python3 app.py
```

Sur **Row Hosting / Pterodactyl**, placez les fichiers directement dans `/home/container/`, gardez `PY_FILE=app.py` et `REQUIREMENTS_FILE=requirements.txt`. Le gestionnaire de processus doit relancer le bot après un redémarrage demandé par `+restart` ou par la maintenance quotidienne. Avec **PM2**, le fichier `ecosystem.config.cjs` est fourni (`pm2 start ecosystem.config.cjs`, puis `pm2 save`).

La base est initialisée au premier lancement. Le statut normal du bot revient après le redémarrage ; seul `+maintenance on` active la maintenance globale.

---

## 📚 Liste des commandes

### 👤 Commandes publiques

| Commande | Description |
| :-- | :-- |
| `/sum [user]` | Statistiques personnelles ou d'un autre membre. |
| `/sumall` | Classement du serveur. |
| `/absence` et `/absences_list` | Déclarer une absence et consulter les absences en cours. |
| `/feedback` | Envoyer un avis ou signaler un bug. |
| `/help` | Aide interactive et possibilité de contacter le bot en MP. |
| `/about` | Informations sur Chronis. |
| `/vote` | Lien vers le vote Top.gg. |
| `/premium` | Voir le statut Premium ou découvrir l'abonnement. |

### 👮 Staff / Direction — permission « Gérer le serveur »

| Commande | Description |
| :-- | :-- |
| `/forcestart [user]`, `/pause [user]` | Démarrer, mettre en pause ou reprendre un service. |
| `/edittime [user]`, `/details [user]` | Ajuster un temps ou consulter l'historique. |
| `/pauselist`, `/employees` | Voir les agents en pause ou la liste des employés. |
| `/delrole [user]` | Retirer les rôles configurés. |

### 👑 Administration — permission « Administrateur »

| Commande | Description |
| :-- | :-- |
| `/setup`, `/config_rdv` | Configurer le bot et les motifs de RDV. |
| `/server_stats`, `/presence [channel]` | Statistiques du serveur, agents en service ou recensement des réactions. |
| `/reaction_list [channel]`, `/service_list` | Accès direct aux vues des réactions ou du service. |
| `/close [user]`, `/cancel [user]` | Fermer ou annuler une session. |
| `/remove_user [user]`, `/reset_server` | Effacer des données ou réinitialiser une période. |
| `/auto_role [user]` | Attribuer les rôles automatiques configurés. |
| `/export` | Télécharger un CSV avec Premium ou un vote valide. |
| `/defcon` | Diffuser une alerte sur un serveur Premium. |

### 🛠️ Commandes avec le préfixe `+`

| Commande | Accès | Description |
| :-- | :-- | :-- |
| `+help` | Tous | Liste des commandes préfixées. |
| `+sync`, `+restart` | Admin | Synchroniser les commandes ou redémarrer le bot. |
| `+infos` | Propriétaire | Serveurs classés par membres, avec leur statut Premium. |
| `+premium_list` | Propriétaire | Liste des serveurs Premium. |
| `+add_premium <ID>`, `+remove_premium <ID>` | Propriétaire | Ajouter ou retirer un droit Premium manuel. Un abonnement Discord reste géré par Discord. |
| `+maintenance [statut\|on\|off]` | Propriétaire | Consulter ou modifier la maintenance globale. |
| `+sync_global`, `+fix_doublons`, `+debug` | Propriétaire | Gérer la synchronisation et recharger les commandes. |
| `+start`, `+stop` | Propriétaire | Confirmer que le bot est en ligne ou l'arrêter. |

---

# 🇬🇧 Chronis Bot – RP Service & Appointment Manager

**Chronis** helps roleplay communities track duty time, manage appointments and absences, and understand team activity.

## 🚀 Features

- Persistent **Start / Pause / End** controls; service panel refreshes every **10 seconds**.
- Daily restart at **04:00 Paris time** closes active sessions and restores the normal status on reconnect. Completion is announced only in the development server's log channel.
- Appointment reasons, booking menus, private tickets and transcripts; absence management.
- Personal and server statistics, charts and a leaderboard.
- **Premium** includes weekly CSV reports, configurable reset time, goal reminders, custom colours, unlimited appointment reasons and `/defcon` alerts. The owner can grant or revoke manual Premium rights.
- Premium servers see **no partner ads**. Free servers see the Hosterfy offer and **CHRONISBOT** code only in `/about`, an on-demand `/help` button and the private confirmation of their first `/setup`.
- Users can DM Chronis for help. Known questions receive a knowledge-base answer; the owner also receives the message and can reply through a button.

## ⚙️ Installation & Setup

1. Use Python **3.9+** and MySQL/MariaDB. Enable **Message Content** and **Server Members** intents in the Discord Developer Portal.
2. Clone the repository and install dependencies:

   ```bash
   git clone https://github.com/matteohooliga/BotChronis.git
   cd BotChronis
   python3 -m pip install -r requirements.txt
   ```

3. Fill in `.env` **on the server** using the blank template above. `DISCORD_TOKEN` and `DB_*` values are required; `TOPGG_TOKEN` enables vote checks for the free export option. Never commit a filled `.env`.
4. Run `python3 app.py`. On Row Hosting / Pterodactyl, place all runtime files directly in `/home/container/`, set `PY_FILE=app.py` and `REQUIREMENTS_FILE=requirements.txt`. For PM2, use `ecosystem.config.cjs`.

Keep `commands.py` beside `bot.py` at the repository root. The bot accepts `cogs/commands.py` only as a fallback for older deployments.

## 📚 Commands

| Access | Commands | Purpose |
| :-- | :-- | :-- |
| Everyone | `/sum`, `/sumall`, `/absence`, `/absences_list`, `/feedback`, `/help`, `/about`, `/vote`, `/premium` | Statistics, absences, help and bot information. |
| Manage Server | `/forcestart`, `/pause`, `/edittime`, `/details`, `/pauselist`, `/employees`, `/delrole` | Manage staff activity and records. |
| Administrator | `/setup`, `/config_rdv`, `/server_stats`, `/presence`, `/reaction_list`, `/service_list`, `/close`, `/cancel`, `/remove_user`, `/reset_server`, `/auto_role`, `/export`, `/defcon` | Configure and manage the server. `/defcon` needs Premium; `/export` needs Premium or a valid vote. |
| Administrator | `+sync`, `+restart` | Sync commands or restart Chronis. |
| Bot owner | `+infos`, `+premium_list`, `+add_premium <ID>`, `+remove_premium <ID>`, `+maintenance`, `+sync_global`, `+fix_doublons`, `+debug`, `+start`, `+stop` | Manage the bot and manual Premium rights. |

The `+help` command is available to everyone. The weekly report runs only on Premium servers and contains no advertising.

---

MIT licence: see [LICENSE](LICENSE).
