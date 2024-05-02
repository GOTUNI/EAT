from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, LocationMessage, FlexSendMessage
import requests
import random

app = Flask(__name__)

CHANNEL_ACCESS_TOKEN = 'YOUR_CHANNEL_ACCESS_TOKEN'
CHANNEL_SECRET = 'YOUR_CHANNEL_SECRET'
GOOGLE_MAPS_API_KEY = 'YOUR_GOOGLE_MAPS_API_KEY'

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

def search_nearby_restaurant(lat, lng):
    url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius=1000&type=restaurant&key={GOOGLE_MAPS_API_KEY}"
    response = requests.get(url)
    data = response.json()
    if 'results' in data and len(data['results']) > 0:
        restaurant = random.choice(data['results'])
        name = restaurant.get('name', 'Unknown')
        address = restaurant.get('vicinity', 'Unknown')
        map_url = f"https://www.google.com/maps/search/?api=1&query={lat},{lng}&query_place_id={restaurant['place_id']}"
        return {'name': name, 'address': address, 'map_url': map_url}
    else:
        return None

@handler.add(MessageEvent, message=LocationMessage)
def handle_location_message(event):
    lat = event.message.latitude
    lng = event.message.longitude
    restaurant = search_nearby_restaurant(lat, lng)
    if restaurant:
        google_style_message = generate_google_style_message(restaurant)
        line_bot_api.reply_message(event.reply_token, google_style_message)
    else:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="抱歉，附近沒有找到餐廳"))

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

def generate_google_style_message(restaurant):
    return FlexSendMessage(
        alt_text='Google Style Message',
        contents={
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": restaurant['name'],
                        "weight": "bold",
                        "size": "xl",
                        "margin": "md"
                    },
                    {
                        "type": "text",
                        "text": restaurant['address'],
                        "wrap": True,
                        "margin": "md"
                    },
                    {
                        "type": "button",
                        "action": {
                            "type": "uri",
                            "label": "查看地圖",
                            "uri": restaurant['map_url']
                        },
                        "color": "#1AA260",
                        "style": "primary",
                        "margin": "md"
                    }
                ]
            }
        }
    )

if __name__ == "__main__":
    app.run(debug=True)
