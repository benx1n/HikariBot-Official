import asyncio
import os
import platform
import re
import sys
import traceback
from collections import defaultdict, namedtuple

import httpx
from hikari_core import callback_hikari, init_hikari, set_hikari_config
from hikari_core.data_source import __version__
from hikari_core.game.help import check_version
from hikari_core.model import Hikari_Model
from hikari_core.moudle.wws_real_game import (
    add_listen_list,
    delete_listen_list,
    get_diff_ship,
    get_listen_list,
)
from nonebot import get_driver, on_command, on_fullmatch, on_message, require
from nonebot.adapters.qq import ActionFailed, Bot, Message, MessageEvent, MessageSegment
from nonebot.log import logger
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER

from .data_source import dir_path, nb2_file, template_path
from .game.ocr import (
    downlod_OcrResult,
    get_Random_Ocr_Pic,
    pic2txt_byOCR,
    upload_OcrResult,
)
from .game.pupu import get_pupu_msg
from .utils import DailyNumberLimiter, FreqLimiter, download, get_bot, upload_oss

scheduler = require('nonebot_plugin_apscheduler').scheduler

_max = 100
EXCEED_NOTICE = f'您今天已经冲过{_max}次了，请明早5点后再来！'
is_first_run = True
_nlmt = DailyNumberLimiter(_max)
_flmt = FreqLimiter(3)
__bot_version__ = '1.0.2.1'

test = on_command('test', priority=4, block=True)
bot_get_random_pic = on_command('wws 随机表情包', block=True, priority=5)
bot_update = on_command('wws 更新Hikari', priority=5, block=True, permission=SUPERUSER)
wws = on_command('wws', block=False, aliases={'WWS'}, priority=1)
bot_pupu = on_command('噗噗', block=False, priority=5)
bot_listen = on_message(priority=5, block=False)
driver = get_driver()

_proxy = None
if driver.config.proxy_on:
    _proxy = driver.config.proxy

set_hikari_config(
    use_broswer=driver.config.htmlrender_browser,
    http2=driver.config.http2,
    proxy=_proxy,
    token=driver.config.api_token,
    game_path=str(dir_path / 'game'),
)

SlectState = namedtuple('SlectState', ['state', 'SlectIndex', 'SelectList'])
SecletProcess = defaultdict(lambda: SlectState(False, None, None))


@test.handle()
async def handle_first_receive(event: MessageEvent):
    print(event)
    print(event.get_user_id())
    print(event.get_message())
    print(event.get_type())
    print(event.get_session_id())
    await test.send('收到消息')


@wws.handle()
async def main(ev: MessageEvent, matchmsg: Message = CommandArg()):  # noqa: B008
    try:
        print(matchmsg)
        server_type = 'QQ_OFFICIAL'
        qqid = ev.get_user_id()
        group_id = None
        if not _nlmt.check(qqid):
            await wws.send(EXCEED_NOTICE, at_sender=True)
            return False
        if not _flmt.check(qqid):
            await wws.send('您冲得太快了，请稍候再冲', at_sender=True)
            return False
        _flmt.start_cd(qqid)
        _nlmt.increase(qqid)
        hikari = await init_hikari(
            platform=server_type,
            PlatformId=str(qqid),
            command_text=str(matchmsg),
            GroupId=group_id,
            Ignore_List=[
                add_listen_list,
                delete_listen_list,
                get_diff_ship,
                get_listen_list,
            ],
        )
        if hikari.Status == 'success':
            if isinstance(hikari.Output.Data, bytes):
                url = await upload_oss(hikari.Output.Data)
                logger.success(url)
                await wws.send(MessageSegment.image(url))
            elif isinstance(hikari.Output.Data, str):
                await wws.send(hikari.Output.Data)
        elif hikari.Status == 'wait':
            url = await upload_oss(hikari.Output.Data)
            logger.success(url)
            await wws.send(MessageSegment.image(url))
            hikari = await wait_to_select(hikari)
            if hikari.Status == 'error':
                await wws.send(str(hikari.Output.Data))
                return
            hikari = await callback_hikari(hikari)
            if isinstance(hikari.Output.Data, bytes):
                url = await upload_oss(hikari.Output.Data)
                logger.success(url)
                await wws.send(MessageSegment.image(url))
            elif isinstance(hikari.Output.Data, str):
                await wws.send(str(hikari.Output.Data))
        else:
            await wws.send(str(hikari.Output.Data))
    except ActionFailed:
        logger.warning(traceback.format_exc())
        try:
            await wws.send('发不出图片，可能被风控了QAQ')
            return True
        except Exception:
            pass
        return False
    except Exception:
        logger.error(traceback.format_exc())
        await wws.send('呜呜呜发生了错误，可能是网络问题，如果过段时间不能恢复请联系麻麻哦~')


@bot_listen.handle()
async def change_select_state(ev: MessageEvent):
    try:
        msg = str(ev.get_message()).strip()
        qqid = str(ev.get_user_id())
        print(msg, qqid)
        if SecletProcess[qqid].state and str(msg).isdigit():
            if int(msg) <= len(SecletProcess[qqid].SelectList):
                SecletProcess[qqid] = SecletProcess[qqid]._replace(state=False)
                SecletProcess[qqid] = SecletProcess[qqid]._replace(SlectIndex=int(msg))
            else:
                await bot_listen.send('请选择列表中的序号哦~')
        return
    except Exception:
        logger.error(traceback.format_exc())
        return


async def wait_to_select(hikari):
    SecletProcess[hikari.UserInfo.PlatformId] = SlectState(True, None, hikari.Input.Select_Data)
    a = 0
    while a < 40 and not SecletProcess[hikari.UserInfo.PlatformId].SlectIndex:
        a += 1
        await asyncio.sleep(0.5)
    if SecletProcess[hikari.UserInfo.PlatformId].SlectIndex:
        hikari.Input.Select_Index = SecletProcess[hikari.UserInfo.PlatformId].SlectIndex
        SecletProcess[hikari.UserInfo.PlatformId] = SlectState(False, None, None)
        return hikari
    else:
        SecletProcess[hikari.UserInfo.PlatformId] = SlectState(False, None, None)
        return hikari.error('已超时退出')


@bot_get_random_pic.handle()
async def send_random_ocr_image(ev: MessageEvent):
    try:
        img = await get_Random_Ocr_Pic()
        if isinstance(img, bytes):
            await bot_get_random_pic.send(MessageSegment.file_image(img))
        elif isinstance(img, str):
            await bot_get_random_pic.send(str(img))
    except Exception:
        logger.error(traceback.format_exc())
        await bot_get_random_pic.send('呜呜呜发生了错误，可能是网络问题，如果过段时间不能恢复请联系麻麻哦~')
        return


@bot_update.handle()
async def update_Hikari(ev: MessageEvent, bot: Bot):
    try:
        from nonebot_plugin_reboot import Reloader

        await bot.send(ev, '正在更新Hikari，完成后将自动重启，如果没有回复您已上线的消息，请登录服务器查看')
        if hasattr(driver.config, 'nb2_path'):
            # 并发fastgit会429，改为顺序请求
            for each in nb2_file:
                await download(each['url'], f"{driver.config.nb2_path}\\{each['name']}")
                await asyncio.sleep(0.5)

            # await asyncio.gather(
            #    *[download(each["url"], f"{driver.config.nb2_path}\{each['name']}") for each in nb2_file]
            # )
        logger.info(f'当前解释器路径{sys.executable}')
        os.system(f'{sys.executable} -m pip install hikari-bot -i https://pypi.tuna.tsinghua.edu.cn/simple --upgrade')
        os.system(f'{sys.executable} -m pip install hikari-core -i https://pypi.tuna.tsinghua.edu.cn/simple --upgrade')
        os.system(f'{sys.executable} -m pip install nonebot-plugin-gocqhttp -i https://pypi.tuna.tsinghua.edu.cn/simple --upgrade')
        Reloader.reload(delay=1)
    except RuntimeError:
        if str(platform.system()).lower() == 'linux':
            try:
                import multiprocessing

                for child in multiprocessing.active_children():
                    child.terminate()
                sys.stdout.flush()
                # not compatible with cmdline with '\n'
                os.execv(
                    os.readlink('/proc/self/exe'),
                    open('/proc/self/cmdline', 'rb').read().replace(b'\0', b'\n').decode().split('\n')[:-1],
                )
            except Exception:
                logger.error(traceback.format_exc())
                await bot.send(ev, '自动更新失败了QAQ，请登录服务器查看具体报错日志')
        else:
            logger.error(traceback.format_exc())
            await bot.send(ev, '不支持nb run启动的方式更新哦，请使用python bot.py 启动Hikari')
    except Exception:
        logger.error(traceback.format_exc())
        await bot.send(ev, '自动更新失败了QAQ，请登录服务器查看具体报错日志')


@driver.on_startup
async def startup():
    try:
        if driver.config.ocr_on:
            await downlod_OcrResult()
    except Exception:
        logger.error(traceback.format_exc())
        return


async def startup_download(url, name):
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=20)
        with open(template_path / name, 'wb+') as file:
            file.write(resp.content)


async def job_chech_version():
    bot = get_bot()
    hikari = Hikari_Model()
    hikari = await check_version(hikari)
    superid = driver.config.superusers
    for each in superid:
        await bot.send_private_msg(user_id=int(each), message=hikari.Output.Data)


scheduler.add_job(job_chech_version, 'cron', hour=12)
scheduler.add_job(startup, 'cron', hour=4)
scheduler.add_job(downlod_OcrResult, 'interval', minutes=10)


@bot_pupu.handle()
async def send_pupu_msg(ev: MessageEvent):
    try:
        if driver.config.group and ev.group_id not in driver.config.ban_group_list:
            msg = await get_pupu_msg()
            await bot_pupu.send(msg)
    except ActionFailed:
        logger.warning(traceback.format_exc())
        try:
            await bot_pupu.send('噗噗寄了>_<可能被风控了QAQ')
        except Exception:
            pass
        return
