import os
import logging
import schedule
import time
from datetime import datetime, timezone
from mastodon import Mastodon, MastodonIllegalArgumentError

# V0.1.0

# init logger
logger = logging.getLogger("good_night_bot")
logger.setLevel(level=logging.DEBUG)
handler = logging.FileHandler('good_night_bot.log')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# def website
mstd_website = 'https://utopia.cool'

# default music path
FILE_PATH = os.getenv("NIGHT_BOT_FILE", "/home/bot/music")

# account
BOT_ACCOUNT = os.getenv("NIGHT_EMAIL", "")
BOT_PASSWD = os.getenv("NIGHT_PASSWD", "")

def make_cred_secret():
    Mastodon.create_app(
        'good night',
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

def post_msg(text, media, schedule_time):
    # To post, create an actual API instance.
    mastodon = Mastodon(
        access_token = 'pytooter_usercred.secret',
        api_base_url = mstd_website
    )
    media_dict = mastodon.media_post(media)
    response = mastodon.status_post(text, media_ids=media_dict, visibility="public", scheduled_at=schedule_time)
    # 测试时可用 direct 发送私信给自己的账号:
    # response = mastodon.status_post("@twisted " + text, media_ids=media_dict, visibility="direct", scheduled_at=schedule_time)
    return response

def periodic_task():
    # 这里似乎是UTC时间，不能直接用东8区时间。所以22:22的推送要减去8小时
    # 不同服务器可能不一样，要测一下
    schedule_time = datetime.today().replace(hour=14, minute=22, second=0, microsecond=0)
    schedule_time = schedule_time.replace(tzinfo=timezone.utc)
    try:
        name, writer, music = get_music_info()
    except:
        send_error_msg("找不到介绍文字")
        return
    msg_text = get_msg_text(name, writer)
    try:
        music_file = get_music_path(music)
    except:
        send_error_msg("找不到音乐文件")
        return
    
    for i in range(3): # 考虑网络不稳定的情况，try 3次
        try:
            response = post_msg(msg_text, music_file, schedule_time)
            print('scheduled_at:', response['scheduled_at'])
        except:
            print(i, "try failed")
            logger.exception("periodic_task fail " + str(i))
        else:
            logger.info(get_date_str() + ' post done!')
            clear_old_file(music_file)
            print("post finish, files cleared")
            break
        if i == 2:
            send_error_msg("文件及介绍无误，但发送失败")
    
def get_date():
    d = datetime.today()
    return d.year, d.month, d.day

def get_date_str(separator='-'):
    assert(isinstance(separator, str))
    num = get_date()
    day_str = separator.join(map(str, num))
    return day_str

def get_music_path(file_name):
    music_file_path = os.path.join(FILE_PATH, file_name)
    if not os.path.isfile(music_file_path):
        raise IOError("没有找到今日音乐文件")
    return music_file_path

def get_music_info():
    file_name = get_date_str() + '.txt'
    info_file_path = os.path.join(FILE_PATH, file_name)
    if not os.path.isfile(info_file_path):
        raise IOError("没有找到今日info文件")
    with open(info_file_path,'rU',encoding="utf-8") as f:
        info = f.readlines()
        name = info[0].strip(os.linesep)
        writer = info[1].strip(os.linesep)
        music = info[2].strip(os.linesep)
    return name, writer, music

def get_msg_text(name, writer):
    text = get_date_str('/')
    text += "\n\n歌曲：" + name + "\n艺术家：" + writer
    # print(text)
    return text

def send_error_msg(text):
    print(text)
    # To post, create an actual API instance.
    mastodon = Mastodon(
        access_token = 'pytooter_usercred.secret',
        api_base_url = mstd_website
    )
    msg = "@twisted @5432688 " + get_date_str() + '\n' + text
    response = mastodon.status_post(msg, visibility="direct")
    return response

def remove_file(file):
    if os.path.exists(file):
        os.remove(file)
    else:
        print("The file does not exist",file)
        logger.info('remove file dosnt exist: ' + file)

def clear_old_file(music_file_path):
    file_name = get_date_str() + '.txt'
    info_file_path = os.path.join(FILE_PATH, file_name)

    remove_file(music_file_path)
    remove_file(info_file_path)

schedule.every().day.at("19:00").do(periodic_task)


if __name__ == "__main__":
    make_cred_secret()
    print("periodic_task start!")
    while True:
        schedule.run_pending()
        time.sleep(60)
    print("finish")