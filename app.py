from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import *
import requests
import random
import os

app = Flask(__name__)

# 硬編碼的敏感信息
line_bot_api = LineBotApi('ZXxMakoI5GNuejiC7Igzm1wvqw3vDxHGRlicvQPM1qizx9eqUJSouLzo1rbTZxo24IWBi0E3AP8lBSOj7SRVt0GkK5Duowbfjn/Zgn8YPHKYfxJC90NHFr8ihfry5YKOjFiNPkHv+XGPydkBv5F0UAdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('4226f38b9cd8bce4d0417d29d575f750')
GOOGLE_MAPS_API_KEY = 'AIzaSyD5sX433QilH8IVyjPiIpqqzJAy_dZrLvE'

# 用來存儲用戶狀態的字典
user_states = {}

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    print(f"Request body: {body}")
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("簽名驗證失敗。請檢查您的頻道訪問令牌和頻道密鑰。")
        abort(400)
    except Exception as e:
        print(f"例外情況: {e}")
        abort(400)
    return 'OK'

def get_nearby_restaurants(latitude, longitude):
    try:
        url = f'https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={latitude},{longitude}&radius=500&type=restaurant&key={GOOGLE_MAPS_API_KEY}'
        response = requests.get(url)
        response.raise_for_status()  # 為不良回應引發HTTPError
        data = response.json()
        print(f"Google Maps API 回應: {data}")
        return data.get('results', [])[:10]  # 限制返回的餐廳數量不超過10個
    except requests.RequestException as e:
        print(f"請求失敗: {e}")
        return []

def get_place_details(place_id):
    try:
        url = f'https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&key={GOOGLE_MAPS_API_KEY}'
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        print(f"Google Maps Place Details API 回應: {data}")
        return data.get('result', {})
    except requests.RequestException as e:
        print(f"請求失敗: {e}")
        return {}

def format_restaurant_info(restaurant):
    try:
        print(f"正在格式化餐廳信息: {restaurant}")
        place_id = restaurant.get('place_id', '')
        details = get_place_details(place_id)
        
        photo_reference = restaurant.get('photos')[0].get('photo_reference') if restaurant.get('photos') else ''
        name = restaurant.get('name', '')[:40]  # 確保名稱符合限制
        address = restaurant.get('vicinity', '')[:40]  # 限制地址長度
        phone_number = details.get('formatted_phone_number', '無電話號碼')[:20]  # 限制電話號碼長度
        map_url = f'https://www.google.com/maps/search/?api=1&query=Google&query_place_id={place_id}'
        photo_url = f'https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photoreference={photo_reference}&key={GOOGLE_MAPS_API_KEY}' if photo_reference else ''
        return {
            'photo_url': photo_url,
            'name': name,
            'address': address,
            'phone_number': phone_number,
            'map_url': map_url
        }
    except Exception as e:
        print(f"格式化餐廳信息時出現錯誤: {e}")
        return {
            'photo_url': '',
            'name': '未知餐廳',
            'address': '未知地址',
            'phone_number': '無電話號碼',
            'map_url': ''
        }

def create_carousel_template(restaurants):
    if not isinstance(restaurants, list):
        restaurants = [restaurants]
    
    columns = []
    for restaurant in restaurants:
        info = format_restaurant_info(restaurant)
        text = f"{info['address']}\n電話: {info['phone_number']}"
        if len(text) > 60:
            text = text[:57] + '...'  # 確保總長度不超過60個字符
        column = CarouselColumn(
            thumbnail_image_url=info['photo_url'],
            title=info['name'],
            text=text,
            actions=[
                URIAction(label='詳細資訊', uri=info['map_url'])
            ]
        )
        columns.append(column)
    
    template = TemplateSendMessage(
        alt_text='附近餐廳推薦',
        template=CarouselTemplate(columns=columns)
    )
    return template

@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    message_text = event.message.text.strip()
    user_id = event.source.user_id
    print(f"收到文本消息: {message_text} (來自用戶: {user_id})")

    if message_text == '推薦附近餐廳':
        user_states[user_id] = '推薦附近餐廳'
        print(f"設置用戶狀態為: {user_states[user_id]}")
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text='請麻煩您按左下方「+」，選擇位置訊息，將您的位置分享給我謝謝！♡♡♡'))
    elif message_text == '隨機推薦餐廳':
        user_states[user_id] = '隨機推薦餐廳'
        print(f"設置用戶狀態為: {user_states[user_id]}")
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text='請麻煩您按左下方「+」，選擇位置訊息，將您的位置分享給我謝謝！♡♡♡'))
    else:
        user_states[user_id] = None

@handler.add(MessageEvent, message=LocationMessage)
def handle_location_message(event):
    latitude = event.message.latitude
    longitude = event.message.longitude
    user_id = event.source.user_id
    print(f"收到位置消息: 經度={latitude}, 緯度={longitude} (來自用戶: {user_id})")
    
    nearby_restaurants = get_nearby_restaurants(latitude, longitude)
    print(f"獲取到的附近餐廳: {nearby_restaurants}")

    if not nearby_restaurants:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text='找不到附近的餐廳，請稍後再試。'))
        return

    user_state = user_states.get(user_id)
    print(f"用戶狀態: {user_state}")

    if user_state == '隨機推薦餐廳':
        random_restaurant = random.choice(nearby_restaurants)
        carousel_template = create_carousel_template([random_restaurant])
        print("隨機推薦餐廳的 Carousel 模板已創建")
        line_bot_api.reply_message(event.reply_token, carousel_template)
    elif user_state == '推薦附近餐廳':
        carousel_template = create_carousel_template(nearby_restaurants)
        print("推薦附近餐廳的 Carousel 模板已創建")
        line_bot_api.reply_message(event.reply_token, carousel_template)

    # 重置用戶狀態
    user_states[user_id] = None
    print(f"用戶狀態重置: {user_states[user_id]}")

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

