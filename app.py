from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, LocationMessage
import requests
import random

app = Flask(__name__)

CHANNEL_ACCESS_TOKEN = 'ZXxMakoI5GNuejiC7Igzm1wvqw3vDxHGRlicvQPM1qizx9eqUJSouLzo1rbTZxo24IWBi0E3AP8lBSOj7SRVt0GkK5Duowbfjn'
CHANNEL_SECRET = '4226f38b9cd8bce4d0417d29d575f750'
GOOGLE_MAPS_API_KEY = 'AIzaSyD5sX433QilH8IVyjPiIpqqzJAy_dZrLvE'

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

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

@handler.add(MessageEvent, message=LocationMessage)
def handle_location_message(event):
    lat = event.message.latitude
    lng = event.message.longitude
    restaurant = search_nearby_restaurant(lat, lng)
    if restaurant:
        reply_text = f"我找到一家附近的餐廳：{restaurant['name']}，地址：{restaurant['address']}"
    else:
        reply_text = "抱歉，附近沒有找到餐廳"
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))

def search_nearby_restaurant(lat, lng):
    url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius=1000&type=restaurant&key={GOOGLE_MAPS_API_KEY}"
    response = requests.get(url)
    data = response.json()
    if 'results' in data and len(data['results']) > 0:
        restaurant = random.choice(data['results'])
        name = restaurant.get('name', 'Unknown')
        address = restaurant.get('vicinity', 'Unknown')
        return {'name': name, 'address': address}
    else:
        return None

if __name__ == "__main__":
    app.run(debug=True)
