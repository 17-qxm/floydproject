import sys
import os
import importlib

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

import cloudmusic_return
importlib.reload(cloudmusic_return)
from cloudmusic_return import extract_music_info_from_str, create_song_card

import json
from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
import astrbot.api.message_components as Comp
from astrbot.api import logger

@register("floyd_project", "17qxm", "一个简单的 Hello World 插件", "0.0.1")
class MyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    async def initialize(self):
        """可选择实现异步的插件初始化方法，当实例化该插件类之后会自动调用该方法。"""

    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
    async def on_all_message(self, event: AstrMessageEvent):
        """处理群聊信息，如果群聊信息为音乐分享则处理音乐分享"""
        if event.get_group_id() == "833512627":
            data = str(event.message_obj)
            chain_data = extract_music_info_from_str(data)
            if chain_data.get('isitok') == 'no':
                yield event.plain_result("Is not a music share card")
            else:
                output_card_path = create_song_card(chain_data)

                yield event.image_result(output_card_path)
            



    # 注册指令的装饰器。指令名为 helloworld。注册成功后，发送 `/helloworld` 就会触发这个指令，并回复 `你好, {user_name}!`
    @filter.command("helloworld")
    async def helloworld(self, event: AstrMessageEvent):
        """这是一个 hello world 指令""" # 这是 handler 的描述，将会被解析方便用户了解插件内容。建议填写。
        user_name = event.get_sender_id()
        message_obj = event.message_obj # 用户发的纯文本消息字符串
        message_chain = event.get_messages() # 用户所发的消息的消息链 # from astrbot.api.message_components import *
        logger.info(message_chain)
        yield event.plain_result(f"Hello, {user_name}, 你发了如下信息: \n {message_obj}") # 发送一条纯文本消息

    async def terminate(self):
        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""
