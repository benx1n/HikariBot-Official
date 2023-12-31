import gzip
import hashlib
import io
import os
import time
import traceback
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Optional

import httpx
import nonebot
import orjson
import oss2
import pytz
from nonebot import get_driver
from nonebot.adapters.qq import Bot

from .data_source import image_path

config = get_driver().config


async def match_keywords(match_list, Lists):
    for List in Lists:
        for kw in List.keywords:
            for match_kw in match_list:
                if match_kw == kw or match_kw.upper() == kw.upper() or match_kw.lower() == kw.lower():
                    match_list.remove(match_kw)
                    return List.match_keywords, match_list
    return None, match_list


async def find_and_replace_keywords(match_list, Lists):
    for List in Lists:
        for kw in List.keywords:
            for i, match_kw in enumerate(match_list):
                if match_kw.find(kw) + 1:
                    match_list[i] = str(match_kw).replace(kw, '')
                    if match_list[i] == '':
                        match_list.remove('')
                    return List.match_keywords, match_list
    return None, match_list


def encode_gzip(bytes):
    buf = io.BytesIO(bytes)
    gf = gzip.GzipFile(fileobj=buf)
    return gf.read().decode('utf-8')


class FreqLimiter:
    def __init__(self, default_cd_seconds):
        self.next_time = defaultdict(float)
        self.default_cd = default_cd_seconds

    def check(self, key) -> bool:
        return bool(time.time() >= self.next_time[key])

    def start_cd(self, key, cd_time=0):
        self.next_time[key] = time.time() + (cd_time if cd_time > 0 else self.default_cd)

    def left_time(self, key) -> float:
        return self.next_time[key] - time.time()


class DailyNumberLimiter:
    tz = pytz.timezone('Asia/Shanghai')

    def __init__(self, max_num):
        self.today = -1
        self.count = defaultdict(int)
        self.max = max_num

    def check(self, key) -> bool:
        now = datetime.now(self.tz)
        day = (now - timedelta(hours=5)).day
        if day != self.today:
            self.today = day
            self.count.clear()
        return bool(self.count[key] < self.max)

    def get_num(self, key):
        return self.count[key]

    def increase(self, key, num=1):
        self.count[key] += num

    def reset(self, key):
        self.count[key] = 0


def get_bot() -> Optional[Bot]:
    """
    说明：
        获取 bot 对象
    """
    try:
        return list(nonebot.get_bots().values())[0]
    except IndexError:
        return None


async def download(url, path, proxy={}):  # noqa: B006
    async with httpx.AsyncClient(proxies=proxy, verify=False) as client:
        try:
            resp = await client.get(url, timeout=None)
            if resp.status_code == 200:
                content = resp.read()
                content = content.replace(b'\n', b'\r\n')
                with open(path, 'wb') as f:
                    f.write(content)
            else:
                print(f'fastgit请求失败{resp.status_code}')
        except Exception:
            print(traceback.format_exc())


async def byte2md5(bytes):
    res = hashlib.md5(bytes).hexdigest()
    return res


async def upload_oss(bytes):
    endpoint = config.oss_endpoint
    auth = oss2.Auth(config.oss_id, config.oss_key)
    bucket = oss2.Bucket(auth, endpoint, config.oss_bucket)
    md5 = await byte2md5(bytes)
    key = f'bot_image/{md5}.png'
    bucket.put_object(key, bytes)
    url = bucket.sign_url('GET', key, 3600, slash_safe=True)
    url = url.replace('http', 'https')
    print(url)
    return url


async def upload_smms(bytes):
    headers = {'Authorization': config.smms_key}
    async with httpx.AsyncClient(proxies={}, headers=headers) as client:
        files = {'smfile': bytes}
        url = 'https://smms.app/api/v2/upload'
        resp = await client.post(url, files=files)
        result = orjson.loads(resp.content)
        print(result)
        if result['success']:
            return result['data']['url']
        else:
            return result['images']


async def upload_local(bytes):
    md5 = await byte2md5(bytes)
    if not os.path.exists(image_path):
        os.mkdir(image_path)
    with open(image_path / f'{md5}.png', 'wb') as f:
        f.write(bytes)
    async with httpx.AsyncClient(proxies={}) as client:
        url = 'https://4.ipw.cn'
        resp = await client.get(url)
        ip = str(resp.text)
    return f'http://{ip}:{config.port}/images/{md5}.png'


async def upload_image(bytes):
    if config.upload_image == 'oss':
        return await upload_oss(bytes)
    elif config.upload_image == 'smms':
        return await upload_smms(bytes)
    elif config.upload_image == 'local':
        return await upload_local(bytes)
    else:
        return None
