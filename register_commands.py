"""
Script à exécuter UNE SEULE FOIS pour enregistrer les slash commands sur Discord.
Usage : python register_commands.py
"""

import urllib.request
import urllib.parse
import json

BOT_TOKEN = "REMPLACE_PAR_TON_BOT_TOKEN"
CLIENT_ID = "REMPLACE_PAR_TON_CLIENT_ID"

COMMANDS = [
    {
        "name": "register",
        "description": "📝 Lance le formulaire d'inscription via Discord OAuth"
    },
    {
        "name": "ping",
        "description": "🏓 Teste la latence du serveur bot"
    },
    {
        "name": "help",
        "description": "❓ Affiche toutes les commandes disponibles"
    }
]

def register_commands():
    url = f"https://discord.com/api/v10/applications/{CLIENT_ID}/commands"
    data = json.dumps(COMMANDS).encode()

    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bot {BOT_TOKEN}",
            "Content-Type": "application/json"
        },
        method="PUT"
    )

    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read())
            print(f"✅ {len(result)} commandes enregistrées avec succès !")
            for cmd in result:
                print(f"   • /{cmd['name']} — {cmd['description']}")
    except Exception as e:
        print(f"❌ Erreur : {e}")

if __name__ == "__main__":
    register_commands()
