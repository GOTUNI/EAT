from flask import Flask, request, abort
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *
import requests
import os

app = Flask(__name__)
# Channel Access Token
line_bot_api = LineBotApi('ZXxMakoI5GNuejiC7Igzm1wvqw3vDxHGRlicvQPM1qizx9eqUJSouLzo1rbTZxo24IWBi0E3AP8lBSOj7SRVt0GkK5Duowbfjn/Zgn8YPHKYfxJC90NHFr8ihfry5YKOjFiNPkHv+XGPydkBv5F0UAdB04t89/1O/w1cDnyilFU=')
# Channel Secret
handler = WebhookHandler('4226f38b9cd8bce4d0417d29d575f750')
GOOGLE_MAPS_API_KEY = 'AIzaSyD5sX433QilH8IVyjPiIpqqzJAy_dZrLvE'

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)
    except Exception as e:
        print(f"Exception: {e}")
        abort(400)
    return 'OK'

def get_nearby_restaurants(latitude, longitude):
    url = f'https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={latitude},{longitude}&radius=500&type=restaurant&key={GOOGLE_MAPS_API_KEY}'
    print(f"Requesting nearby restaurants with URL: {url}")
    response = requests.get(url)
    data = response.json()
    print(f"Nearby restaurants response: {data}")
    return data.get('results', [])[:10]

def get_restaurant_details(place_id):
    url = f'https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&key={GOOGLE_MAPS_API_KEY}'
    print(f"Requesting restaurant details with URL: {url}")
    response = requests.get(url)
    details = response.json().get('result', {})
    print(f"Restaurant details response: {details}")
    return details

def format_restaurant_info(restaurant):
    photo_url = restaurant.get('photos')[0]['photo_reference'] if restaurant.get('photos') else ''
    name = restaurant.get('name', '')
    address = restaurant.get('vicinity', '')[:60]
    place_id = restaurant.get('place_id', '')
    
    details = get_restaurant_details(place_id)
    phone_number = details.get('formatted_phone_number', '電話號碼不詳')
    
    return {
        'photo_url': f'https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photoreference={photo_url}&key={GOOGLE_MAPS_API_KEY}' if photo_url else '',
        'name': name,
        'address': address,
        'phone_number': phone_number
    }

def create_carousel_template(restaurants):
    columns = []
    for restaurant in restaurants:
        info = format_restaurant_info(restaurant)
        column = CarouselColumn(
            thumbnail_image_url=info['photo_url'] if info['photo_url'] else None,
            title=info['name'],
            text=f"{info['address']}\n電話: {info['phone_number']}",
            actions=[
                MessageAction(label='詳細資訊', text=f'詳細資訊: {info["name"]}\n電話: {info["phone_number"]}'),
            ]
        )
        columns.append(column)
    return TemplateSendMessage(
        alt_text='附近餐廳推薦',
        template=CarouselTemplate(columns=columns)
    )

@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    user_id = event.source.user_id
    message_text = event.message.text
    if message_text == '推薦附近餐廳':
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text='按左下方「+」，選擇位置訊息，將您的位置分享給我謝謝！♡♡♡'))
    elif message_text == '隨機推薦附近餐廳':
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text='按左下方「+」，選擇位置訊息，將您的位置分享給我謝謝！♡♡♡'))

@handler.add(MessageEvent, message=LocationMessage)
def handle_location_message(event):
    user_id = event.source.user_id
    latitude = event.message.latitude
    longitude = event.message.longitude
    nearby_restaurants = get_nearby_restaurants(latitude, longitude)
    carousel_template = create_carousel_template(nearby_restaurants)
    line_bot_api.reply_message(event.reply_token, carousel_template)

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
