import os
import requests
import json
import logging
import schedule
import time
from mastodon import Mastodon
#from my_timer import RepeatedTimer
# V1.0.2

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
# 参数筛选：动画、漫画、游戏、文学、影视、诗词、哲学
para = "?c=a&c=b&c=c&c=d&c=h&c=i&c=k&encode=json&charset=utf-8&max_length=128"
request_url = link + para
# def special list
special_list = ['e', 'f', 'l', 'g'] # 原创/网络/抖机灵/其它
# account
BOT_ACCOUNT = 'youdangls+hitokoto@gmail.com'
BOT_PASSWD = os.getenv("HITOKOTO_PASSWD", "")

def make_cred_secret():
    Mastodon.create_app(
        'hitokoto bot',
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
    logger.info(from_type)

    from_list = []
    if provenance is not None:
        from_list.append("《" + provenance + "》")
    if writer is not None:
        from_list.append(writer)
    from_text = '·'.join(from_list)
    
    if from_text is not None:
        msg = sentence + "\n\n——" + from_text
    else:
        msg = sentence
    return msg

def post_msg(msg):
    # To post, create an actual API instance.
    mastodon = Mastodon(
        access_token = 'pytooter_usercred.secret',
        api_base_url = mstd_website
    )
    response = mastodon.status_post(msg, visibility="public")
    print(">> msg sent")
    return response

def periodic_task():
    for i in range(3):
        try:
            hitokoto = get_hitokoto(request_url)
            data = json.loads(hitokoto.decode('utf-8'))
            msg = parse_hitokoto(data)
            post_msg(msg)
        except:
            print("periodic_task fail ", i)
            logger.exception("periodic_task fail " + str(i))
        else:
            break


schedule.every().day.at("09:00").do(periodic_task)
schedule.every().day.at("13:00").do(periodic_task)
schedule.every().day.at("15:00").do(periodic_task)
schedule.every().day.at("17:00").do(periodic_task)
schedule.every().day.at("19:00").do(periodic_task)
schedule.every().day.at("23:00").do(periodic_task)

if __name__ == "__main__":
    make_cred_secret()
    #rt = RepeatedTimer(3600, periodic_task) # it auto-starts, no need of rt.start()
    print("periodic_task start!")
    while True:
        schedule.run_pending()
        time.sleep(60)