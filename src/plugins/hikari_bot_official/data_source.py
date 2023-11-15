from pathlib import Path

from nonebot import get_driver

dir_path = Path(__file__).parent
template_path = dir_path / 'template'
image_path = dir_path / 'image_cache'
config = get_driver().config

nb2_file = [
    {'name': 'bot.py', 'url': 'https://raw.fastgit.org/benx1n/HikariBot-Official/master/bot.py'},
    {'name': '.env', 'url': 'https://raw.fastgit.org/benx1n/HikariBot-Official/master/.env'},
    {'name': 'pyproject.toml', 'url': 'https://raw.fastgit.org/benx1n/HikariBot-Official/master/pyproject.toml'},
]
