import asyncio
import os
import platform
import shutil
import sys
import traceback
from collections import defaultdict, namedtuple

import httpx
import nonebot
from fastapi import FastAPI
from fastapi.responses import FileResponse
from hikari_core import callback_hikari, init_hikari, set_hikari_config
from hikari_core.game.help import check_version
from hikari_core.model import Hikari_Model
from hikari_core.moudle.wws_real_game import (
    add_listen_list,
    delete_listen_list,
    get_diff_ship,
    get_listen_list,
)
from nonebot import get_driver, on_command, on_message, require
from nonebot.adapters.qq import (
    ActionFailed,
    Bot,
    DirectMessageCreateEvent,
    GuildMessageEvent,
    Message,
    MessageEvent,
    MessageSegment,
)
from nonebot.exception import FinishedException
from nonebot.log import logger
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER

from .data_source import dir_path, image_path, nb2_file, template_path
from .game.ocr import get_Random_Ocr_Pic
from .game.pupu import get_pupu_msg
from .utils import DailyNumberLimiter, FreqLimiter, download, get_bot, upload_image

scheduler = require('nonebot_plugin_apscheduler').scheduler

_max = 100
EXCEED_NOTICE = f'您今天已经冲过{_max}次了，请明早5点后再来！'
is_first_run = True
_nlmt = DailyNumberLimiter(_max)
_flmt = FreqLimiter(3)
__bot_version__ = '0.2.9'

test = on_command('test', priority=4, block=True)
bot_get_random_pic = on_command('wws 随机表情包', block=True, priority=5)
bot_update = on_command('wws 更新Hikari', priority=5, block=True, permission=SUPERUSER)
delete_image_cache = on_command('wws 清除本地缓存', priority=5, block=True, permission=SUPERUSER)
wws = on_command('wws', block=False, aliases={'WWS'}, priority=10)
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
    user_id = event.get_user_id()
    await test.send(f'您的USER_ID为{user_id}')
    # User = await bot.get_member(guild_id=str(event.guild_id), user_id=str(user_id))
    # print(f'您的USER_ID为{user_id}\n您的uid为{User.user.union_openid}')
    # await test.send(f'您的USER_ID为{user_id}\n您的id为{event.id}\n您的uid为{uid}')


@wws.handle()
async def main(ev: MessageEvent, matchmsg: Message = CommandArg()):  # noqa: B008, PLR0915
    try:
        if not await check_rule(ev):
            # await wws.send('该功能请前往' + MessageSegment.mention_channel(5207171) + '使用')
            await wws.finish('该功能已禁用')
        bot = get_bot()
        server_type = driver.config.platform
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
        if '发送私信' in str(matchmsg) and isinstance(ev, GuildMessageEvent):
            try:
                dms_response = await bot.call_api(
                    'post_dms',
                    recipient_id=str(qqid),
                    source_guild_id=str(ev.guild_id),
                )
                logger.info(f'创建私信频道{dms_response.guild_id}')
                await bot.send(
                    message='hello~',
                    event=DirectMessageCreateEvent(guild_id=dms_response.guild_id, id=ev.id, channel_id=ev.channel_id, author=ev.author),
                )
                await wws.finish('已向您主动发送私信,请注意查收')
            except Exception:
                logger.error(traceback.format_exc())
                await wws.finish('私信发送失败，可能是单日限额，请明天再尝试')
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
                if isinstance(ev, GuildMessageEvent):
                    await wws.send(MessageSegment.file_image(hikari.Output.Data))
                else:
                    url = await upload_image(hikari.Output.Data)
                    logger.success(url)
                    await wws.send(MessageSegment.image(url))
            elif isinstance(hikari.Output.Data, str):
                await wws.send(hikari.Output.Data)
        elif hikari.Status == 'wait':
            if isinstance(ev, GuildMessageEvent):
                await wws.send(MessageSegment.file_image(hikari.Output.Data))
            else:
                url = await upload_image(hikari.Output.Data)
                logger.success(url)
                await wws.send(MessageSegment.image(url))
            hikari = await wait_to_select(hikari)
            if hikari.Status == 'error':
                await wws.send(str(hikari.Output.Data))
                return
            hikari = await callback_hikari(hikari)
            if isinstance(hikari.Output.Data, bytes):
                if isinstance(ev, GuildMessageEvent):
                    await wws.send(MessageSegment.file_image(hikari.Output.Data))
                else:
                    url = await upload_image(hikari.Output.Data)
                    logger.success(url)
                    await wws.send(MessageSegment.image(url))
            elif isinstance(hikari.Output.Data, str):
                await wws.send(str(hikari.Output.Data))
        else:
            await wws.send(str(hikari.Output.Data))
    except FinishedException:
        return
    except ActionFailed as e:
        logger.error(traceback.format_exc())
        try:
            await wws.send(f'发不出图片，可能撞限速了QAQ，请在频道重新尝试\n{e}')
            return True
        except Exception:
            logger.error(traceback.format_exc())
            pass
        return False
    except Exception:
        logger.error(traceback.format_exc())
        await wws.send('呜呜呜发生了错误，可能是网络问题，如果过段时间不能恢复请联系麻麻哦~')


@bot_listen.handle()
async def change_select_state(ev: MessageEvent):
    try:
        if not await check_rule(ev):
            return
        msg = str(ev.get_message()).strip()
        qqid = str(ev.get_user_id())
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
            if isinstance(ev, GuildMessageEvent):
                await wws.send(MessageSegment.file_image(img))
            else:
                url = await upload_image(img)
                logger.success(url)
                await wws.send(MessageSegment.image(url))
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
                await asyncio.sleep(1)
        logger.info(f'当前解释器路径{sys.executable}')
        os.system(f'{sys.executable} -m pip install hikari-bot-official -i https://pypi.tuna.tsinghua.edu.cn/simple --upgrade')
        os.system(f'{sys.executable} -m pip install hikari-core -i https://pypi.tuna.tsinghua.edu.cn/simple --upgrade')
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
def web_run():
    if get_driver().config.upload_image == 'local':
        app: FastAPI = nonebot.get_app()
        if not os.path.exists(image_path):
            os.mkdir(image_path)
        logger.success('本地文件服务器启动成功，请确认是否放行对应端口，如果没有公网ip请将配置项UPLOAD_IMAGE改为smms或oss')

        @app.get('/images/{filename}')
        async def get_file(filename):
            return FileResponse(image_path / filename)


async def startup_download(url, name):
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=20)
        with open(template_path / name, 'wb+') as file:
            file.write(resp.content)


async def job_chech_version():
    get_bot()
    hikari = Hikari_Model()
    hikari = await check_version(hikari)
    # superid = driver.config.superusers
    # for each in superid:
    #    await bot.send_private_msg(user_id=int(each), message=hikari.Output.Data)


scheduler.add_job(job_chech_version, 'cron', hour=12, misfire_grace_time=60)


@bot_pupu.handle()
async def send_pupu_msg(ev: MessageEvent):
    try:
        if await check_rule(ev):
            msg = await get_pupu_msg()
            await bot_pupu.send(msg)
    except ActionFailed:
        logger.warning(traceback.format_exc())
        try:
            await bot_pupu.send('噗噗寄了>_<可能被风控了QAQ')
        except Exception:
            pass
        return


@delete_image_cache.handle()
async def delete_image(ev: MessageEvent):
    try:
        shutil.rmtree(image_path, ignore_errors=True)
        if not os.path.exists(image_path):
            os.mkdir(image_path)
        await delete_image_cache.send('清除缓存成功')
    except Exception:
        logger.error(traceback.format_exc())
        await delete_image_cache.send('清除缓存失败')


async def check_rule(ev):
    if driver.config.filter_rule == 'None':
        return True
    if isinstance(ev, DirectMessageCreateEvent) and driver.config.private:
        return True
    if isinstance(ev, GuildMessageEvent):
        if (
            driver.config.filter_rule == 'white'
            and (int(ev.guild_id) in driver.config.white_guild_list or int(ev.channel_id) in driver.config.white_channel_list)
        ) or (
            driver.config.filter_rule == 'black'
            and (int(ev.guild_id) not in driver.config.ban_guild_list and int(ev.channel_id) not in driver.config.ban_channel_list)
        ):
            return True
    else:
        return True
    return False
