from http.server import BaseHTTPRequestHandler
import json
import time
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError

DISCORD_PUBLIC_KEY = "26e73aa72d3ad3927cdfd5c0dc2b9d15d990e02e105bfd95700a369ef9f6c26c"
DISCORD_BOT_TOKEN = "MTQ5OTg2OTk2ODg5OTI0NDI1Mg.G7voSN.bxlPQjGA-LfO1EhY8sDzeOfnQnWRmVvpfLOSTE"
DISCORD_CLIENT_ID = "1499869968899244252"
DISCORD_CLIENT_SECRET = "6LM5ZPmWcfdpqzB6Gz752-6uBdrOXbMR"
VERCEL_URL = "negro-lemon.vercel.app"  # Sans https://

def verify_signature(public_key: str, signature: str, timestamp: str, body: str) -> bool:
    try:
        vk = VerifyKey(bytes.fromhex(public_key))
        vk.verify(f"{timestamp}{body}".encode(), bytes.fromhex(signature))
        return True
    except BadSignatureError:
        return False

def handle_ping():
    return {"type": 1}

def handle_ping_command():
    """Mesure le temps de réaction du serveur"""
    start = time.time()
    elapsed = round((time.time() - start) * 1000)
    return {
        "type": 4,
        "data": {
            "embeds": [{
                "title": "🏓 Pong!",
                "description": f"**Latence du serveur :** `{elapsed}ms`",
                "color": 0x5865F2,
                "footer": {"text": "Discord Register Bot"}
            }]
        }
    }

def handle_help_command():
    """Affiche l'aide des commandes"""
    return {
        "type": 4,
        "data": {
            "embeds": [{
                "title": "📖 Aide — Discord Register Bot",
                "color": 0x5865F2,
                "fields": [
                    {
                        "name": "📝 `/register`",
                        "value": "Lance le processus d'inscription.\nVous recevrez un lien OAuth Discord pour autoriser l'accès à votre email.\nUne fois connecté, votre **User ID** et **email** vous seront envoyés en message privé.",
                        "inline": False
                    },
                    {
                        "name": "🏓 `/ping`",
                        "value": "Teste la latence du serveur bot.",
                        "inline": False
                    },
                    {
                        "name": "❓ `/help`",
                        "value": "Affiche ce message d'aide.",
                        "inline": False
                    }
                ],
                "footer": {"text": "Discord Register Bot • Powered by Vercel"}
            }],
            "flags": 64  # Ephemeral (visible uniquement par l'utilisateur)
        }
    }

def handle_register_command(user_id: str):
    """Génère un lien OAuth pour l'inscription"""
    base_url = f"https://{VERCEL_URL}"
    oauth_url = (
        f"https://discord.com/oauth2/authorize"
        f"?client_id={DISCORD_CLIENT_ID}"
        f"&redirect_uri={base_url}/api/oauth-callback"
        f"&response_type=code"
        f"&scope=identify%20email"
        f"&state={user_id}"
    )
    return {
        "type": 4,
        "data": {
            "embeds": [{
                "title": "📝 Inscription",
                "description": (
                    "Clique sur le bouton ci-dessous pour t'inscrire.\n\n"
                    "Tu seras redirigé vers Discord pour autoriser l'accès à ton **email**.\n"
                    "Une fois l'autorisation accordée, tu recevras un **message privé** "
                    "avec ton **User ID** et ton **email**."
                ),
                "color": 0x57F287,
                "footer": {"text": "L'autorisation expire dans 5 minutes"}
            }],
            "components": [{
                "type": 1,
                "components": [{
                    "type": 2,
                    "style": 5,  # Link button
                    "label": "🔗 S'inscrire avec Discord",
                    "url": oauth_url
                }]
            }],
            "flags": 64  # Ephemeral
        }
    }

def route_command(data: dict) -> dict:
    command_name = data.get("data", {}).get("name", "")
    user = data.get("member", {}).get("user") or data.get("user", {})
    user_id = user.get("id", "")

    if command_name == "ping":
        return handle_ping_command()
    elif command_name == "help":
        return handle_help_command()
    elif command_name == "register":
        return handle_register_command(user_id)
    else:
        return {
            "type": 4,
            "data": {"content": "❌ Commande inconnue.", "flags": 64}
        }

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(content_length).decode("utf-8")

        signature = self.headers.get("X-Signature-Ed25519", "")
        timestamp = self.headers.get("X-Signature-Timestamp", "")

        # Vérification de la signature Discord
        if not verify_signature(DISCORD_PUBLIC_KEY, signature, timestamp, raw_body):
            self.send_response(401)
            self.end_headers()
            self.wfile.write(b"Invalid signature")
            return

        body = json.loads(raw_body)
        interaction_type = body.get("type")

        # PING Discord (vérification de l'endpoint)
        if interaction_type == 1:
            response = handle_ping()
        # APPLICATION_COMMAND (slash commands)
        elif interaction_type == 2:
            response = route_command(body)
        else:
            response = {"type": 1}

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())

    def log_message(self, format, *args):
        pass  # Silence les logs HTTP par défaut
