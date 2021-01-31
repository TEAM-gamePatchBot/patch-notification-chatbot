from flask import Flask, request
import requests, json
import common.scraping as scraping
import os, boto3
from boto3.dynamodb.conditions import Key

# with open("config.json", "r") as f:
#    config = json.load(f)

app = Flask(__name__)
FB_API_URL = "https://graph.facebook.com/v2.6/me/messages"
# VERIFY_TOKEN = config["TOKEN"]["VERIFY_TOKEN"]
# PAGE_ACCESS_TOKEN = config["TOKEN"]["PAGE_ACCESS_TOKEN"]

VERIFY_TOKEN = os.environ["VERIFY_TOKEN"]
PAGE_ACCESS_TOKEN = os.environ["PAGE_ACCESS_TOKEN"]


def send_message(recipient_id, text):
    """Send a response to Facebook"""
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


@app.route("/webhook", methods=["GET"])
def listen():
    """This is the main function flask uses to
    listen at the `/webhook` endpoint"""
    if request.method == "GET":
        return verify_webhook(request)


@app.route("/webhook", methods=["POST"])
def talk():
    payload = request.get_json()
    event = payload["entry"][0]["messaging"]
    for x in event:
        if is_user_message(x):
            text = x["message"]["text"]
            sender_id = x["sender"]["id"]
            respond(sender_id, text)

    return "ok"


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


@app.route("/")
def hello():
    return "hello"


if __name__ == "__main__":
    app.run(threaded=True, port=5000)
