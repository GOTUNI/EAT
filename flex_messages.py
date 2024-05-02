from linebot.models import FlexSendMessage

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
