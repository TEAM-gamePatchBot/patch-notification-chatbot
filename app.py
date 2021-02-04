from flask import Flask, request
import requests, json
import common.scraping as scraping
import os, boto3
from boto3.dynamodb.conditions import Key

import message


app = Flask(__name__)
FB_API_URL = "https://graph.facebook.com/v2.6/me/messages"

VERIFY_TOKEN = os.environ["VERIFY_TOKEN"]
PAGE_ACCESS_TOKEN = os.environ["PAGE_ACCESS_TOKEN"]

messenger = message.Messenger(os.environ["PAGE_ACCESS_TOKEN"])


def send_message(recipient_id, text):
    """Send a response to Facebook"""
    print(recipient_id, text)
    payload = {
        "message": {"text": text},
        "recipient": {"id": recipient_id},
        "notification_type": "regular",
    }

    auth = {"access_token": PAGE_ACCESS_TOKEN}

    response = requests.post(FB_API_URL, params=auth, json=payload)

    return response.json()


def get_bot_response(sender, message):
    """This is just a dummy function, returning a variation of what
    the user said. Replace this function with one connected to chatbot."""
    print(sender)
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table("gamePatchBot")
    table.put_item(
        Item={"dataType": "customer", "notification_id": int(sender),}
    )

    return "This is a dummy response to '{}'".format(message) + str(sender)


def verify_webhook(req):
    if req.args.get("hub.verify_token") == VERIFY_TOKEN:
        return req.args.get("hub.challenge")
    else:
        return "incorrect"


def respond(sender, message):
    """Formulate a response to the user and
    pass it on to a function that sends it."""
    response = get_bot_response(sender, message)
    send_message(sender, response)


def is_user_message(message):
    """Check if the message is a message from the user"""
    return (
        message.get("message")
        and message["message"].get("text")
        and not message["message"].get("is_echo")
    )


@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        if request.args.get("hub.verify_token") == VERIFY_TOKEN:
            if request.args.get("init") and request.args.get("init") == "true":
                messenger.init_bot()
                return ""
            return request.args.get("hub.challenge")
        raise ValueError("FB_VERIFY_TOKEN does not match.")
    elif request.method == "POST":
        print(request.get_json(force=True))
        messenger.handle(request.get_json(force=True))
    return ""


@app.route("/notification", methods=["POST"])
def notification():
    data = request.get_json()
    print(data)
    error = data["error"]
    patchList = data["patchList"]

    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table("gamePatchBot")

    patchContents = list(
        map(
            lambda patchId: table.get_item(Key={"dataType": "kart", "notification_id": patchId})[
                "Item"
            ],
            patchList,
        )
    )

    patchContents = list(
        map(
            lambda patch: "{}\n{}\n{}\n{}".format(
                patch["subject"], patch["patchTime"], "content", patch["thumbnail_src"]
            ),
            patchContents,
        )
    )

    # {
    #     "subject": " 1/28(목) 업데이트 안내",
    #     "content": {
    #         "patch_list": [
    #             {
    #                 "patch_subject": "1. 시즌 패스 시즌 4가 오픈됩니다.",
    #                 "patch_content": ["▶ 시즌 패스 시즌 4 오픈", "▶ 시즌 패스 시즌 4 관련 아이템 판매"],
    #             },
    #             {"patch_subject": "2. 스노우 모빌-R이 출시됩니다.", "patch_content": ["▶ 스노우 모빌-R이 판매됩니다."]},
    #             {
    #                 "patch_subject": "3. 다양한 이벤트가 진행됩니다.",
    #                 "patch_content": ["▶ 겨울 맞이 아이템 복불복", "▶ 기다리면 열리는 상자가 오픈됩니다."],
    #             },
    #             {
    #                 "patch_subject": "4. 다양한 퀘스트가 진행됩니다.",
    #                 "patch_content": [
    #                     "▶ 시즌  패스 시즌 4 OPEN (하루 한 번만 완료 가능)",
    #                     "▶ 눈사람 요정 케로의 마법 (하루 한 번만 완료 가능)",
    #                 ],
    #             },
    #             {"patch_subject": "5. 기타 시스템 변경사항", "patch_content": ["▶ 네이버 채널링 서비스 종료"]},
    #         ]
    #     },
    #     "date": "2021-01-27",
    #     "dataType": "kart",
    #     "notification_id": Decimal("75190"),
    #     "patchTime": "2021년 1월 28일(목) 오전 0시",
    #     "thumbnail_src": "https://file.nexon.com/NxFile/Download/FileDownloader.aspx?oidFile=4908963554209564999",
    # }

    customerIdList = table.query(KeyConditionExpression=Key("dataType").eq("customer"))["Items"]
    results = []
    for patch in patchContents:
        result = list(
            map(
                lambda customer: send_message(int(customer["notification_id"]), patch),
                customerIdList,
            )
        )
        results.append(result)

    return results


@app.route("/army", methods=["POST"])
def armyBot():
    data = request.get_json()
    print(data)
    me = data["id"]
    text = data["text"]
    people = int(text.split(":")[0])
    print(people)
    if people < 10:
        message = "지금 sw개발병의 경쟁률 {}으로 적은 편! 화이팅~".format(text)
    elif people < 20:
        message = "지금 sw개발병의 경쟁률 {}으로 쵸금 많은 편! 쫄지마 동진아!".format(text)
    elif people < 30:
        message = "지금 sw개발병의 경쟁률 {}으로 많은 편! 후...무섭다 무서워".format(text)
    elif people < 40:
        message = "지금 sw개발병의 경쟁률 {}으로 대박스! 마음을 좀 비워...".format(text)
    elif people >= 40:
        message = "지금 sw개발병의 경쟁률 {}으로 미쳐가는 중!".format(text)
    send_message(me, message)
    return {"statusCode": 200}


@app.route("/")
def hello():
    return "running"


if __name__ == "__main__":
    app.run(threaded=True, port=5000)
