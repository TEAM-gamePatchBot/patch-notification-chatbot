from boto3.dynamodb.conditions import Key
import boto3
from fbmessenger import BaseMessenger, MessengerClient
from fbmessenger.templates import GenericTemplate, OneTimeNotifTemplate
from fbmessenger.elements import Text, Button, Element
from fbmessenger import quick_replies
from fbmessenger.attachments import Image, Video
from fbmessenger.thread_settings import (
    GreetingText,
    GetStartedButton,
    PersistentMenuItem,
    PersistentMenu,
)


def get_element(title, subtitle, image_url, item_url):
    return Element(
        title=title,
        subtitle=subtitle,
        image_url=image_url,
        item_url=f"https://kart.nexon.com/Kart/News/Patch/view.aspx?n4articlesn={item_url}",
    )


def make_qrs_set():
    qr1 = quick_replies.QuickReply(title="최신 패치 내역", payload="PATCH_LIST_PAYLOAD")
    qr2 = quick_replies.QuickReply(title="최신 패치 내역 링크", payload="PATCH_LINK_PAYLOAD")
    qr3 = quick_replies.QuickReply(title="기능 설명", payload="FUNC_DESC_PAYLOAD")
    qr4 = quick_replies.QuickReply(title="알림 설정", payload="OTN_PAYLOAD")
    return quick_replies.QuickReplies(quick_replies=[qr1, qr2, qr3, qr4])


def save_customer_data(sender, otn_token):
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table("gamePatchBot")
    table.put_item(
        Item={"dataType": "customer", "notification_id": int(otn_token),}
    )


def get_recent_patch():
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table("gamePatchBot")
    data = table.query(
        KeyConditionExpression=Key("dataType").eq("kart"), ScanIndexForward=False, Limit=1
    )["Items"][0]
    return data


def make_text_from_data(data):
    text = ""
    text += data["subject"] + "\n"
    text += "업데이트 일정: " + data["patchTime"] + "\n\n"

    patchContents = list(
        map(
            lambda patch: patch["patch_subject"] + "\n\t" + "\n\t".join(patch["patch_content"]),
            data["content"]["patch_list"],
        )
    )
    text += "\n\n".join(patchContents)
    return text


def process_message(message):
    print(message)

    qrs = make_qrs_set()

    if "text" in message["message"]:
        msg = message["message"]["text"]
        if msg == "최신 패치 내역":
            # DB에서 패치 내역 불러와서 contents 처럼 한 str로 처리해주면 됨
            recentData = get_recent_patch()
            contents = make_text_from_data(recentData)
            response = Text(text=contents, quick_replies=qrs)
        elif msg == "최신 패치 내역 링크":
            recentData = get_recent_patch()
            # DB에서 title, subtitle, image_url, item_url(게시글 id 만 가져오면 됨)
            elem = get_element(
                recentData["subject"],
                recentData["date"],
                recentData["thumbnail_src"],
                recentData["notification_id"],
            )
            response = GenericTemplate(elements=[elem], quick_replies=qrs)
        elif msg == "기능 설명":
            contents = "입력창 위의 버튼을 눌러\n⚡최신 패치 내역⚡을 보거나\n📢카트라이더 패치 안내 게시판📢으로 이동할 수 있습니다😍"
            response = Text(text=contents, quick_replies=qrs)
        elif msg == "알림 설정":
            title="매주 목요일 알림을 받으세요!"
            payload="OTN_PAYLOAD"
            response = OneTimeNotifTemplate(title, payload)
        else:
            contents = "버튼을 눌러 내용을 확인해주세요!😊"
            response = Text(text=contents, quick_replies=qrs)
    return response.to_dict()


def process_optin(message):
    qrs = make_qrs_set()
    contents = "감사합니다!"
    response = Text(text=contents, quick_replies=qrs)
    return response.to_dict()


class Messenger(BaseMessenger):
    def __init__(self, page_access_token):
        self.page_access_token = page_access_token
        super(Messenger, self).__init__(self.page_access_token)
        self.client = MessengerClient(self.page_access_token)

    def message(self, message):
        action = process_message(message)
        res = self.send(action, "RESPONSE")

    def init_bot(self):
        self.add_whitelisted_domains("https://facebook.com/")
        greeting = GreetingText(text="카트라이더 패치 내역에 관한 알림을 받으세요!")
        self.set_messenger_profile(greeting.to_dict())

        get_started = GetStartedButton(payload="start")
        res = self.set_messenger_profile(get_started.to_dict())

    def delivery(self, message):
        pass

    def read(self, message):
        pass

    def account_linking(self, message):
        pass

    def postback(self, message):
        payload = message["postback"]["payload"]
        if "start" in payload:
            txt = "안녕하세요~!"
            self.send({"text": txt}, "RESPONSE")

    def optin(self, message):
        sender = message['sender']['id']
        otn_token = message['optin']['one_time_notif_token']
        print(otn_token)
        save_customer_data(sender, otn_token)
        action = process_optin(message)
        res = self.send(action, 'RESPONSE')
        app.logger.debug('Response: {}'.format(res))
