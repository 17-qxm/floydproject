
import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from io import BytesIO
from datetime import date, datetime, timedelta
import linecache

import ast
import re
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))

def extract_music_info_from_str(data_str):
    """
    从完整的消息对象字符串中提取网易云音乐分享信息
    适配包含Group/MessageMember/Event等自定义对象的完整字符串
    
    Args:
        data_str: 完整的消息对象字符串
    
    Returns:
        dict: 包含song_name, cover_url, author, music_url的字典，提取失败返回None
    """
    # 方案3：终极备用 - 直接匹配关键字段
    # 匹配歌曲名
    song_name_match = re.search(r"'title':\s*'([^']+)'", data_str)

    if not song_name_match:
        return {
            'isitok': 'no'
        }
    else:

        song_name = song_name_match.group(1)
        # 匹配封面
        cover_match = re.search(r"'preview':\s*'([^']+)'", data_str)
        cover_url = cover_match.group(1)
        
        # 匹配作者
        author_match = re.search(r"'desc':\s*'([^']+)'", data_str)
        author = author_match.group(1)
    
        return {
            'isitok': 'yes',
            'song_name': song_name,
            'cover_url': cover_url,
            'author': author
        }



def create_song_card(chain_data) -> Image.Image:
    # 尺寸 - 2倍放大：300*2=600, 100*2=200, 25*2=50
    w, h_top, h_bot = 800, 200, 50  # 总高250(200+50)
    img = Image.new("RGB", (w, h_top + h_bot), "white")
    draw = ImageDraw.Draw(img)

    # 字体 - 2倍放大
    font_path = os.path.join(current_dir, "1.ttf")
    font_large = ImageFont.truetype(font_path, 48)  # 32*2=64
    font_small = ImageFont.truetype(font_path, 36)  # 24*2=48
    font_tiny = ImageFont.truetype(font_path, 24)   # 12*2=24

    # 歌曲封面 - 2倍放大
    cover = Image.open(BytesIO(requests.get(
        str(chain_data["cover_url"])
    ).content)).convert("RGB").resize((200, 200), 1)  # 100*2=200
    img.paste(cover, (0, 0))

    # 歌名 - 2倍位置
    txt = str(chain_data["song_name"])
    bbox = draw.textbbox((0, 0), txt, font=font_large)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text((200 + 32, 100 - th - 16), txt, fill="black", font=font_large)  # 16*2=32, 8*2=16
    
    # 作者 - 2倍位置
    author = str(chain_data["author"])
    bbox = draw.textbbox((0, 0), author, font=font_small)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text((200 + 32, 100 + 16), author, fill="gray", font=font_small)  # 8*2=16

    # 推荐人背景（模糊 + 遮罩）
    sender_id = str(chain_data['sender_id'])
    avatar_url = f"https://q.qlogo.cn/g?b=qq&nk={ sender_id }&s=640"
    bg = Image.open(BytesIO(requests.get(avatar_url).content)).convert("RGB").resize((w, h_bot), 1)
    blurred = bg.filter(ImageFilter.GaussianBlur(radius=5))
    overlay = Image.new("RGBA", (w, h_bot), (0, 0, 0, 61))
    composited = Image.alpha_composite(blurred.convert("RGBA"), overlay).convert("RGB")
    img.paste(composited, (0, h_top))

    # 底部文字和头像
    draw_bottom = ImageDraw.Draw(img)
    draw_bottom.text((10, h_top + 8), "推荐人:", fill="white", font=font_tiny, 
                     stroke_width=2, stroke_fill="black")  # 5*2=10, 4*2=8

    # 圆形头像 - 2倍放大
    avatar = Image.open(BytesIO(requests.get(avatar_url).content)).convert("RGB").resize((40, 40), 1)  # 20*2=40
    mask = Image.new("L", (40, 40), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, 40, 40), fill=255)
    avatar.putalpha(mask)
    img.paste(avatar, (120, h_top + 4), avatar)  # 60*2=120, 2*2=4

    draw_bottom.text((170, h_top + 8), str(chain_data["sender_name"]), fill="white", font=font_tiny, 
                     stroke_width=2, stroke_fill="black")  # 85*2=170

    return img


def push_song_daily():
    nowtime = date.today()
    day_pass = nowtime - date(2026, 1, 10)
    int_day_pass = day_pass.days + 17
    txt_path = os.path.join(current_dir, "song_push.txt")
    line_content = linecache.getline(txt_path, int_day_pass)

    return str(line_content)

def calculate_sleep_time(self):
        """计算到下一次推送时间的秒数"""
        now = datetime.now()
        hour, minute = map(int, self.push_time.split(":"))

        tomorrow = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if tomorrow <= now:
            tomorrow += timedelta(days=1)

        seconds = (tomorrow - now).total_seconds()
        return seconds

