import sys
import os
import importlib
import traceback

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

import cloudmusic_return
importlib.reload(cloudmusic_return)
from cloudmusic_return import extract_music_info_from_str, create_song_card, push_song_daily, calculate_sleep_time
import xibao
importlib.reload(xibao)
from xibao import generate_image

import asyncio
from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.core.message.message_event_result import MessageChain
from astrbot.api.star import Context, Star, register
import astrbot.api.message_components as Comp
from astrbot.api.message_components import Plain, Image
from astrbot.api import logger

@register("floyd_project", "17qxm", "一个简单的 Hello World 插件", "0.0.1")
class MyPlugin(Star):
    def __init__(self, context: Context, config: dict):
        super().__init__(context)
        self.push_group = config.get('push_group', '')
        self.push_time = config.get("push_time", "08:00")
        self.debug_use = config.get("debug_use", True)
        self._daily_task = asyncio.create_task(self.daily_task())

    async def initialize(self):
        """可选择实现异步的插件初始化方法，当实例化该插件类之后会自动调用该方法。"""

    async def daily_task(self):
        """定时推送任务"""
        while True:
            try:
                # 计算到下次推送的时间
                sleep_time = calculate_sleep_time(self)
                logger.info(f"[每日新闻] 下次推送将在 {int(sleep_time)} 秒后")

                # 等待到设定时间
                await asyncio.sleep(sleep_time)

                # 推送新闻
                a = str(self.push_group)
                message_chain = MessageChain().message(push_song_daily().rstrip())
                await self.context.send_message(f"Floyd:GroupMessage:{self.push_group}", message_chain)

                # 再等待一段时间，避免重复推送
                await asyncio.sleep(60)
            except Exception as e:
                logger.error(f"[每日新闻] 定时任务出错: {e}")
                traceback.print_exc()
                await asyncio.sleep(300)


    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
    async def on_all_message(self, event: AstrMessageEvent):
        """处理群聊信息，如果群聊信息为音乐分享则处理音乐分享"""
        if event.get_group_id() == str(self.push_group) or event.get_group_id() == "833512627" or event.get_group_id() == "959826262":
            data = str(event.message_obj)
            if event.get_message_outline().rstrip() != "[ComponentType.Json]":
                """TODO"""
                logger.error("Is not a music share card")
            else:
                chain_data = extract_music_info_from_str(data)
                if chain_data.get('isitok') == 'no':
                    """yield event.plain_result("Is not a music share card")"""
                else:
                    chain_data['sender_id'] = event.get_sender_id()
                    chain_data['sender_name'] = event.get_sender_name()
                
                    output_card = create_song_card(chain_data)
                    output_card.save("main.png")
                    yield event.image_result("main.png")
        if self.debug_use == True:
            if event.get_group_id() == "833512627":
                user_name = event.get_sender_id()
                message_obj = event.message_obj # 用户发的纯文本消息字符串
                umo = event.unified_msg_origin
                yield event.plain_result(f"Hello, {user_name}, 你发了信息在{umo}\u200b\n消息类型为{event.get_message_outline()}\u200b\n消息内容为:\u200b\n{message_obj}") # 发送一条纯文本消息
        

    @filter.command("forcepush")
    async def forcepush_launcher(self, event: AstrMessageEvent):
        """强制推歌挑战发送，在bug发生时"""
        
        yield event.plain_result(push_song_daily().rstrip())
    
    @filter.command("喜报")
    async def xibao(self, event: AstrMessageEvent, textinput: str):
        """发送喜报"""
        if len(textinput) >= 20:
            yield event.plain_result("字数太多啦！长度应在 20 个字符以内。")
        elif len(textinput) < 10:
            size = 250 - len(textinput) * 8
        elif 15 < len(textinput) < 20:
            size = 250 - len(textinput) * 9
        else:
            size = 250 - len(textinput) * 10
        x = generate_image("xibao_bg.png", textinput, size, "red", stroke="yellow")
        x.save("bao.png")
        yield event.image_result("bao.png")
    
    @filter.command("悲报")
    async def beibao(self, event: AstrMessageEvent, textinput: str):
        """发送悲报"""
        if len(textinput) >= 20:
            yield event.plain_result("字数太多啦！长度应在 20 个字符以内。")
        elif len(textinput) < 10:
            size = 250 - len(textinput) * 8
        elif 15 < len(textinput) < 20:
            size = 250 - len(textinput) * 9
        else:
            size = 250 - len(textinput) * 10
        b = generate_image("beibao_bg.png", textinput, size, "black", stroke="white")
        b.save("bao.png")
        yield event.image_result("bao.png")

    # 注册指令的装饰器。指令名为 helloworld。注册成功后，发送 `/helloworld` 就会触发这个指令，并回复 `你好, {user_name}!`
    @filter.command("helloworld")
    async def helloworld(self, event: AstrMessageEvent):
        """这是一个 hello world 指令""" # 这是 handler 的描述，将会被解析方便用户了解插件内容。建议填写。
        user_name = event.get_sender_id()
        message_obj = event.message_obj # 用户发的纯文本消息字符串
        message_chain = event.get_messages() # 用户所发的消息的消息链 # from astrbot.api.message_components import *
        umo = event.unified_msg_origin
        logger.info(message_chain)
        yield event.plain_result(f"Hello, {user_name}, 你发了信息在{umo}\u200b\n消息类型为{event.get_message_outline()}\u200b\n消息内容为:\u200b\n{message_obj}") # 发送一条纯文本消息

    async def terminate(self):
        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""
