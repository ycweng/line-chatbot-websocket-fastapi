import os.path
from typing import List
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException
from fastapi import Response
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, FlexSendMessage, ImageSendMessage,
)
import asyncio

from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware

access_token = os.getenv("RUTEN_LINE_ACCESS_TOKEN")
secret = os.getenv("RUTEN_LINE_SECRET")

line_bot_api = LineBotApi(access_token)
handler = WebhookHandler(secret)

app = FastAPI()
app.add_middleware(HTTPSRedirectMiddleware)


class ConnectionManager:
    def __init__(self):
        # 存放激活的ws连接对象
        self.active_connections: List[WebSocket] = []

    async def connect(self, ws: WebSocket):
        # 等待连接
        await ws.accept()
        # 存储ws连接对象
        self.active_connections.append(ws)

    def disconnect(self, ws: WebSocket):
        # 关闭时 移除ws对象
        self.active_connections.remove(ws)

    @staticmethod
    async def send_personal_message(message: str, ws: WebSocket):
        # 发送个人消息
        await ws.send_text(message)

    async def broadcast(self, message: str):
        # 广播消息
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()


@app.websocket("/ws/user1")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    #    await manager.broadcast(f"有人登入了")
    # await manager.broadcast(f"用户{user}进入聊天室")

    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message(f"你说了: {data}", websocket)
            await manager.broadcast(f"用户:{user} 说: {data}")

    except WebSocketDisconnect:
        manager.disconnect(websocket)


#        await manager.broadcast(f"用户-{user}-离开")


@app.get("/sendmsg/{user}/{msg}")
async def sendmsg(user: str, msg: str):
    # await manager.connect(websocket)
    return await manager.broadcast(f"{user} : {msg}")
    # return "succeed"
    # try:
    #     while True:
    #         await manager.broadcast(f"{msg}")
    # except WebSocketDisconnect:
    #     manager.disconnect(websocket)


@app.post("/line/webhook")
async def echoBot(request: Request):
    signature = request.headers["X-Line-Signature"]
    body = await request.body()
    try:
        handler.handle(body.decode(), signature)

    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Missing Parameters")
    return "OK"


eventMessage = "地點｜HOOTERS美式餐廳 信義店  \n" +\
               "    📍 110台北市信義區松仁路58號14樓\n" + \
               "日期｜2023/01/13\n" + \
               "時間｜17:30 開放報到，18:00準時入場"

helpMessage = "輸入\"啤酒汽水大賽\"、\"撲克大賽\"、\"樂透\"、\"濾鏡\" 獲得資訊！或直接送出將你（記名）想跟大家的話發送到彈幕上！ \n"
beerMessage = "🍺🍻🍾啤酒汽水大賽 \n" + \
              "📌所有員工(正職、顧問、實習生、工讀生) \n" + \
              "💰預賽輪最多三輪，每輪取前三名頒發2000元(一人1000千) \n" + \
              "💰💰決賽輪，取預賽各輪前兩名晉級參加，總冠軍頒發3000元(一人1500元) \n"
pokerMessage = "♠️♥️♣️♦️撲克遊戲 \n" + \
               "📌所有員工(正職、顧問、實習生、工讀生) \n" + \
               "📌取積分最高六組 \n" + \
               "🥇第一名，組內每人獲得2000元 \n" + \
               "🥈第二名，組內每人獲得1000元 \n" + \
               "🥉第四到六名，組內每人獲得500元 \n"
lotteryMessage = "🎲🎰樂透抽獎資格 \n" + \
                 "正職員工(不含實習生、工讀生僅返還入場禮300元) \n" + \
                 "💵我要錢錢箱： \n" + \
                 "抽80名均分此箱獎池，保底一人獲得500元。 \n" + \
                 "另外抽出廠商贊助面額1000禮券，共抽8名；Galaxy Watch三星智慧型手錶，1名。 \n" + \
                 "🤑我全都要箱： \n" + \
                 "抽5名均分此箱獎池，依照投注金額及神秘加碼金額，上看20,000元。 \n" + \
                 "💸休單幾哩箱： \n" + \
                 "依照投入金額100%返還現金給同仁，1張還給大家100元。"

socialMedia = "尾牙資訊網 感謝iw James開發系統 \n" +\
              "https://ruten-party.glitch.me/info \n" +\
              "另外還有ux同事Rina設計主視覺及Abbie創意製作的社群濾鏡可以使用喔！也不妨按讚追蹤喔！ \n" + \
              "https://www.instagram.com/ar/3659533600994499/  \n" + \
              "https://www.facebook.com/fbcameraeffects/tryit/3659533600994499/"
flexMessage = FlexSendMessage(
    alt_text="歡迎光臨露天市集尾牙", contents=json.load(open('src/flex.json', 'r', encoding='utf-8'))
)


@handler.add(MessageEvent, message=(TextMessage))
def handling_message(event):
    replyToken = event.reply_token
    userid = event.source.user_id
    if isinstance(event.message, TextMessage):
        messages = event.message.text
        if messages == "活動資訊":
            line_bot_api.reply_message(reply_token=replyToken, messages=TextSendMessage(eventMessage))
            return
        if messages == "幫助" or messages == "help":
            line_bot_api.reply_message(reply_token=replyToken, messages=flexMessage)
            return
        if messages == "啤酒汽水大賽":
            line_bot_api.reply_message(reply_token=replyToken, messages=TextSendMessage(beerMessage))
            return
        if messages == "撲克大賽":
            line_bot_api.reply_message(reply_token=replyToken, messages=TextSendMessage(pokerMessage))
            return
        if messages == "樂透":
            line_bot_api.reply_message(reply_token=replyToken, messages=TextSendMessage(lotteryMessage))
            return
        if messages == "尾牙資訊網及社群濾鏡":
            line_bot_api.reply_message(reply_token=replyToken, messages=TextSendMessage(socialMedia))
            return
        if messages == "座位表":
            line_bot_api.reply_message(reply_token=replyToken,
                                       messages=ImageSendMessage(original_content_url="https://i.imgur.com/mRxLRUL.jpg",
                                                                 preview_image_url="https://i.imgur.com/mRxLRUL.jpg"))
            return
        else:
            asyncio.create_task(sendmsg(line_bot_api.get_profile(userid).display_name, messages))
            echoMessages = TextSendMessage(text="發送：" + messages + "成功")
            line_bot_api.reply_message(reply_token=replyToken, messages=(echoMessages))


@app.get("/demo")
async def demo():
    with open(os.path.join("class", "client1.html")) as fh:
        page = fh.read()
    return Response(content=page, media_type="text/html")


if __name__ == "__main__":
    import uvicorn

    # 官方推荐是用命令后启动 uvicorn main:app --host=127.0.0.1 --port=8010 --reload
    # uvicorn.run(app='main:app', host="127.0.0.1", port=8010, reload=True, debug=True)
    uvicorn.run(app='main:app', host="linebot.ycwww.dev", port=8010, ssl_keyfile="privkey.pem",
                ssl_certfile="fullchain.pem")
