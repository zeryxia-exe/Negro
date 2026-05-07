from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
import urllib.request
import urllib.parse

DISCORD_BOT_TOKEN = "MTQ5OTg2OTk2ODg5OTI0NDI1Mg.G7voSN.bxlPQjGA-LfO1EhY8sDzeOfnQnWRmVvpfLOSTE"
DISCORD_CLIENT_ID = "1499869968899244252"
DISCORD_CLIENT_SECRET = "6LM5ZPmWcfdpqzB6Gz752-6uBdrOXbMR"
VERCEL_URL = "negro-lemon.vercel.app"  # Sans https://


def exchange_code(code: str) -> dict:
    """Échange le code OAuth contre un access token"""
    base_url = f"https://{VERCEL_URL}"
    data = urllib.parse.urlencode({
        "client_id": DISCORD_CLIENT_ID,
        "client_secret": DISCORD_CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": f"{base_url}/api/oauth-callback",
    }).encode()

    req = urllib.request.Request(
        "https://discord.com/api/oauth2/token",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def get_user_info(access_token: str) -> dict:
    """Récupère les infos de l'utilisateur (id + email)"""
    req = urllib.request.Request(
        "https://discord.com/api/users/@me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def send_dm(user_id: str, user_info: dict):
    """Envoie un DM à l'utilisateur avec son User ID et son email"""
    # Créer un DM channel
    dm_data = json.dumps({"recipient_id": user_id}).encode()
    req = urllib.request.Request(
        "https://discord.com/api/v10/users/@me/channels",
        data=dm_data,
        headers={
            "Authorization": f"Bot {DISCORD_BOT_TOKEN}",
            "Content-Type": "application/json"
        },
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        channel = json.loads(resp.read())

    channel_id = channel["id"]
    username = user_info.get("username", "Inconnu")
    email = user_info.get("email", "Non disponible")
    uid = user_info.get("id", "Inconnu")

    # Envoyer le message dans le DM channel
    msg_data = json.dumps({
        "embeds": [{
            "title": "✅ Inscription réussie !",
            "description": (
                f"Voici les informations liées à ton compte Discord :\n\n"
                f"👤 **Nom d'utilisateur :** `{username}`\n"
                f"🆔 **User ID :** `{uid}`\n"
                f"📧 **Email :** `{email}`"
            ),
            "color": 0x57F287,
            "footer": {"text": "Discord Register Bot • Ces informations sont confidentielles"}
        }]
    }).encode()

    req2 = urllib.request.Request(
        f"https://discord.com/api/v10/channels/{channel_id}/messages",
        data=msg_data,
        headers={
            "Authorization": f"Bot {DISCORD_BOT_TOKEN}",
            "Content-Type": "application/json"
        },
        method="POST"
    )
    urllib.request.urlopen(req2)


HTML_SUCCESS = """
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>Inscription réussie</title>
  <style>
    body { font-family: sans-serif; background: #23272a; color: #fff; display: flex;
           align-items: center; justify-content: center; height: 100vh; margin: 0; }
    .card { background: #2c2f33; border-radius: 12px; padding: 40px; text-align: center;
            max-width: 400px; box-shadow: 0 4px 24px rgba(0,0,0,0.4); }
    h1 { color: #57f287; font-size: 2rem; margin-bottom: 8px; }
    p { color: #b9bbbe; margin-top: 12px; }
    .badge { background: #57f287; color: #23272a; border-radius: 6px;
             padding: 4px 12px; font-weight: bold; display: inline-block; margin-top: 16px; }
  </style>
</head>
<body>
  <div class="card">
    <h1>✅ Inscription réussie !</h1>
    <p>Tes informations ont été envoyées en message privé sur Discord.</p>
    <div class="badge">Tu peux fermer cette page</div>
  </div>
</body>
</html>
"""

HTML_ERROR = """
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>Erreur</title>
  <style>
    body { font-family: sans-serif; background: #23272a; color: #fff; display: flex;
           align-items: center; justify-content: center; height: 100vh; margin: 0; }
    .card { background: #2c2f33; border-radius: 12px; padding: 40px; text-align: center;
            max-width: 400px; }
    h1 { color: #ed4245; }
    p { color: #b9bbbe; }
  </style>
</head>
<body>
  <div class="card">
    <h1>❌ Une erreur est survenue</h1>
    <p>Impossible de finaliser l'inscription. Réessaie avec <code>/register</code>.</p>
  </div>
</body>
</html>
"""


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        code = params.get("code", [None])[0]
        state = params.get("state", [None])[0]  # = user_id de la personne qui a fait /register

        if not code or not state:
            self._respond(400, HTML_ERROR)
            return

        try:
            token_data = exchange_code(code)
            access_token = token_data["access_token"]
            user_info = get_user_info(access_token)
            send_dm(state, user_info)
            self._respond(200, HTML_SUCCESS)
        except Exception as e:
            print(f"OAuth error: {e}")
            self._respond(500, HTML_ERROR)

    def _respond(self, status: int, html: str):
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode())

    def log_message(self, format, *args):
        pass
