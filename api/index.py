from flask import Flask, request
import requests
import os

app = Flask(__name__)

CLIENT_ID = "1499869968899244252"
CLIENT_SECRET = "G2Z-Hx8fSOv8d_DsROLk0k-CZdFBrbA5"
REDIRECT_URI  = "negro-lemon.vercel.app"

@app.route("/")
def home():
    return "Bot de vérification en ligne ✅"

@app.route("/callback")
def callback():
    code = request.args.get("code")
    if not code:
        return "❌ Aucun code reçu.", 400

    token_resp = requests.post(
        "https://discord.com/api/oauth2/token",
        data={
            "client_id":     CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type":    "authorization_code",
            "code":          code,
            "redirect_uri":  REDIRECT_URI,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    token_data = token_resp.json()
    access_token = token_data.get("access_token")

    if not access_token:
        return f"❌ Erreur token : {token_data}", 400

    user_resp = requests.get(
        "https://discord.com/api/users/@me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    user = user_resp.json()

    username = user.get("username")
    email    = user.get("email")
    user_id  = user.get("id")

    print(f"✅ {username} ({user_id}) — {email}")

    return f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: sans-serif;
                text-align: center;
                margin-top: 80px;
                background: #2b2d31;
                color: white;
            }}
            .card {{
                background: #313338;
                border-radius: 12px;
                padding: 40px;
                display: inline-block;
                box-shadow: 0 4px 20px rgba(0,0,0,0.4);
            }}
            h1 {{ color: #57f287; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h1>✅ Vérification réussie !</h1>
            <p>Bonjour <strong>{username}</strong> !</p>
            <p>Votre email <strong>{email}</strong> a bien été enregistré.</p>
            <p>Vous pouvez fermer cette page et retourner sur Discord.</p>
        </div>
    </body>
    </html>
    """
