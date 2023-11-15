#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path

import nonebot
from nonebot.adapters.qq import Adapter
from nonebot.log import default_format, logger

nonebot.init()

driver = nonebot.get_driver()
driver.register_adapter(Adapter)
config = nonebot.get_driver().config
config.nb2_path = Path(__file__).parent

if __name__ == '__main__':
    logger.add(
        'logs/error.log',
        rotation='00:00',
        retention='1 week',
        diagnose=False,
        level='ERROR',
        format=default_format,
        encoding='utf-8',
    )
    logger.add(
        'logs/info.log',
        rotation='00:00',
        retention='1 week',
        diagnose=False,
        level='INFO',
        format=default_format,
        encoding='utf-8',
    )
    logger.add(
        'logs/warning.log',
        rotation='00:00',
        retention='1 week',
        diagnose=False,
        level='WARNING',
        format=default_format,
        encoding='utf-8',
    )
    nonebot.load_from_toml('pyproject.toml')
    nonebot.run()
