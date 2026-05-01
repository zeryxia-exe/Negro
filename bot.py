import discord
from discord import app_commands
from discord.ext import commands
import os
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = "1499869968899244252"
REDIRECT_URI = "G2Z-Hx8fSOv8d_DsROLk0k-CZdFBrbA5"

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# ── Bouton de vérification ────────────────────────────────────────────────────
class VerifyButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

        # Lien OAuth2 Discord avec scope "email"
        oauth_url = (
            f"https://discord.com/oauth2/authorize"
            f"?client_id={CLIENT_ID}"
            f"&redirect_uri={REDIRECT_URI}"
            f"&response_type=code"
            f"&scope=identify%20email"
        )

        self.add_item(discord.ui.Button(
            label="✅ Vérifier",
            style=discord.ButtonStyle.green,
            url=oauth_url,  # bouton URL, ouvre le navigateur
        ))


# ── Commande /verification ────────────────────────────────────────────────────
@bot.tree.command(
    name="verification",
    description="Envoie le message de vérification",
)
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def verification(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Vérification",
        description=(
            "Vérifiez-vous pour vous enregistrer.\n\n"
            "En cliquant sur le bouton ci-dessous, vous serez redirigé "
            "vers Discord pour autoriser l'accès à votre email."
        ),
        color=discord.Color.blurple(),
    )
    embed.set_footer(text="Votre email ne sera pas partagé publiquement.")

    await interaction.response.send_message(embed=embed, view=VerifyButton())


# ── Sync ──────────────────────────────────────────────────────────────────────
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Bot connecté : {bot.user} ({bot.user.id})")

bot.run(os.getenv("DISCORD_TOKEN"))
