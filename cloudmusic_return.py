import json
from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
import astrbot.api.message_components as Comp
from astrbot.api import logger
import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO


import ast
import re
import os


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



def create_song_card(info):
    output_path="song_card.jpg"
    # === 1. 确定字体路径（使用插件目录下的 1.ttf）===
    font_file = os.path.join(os.path.dirname(__file__), "1.ttf")
    if not os.path.exists(font_file):
        raise FileNotFoundError(f"字体文件缺失: {font_file}")
    
    try:
        font_big = ImageFont.truetype(font_file, 128)    # 歌名
        font_small = ImageFont.truetype(font_file, 64)  # 作者
    except OSError as e:
        raise RuntimeError(f"无法加载字体 {font_file}: {e}")

    # === 2. 下载封面并裁剪为 300x300 ===
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://music.163.com/"
    }
    resp = requests.get(info['cover_url'], headers=headers)
    resp.raise_for_status()
    cover = Image.open(BytesIO(resp.content)).convert("RGB")
    cover = make_square_thumbnail(cover, 300)

    # === 3. 创建 1200x300 画布 ===
    final_img = Image.new("RGB", (1200, 300), "white")
    final_img.paste(cover, (0, 0))

    # === 4. 绘制顶部对齐的文字 ===
    draw = ImageDraw.Draw(final_img)
    text_x = 320          # 封面右侧留 20px 间距
    top_margin = 32       # 距离顶部的空白

    song_y = top_margin
    author_y = song_y + 128 + 16  # 歌名字体 48pt，留 7px 间距（≈48+7=55）

    draw.text((text_x, song_y), info['song_name'], fill="black", font=font_big)
    draw.text((text_x, author_y), info['author'], fill="gray", font=font_small)

    # === 5. 保存 ===
    final_img.save(output_path, "JPEG", quality=90, optimize=True)
    return output_path


def make_square_thumbnail(image: Image.Image, size: int) -> Image.Image:
    """
    将任意图片裁剪为正方形缩略图（居中裁剪）
    """
    width, height = image.size
    if width > height:
        # 横向图：裁剪左右
        left = (width - height) // 2
        image = image.crop((left, 0, left + height, height))
    elif height > width:
        # 纵向图：裁剪上下
        top = (height - width) // 2
        image = image.crop((0, top, width, top + width))
    # 现在是正方形，缩放到目标尺寸
    return image.resize((size, size), Image.Resampling.LANCZOS)