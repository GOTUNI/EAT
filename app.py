import random
import requests
import os
from linebot import WebhookHandler, LineBotApi
from linebot.models import TextSendMessage, TemplateSendMessage, CarouselTemplate, CarouselColumn, MessageAction
from flask import Flask, request, abort
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, LocationMessage

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = 'ZXxMakoI5GNuejiC7Igzm1wvqw3vDxHGRlicvQPM1qizx9eqUJSouLzo1rbTZxo24IWBi0E3AP8lBSOj7SRVt0GkK5Duowbfjn/Zgn8YPHKYfxJC90NHFr8ihfry5YKOjFiNPkHv+XGPydkBv5F0UAdB04t89/1O/w1cDnyilFU='
GOOGLE_MAPS_API_KEY = 'AIzaSyD5sX433QilH8IVyjPiIpqqzJAy_dZrLvE'

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler('4226f38b9cd8bce4d0417d29d575f750')

def get_nearby_restaurants(latitude, longitude):
    url = f'https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={latitude},{longitude}&radius=500&type=restaurant&key={GOOGLE_MAPS_API_KEY}'
    response = requests.get(url)
    data = response.json()
    return data.get('results', [])

def format_restaurant_info(restaurant):
    photo_reference = restaurant.get('photos', [{}])[0].get('photo_reference', '')
    photo_url = f'https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photoreference={photo_reference}&key={GOOGLE_MAPS_API_KEY}' if photo_reference else ''
    name = restaurant.get('name', '未知餐廳')
    address = restaurant.get('vicinity', '地址未知')
    phone_number = restaurant.get('formatted_phone_number', '電話號碼未知')
    return {
        'photo_url': photo_url,
        'name': name,
        'address': address,
        'phone_number': phone_number
    }

def create_carousel_template(restaurants):
    columns = []
    for restaurant in restaurants:
        info = format_restaurant_info(restaurant)
        column = CarouselColumn(
            thumbnail_image_url=info['photo_url'] or 'https://via.placeholder.com/400',
            title=info['name'][:40],
            text=info['address'][:60],
            actions=[
                MessageAction(label='詳細資訊', text=f'詳細資訊: {info["name"]}'),
            ]
        )
        columns.append(column)
    return TemplateSendMessage(
        alt_text='附近餐廳推薦',
        template=CarouselTemplate(columns=columns)
    )

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    print(f"Request body: {body}")
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)
    except Exception as e:
        print(f"Exception: {e}")
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    message_text = event.message.text
    if message_text in ['推薦附近餐廳', '隨機推薦附近餐廳']:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text='請分享您的位置'))
    else:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text='未知的指令'))

@handler.add(MessageEvent, message=LocationMessage)
def handle_location_message(event):
    latitude = event.message.latitude
    longitude = event.message.longitude
    message_text = event.message.text
    print(f"Received location: {latitude}, {longitude}")
    if message_text == '推薦附近餐廳':
        nearby_restaurants = get_nearby_restaurants(latitude, longitude)
        carousel_template = create_carousel_template(nearby_restaurants)
        line_bot_api.reply_message(event.reply_token, carousel_template)
    elif message_text == '隨機推薦附近餐廳':
        nearby_restaurants = get_nearby_restaurants(latitude, longitude)
        if nearby_restaurants:
            random_restaurant = random.choice(nearby_restaurants)
            info = format_restaurant_info(random_restaurant)
            text_message = f'名稱: {info["name"]}\n地址: {info["address"]}\n電話: {info["phone_number"]}'
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=text_message))
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text='找不到附近的餐廳'))

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
