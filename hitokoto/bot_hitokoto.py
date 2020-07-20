import os
import requests
import json
import logging
from mastodon import Mastodon
from my_timer import RepeatedTimer

# init logger
logger = logging.getLogger("hitokoto_bot")
logger.setLevel(level=logging.DEBUG)
handler = logging.FileHandler('hitokoto_bot.log')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# def website
mstd_website = 'https://utopia.cool'
# def link
link = 'https://v1.hitokoto.cn'
para = "?encode=json&charset=utf-8&max_length=128"
request_url = link + para
# def special list
special_list = ['e', 'f', 'l', 'g'] # 原创/网络/抖机灵/其它
# account
BOT_ACCOUNT = 'youdangls+hitokoto@gmail.com'
BOT_PASSWD = os.getenv("HITOKOTO_PASSWD", "")

def make_cred_secret():
    Mastodon.create_app(
        'pytooterapp',
        api_base_url = mstd_website,
        to_file = 'pytooter_clientcred.secret'
    )
    mastodon = Mastodon(
        client_id = 'pytooter_clientcred.secret',
        api_base_url = mstd_website
    )
    mastodon.log_in(
        BOT_ACCOUNT,
        BOT_PASSWD,
        to_file = 'pytooter_usercred.secret'
    )

def get_hitokoto(url):
    try:
        r = requests.get(url)
    except requests.exceptions.RequestException as err:
        print(err)
        logger.exception('get_hitokoto Error')
        return None
    return r.content

def parse_hitokoto(data):
    provenance, sentence, writer = data['from'], data['hitokoto'], data['from_who']
    from_type = data['type']

    from_text = ""
    if from_type in special_list:
        if provenance is not None:
            from_text += provenance
        if writer is not None:
            from_text += writer
    else:
        if provenance is not None:
            from_text += '《' + provenance + '》'
        if writer is not None:
            from_text += writer
    
    if len(from_text) > 0:
        msg = sentence + "\n\n——" + from_text
    else:
        msg = sentence
    #print(msg)
    return msg

def post_msg(msg):
    # To post, create an actual API instance.
    mastodon = Mastodon(
        access_token = 'pytooter_usercred.secret',
        api_base_url = mstd_website
    )
    response = mastodon.status_post(msg, visibility="private")
    return response

def every_hour_task():
    hitokoto = get_hitokoto(request_url)
    data = json.loads(hitokoto)
    #print(data)
    msg = parse_hitokoto(data)
    post_msg(msg)

if __name__ == "__main__":
    make_cred_secret()
    rt = RepeatedTimer(3600, every_hour_task) # it auto-starts, no need of rt.start()
    print("every_hour_task start!")