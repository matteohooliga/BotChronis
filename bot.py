import os
import subprocess
import sys
import shutil
from dotenv import load_dotenv

print("====================================")
print("     CHRONIS BOT - DEMARRAGE")
print("           By matteohooliga")
print("====================================\n")

# -------------------------
#  Vérifier Python
# -------------------------
print(">>> Vérification de Python...")

try:
    version = sys.version
    print("[OK] Python détecté :", version.split()[0])
except Exception:
    print("❌ ERREUR : Python n'est pas installé !")
    print("Télécharge-le ici : https://www.python.org/downloads/")
    sys.exit(1)


# -------------------------
#  Vérifier .env
# -------------------------
print("\n>>> Vérification du fichier .env...")

if not os.path.exists(".env"):
    print("[AVERTISSEMENT] .env introuvable ! Création depuis .env.example...")
    if os.path.exists(".env.example"):
        shutil.copy(".env.example", ".env")
        print("[ACTION REQUISE] Édite le fichier .env et ajoute ton token Discord.")
    else:
        print("❌ Aucun .env ou .env.example trouvé ! Le bot ne peut pas démarrer.")
    sys.exit(1)
else:
    print("[OK] .env trouvé.")

# Charger les variables
load_dotenv()


# -------------------------
#  Installer les dépendances
# -------------------------
print("\n>>> Vérification des dépendances...")

try:
    import discord  # Test discord.py
    print("[OK] Dépendances déjà installées.")
except ImportError:
    print(">>> Installation des dépendances...")
    result = subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    if result.returncode != 0:
        print("❌ ERREUR : Impossible d'installer les dépendances.")
        sys.exit(1)
    print("[OK] Dépendances installées.")

print("\n====================================\n")
print(">>> Démarrage du bot...\n")


# ==========================================================
#  Le code de ton bot (collé et intégré proprement)
# ==========================================================
import discord
from discord.ext import commands
import asyncio

from database import ChronosDatabase
from utils import create_service_embed
from views import ServiceButtonsView
import config


# ----- Configuration Discord -----
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True


class ChronosBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None
        )
        self.db = ChronosDatabase()

    async def setup_hook(self):
        await self.load_extension('cogs.commands')
        self.add_view(ServiceButtonsView(self))

        guild_id = os.getenv('GUILD_ID')
        if guild_id:
            guild = discord.Object(id=int(guild_id))
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            print(f"Commandes synchronisées pour le serveur {guild_id}")
        else:
            await self.tree.sync()
            print("Commandes synchronisées globalement")

    async def on_ready(self):
        print(f"✅ {self.user} est connecté et prêt !")
        print(f"ID: {self.user.id}")
        print(f"Serveurs: {len(self.guilds)}")

        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="les services RP 👮"
            )
        )

    async def update_service_message(self, guild_id: int):
        config_data = self.db.get_guild_config(str(guild_id))
        if not config_data:
            return

        try:
            guild = self.get_guild(guild_id)
            if not guild:
                return

            channel = guild.get_channel(int(config_data['channel_id']))
            if not channel:
                return

            message = await channel.fetch_message(int(config_data['message_id']))
            if not message:
                return

            active_sessions = self.db.get_all_active_sessions(str(guild_id))
            embed = create_service_embed(active_sessions, guild)

            await message.edit(embed=embed)

        except Exception as e:
            print(f"Erreur lors de la mise à jour du message de service : {e}")


def main():
    token = os.getenv("DISCORD_TOKEN")

    if not token:
        print("❌ ERREUR : DISCORD_TOKEN manquant dans .env !")
        return

    bot = ChronosBot()

    try:
        bot.run(token)
    except KeyboardInterrupt:
        print("\n🛑 Arrêt du bot...")
    except Exception as e:
        print(f"❌ Erreur : {e}")
    finally:
        bot.db.close()


if __name__ == "__main__":
    main()
