import json
from dataclasses import dataclass

import requests
from flask import Flask, jsonify, request
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    PushMessageRequest,
    TextMessage,
)


@dataclass
class AppConfig:
    line_channel_access_token: str
    line_channel_secret: str
    user_id: str


LLMS_HOST = "http://localhost:8000"
app: Flask


def setup_app():
    access_token = input("input LINE channel access token:")
    assert (len(access_token) != 0)
    secret = input("input LINE channel secret:")
    assert (len(secret) != 0)
    print(f"open {LLMS_HOST}/login and input the code")
    code = input("code:")
    assert (len(code) != 0)

    auth_collect = requests.post(f"{LLMS_HOST}/api/v1/auth/collect", json={"code": code})
    session_id = auth_collect.json()["session"]
    profile = requests.get(f"{LLMS_HOST}/api/v1/sessions/{session_id}/")
    print(profile.json())

    with open('config.json', 'w') as fp:
        json.dump({
            "access_token": access_token,
            "secret": secret,
            "user_id": profile.json()["user_id"],
        }, fp=fp)

    print("done")


def serve_app(config: AppConfig):
    app = Flask(__name__)
    app.config["DEBUG"] = True

    configuration = Configuration(access_token=config.line_channel_access_token)

    @app.route('/', methods=['GET'])
    def index():
        return jsonify({"message": "ok"})

    @app.route('/text', methods=['POST'])
    def text():
        data = request.get_json()
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            result = line_bot_api.push_message(PushMessageRequest(
                to=config.user_id,
                messages=[TextMessage(
                    text=data["message"].trim()
                )]
            ))
        return jsonify({"message": "ok", "result": result.sent_messages[0].__dict__})

    app.run(host="0.0.0.0", port=8001)


def load_config() -> AppConfig:
    with open("config.json", "r") as fp:
        config = json.load(fp)
        return AppConfig(
            line_channel_access_token=config["access_token"],
            line_channel_secret=config["secret"],
            user_id=config["user_id"]
        )


if __name__ == "__main__":
    app_config: AppConfig | None = None

    try:
        app_config = load_config()
    except Exception as e:
        setup_app()
        exit(0)

    serve_app(app_config)