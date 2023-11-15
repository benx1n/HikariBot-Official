<!-- markdownlint-disable MD033 MD041 -->
<p align="center">
  <a href="https://github.com/benx1n/HikariBot"><img src="https://s2.loli.net/2022/05/28/SFsER8m6TL7jwJ2.png" alt="Hikari " style="width:200px; height:200px" ></a>
</p>

<div align="center">

# Hikari

<!-- prettier-ignore-start -->
<!-- markdownlint-disable-next-line MD036 -->
战舰世界水表BOT
<!-- prettier-ignore-end -->

<p align="center">
  <a href="https://pypi.python.org/pypi/hikari-bot">
    <img src="https://img.shields.io/pypi/v/hikari-bot" alt="pypi">
  </a>
  <img src="https://img.shields.io/badge/python-3.8.0+-blue" alt="python">
  <a href="http://hits.dwyl.com/benx1n/HikariBot">
    <img src="https://hits.dwyl.com/benx1n/HikariBot.svg?style=flat-square" alt="hits">
  </a>
  <a href="https://github.com/benx1n/HikariBot/stargazers"><img src="https://img.shields.io/github/stars/benx1n/HikariBot" alt="GitHub stars"style="max-width: 100%;">
  </a>
  <br/>
  <a href="https://jq.qq.com/?_wv=1027&k=S2WcTKi5">
    <img src="https://img.shields.io/badge/QQ%E7%BE%A4-967546463-orange?style=flat-square" alt="QQ Chat Group">
  </a>
  <a href="https://qun.qq.com/qqweb/qunpro/share?_wv=3&_wwv=128&appChannel=share&inviteCode=1W4NX2S&from=181074&biz=ka#/pc">
    <img src="https://img.shields.io/badge/QQ%E9%A2%91%E9%81%93-yuyuko助手-5492ff?style=flat-square" alt="QQ Channel">
  </a>

# 💘您不打算给可爱的Hikari点个Star吗QAQ
</p>
</div>

## 简介

战舰世界水表BOT，基于Nonebot2，适配QQ官方机器人
水表人，出击！wws me recent！！！  


## 特色

- [x] 账号总体、单船、近期战绩
- [x] 全指令支持参数乱序
- [x] 快速切换绑定账号
- [x] 实时推送对局信息
- [x] 支持@快速查询
- [x] 全异步，高并发下性能更优
- [x] 适配官方BOT

  <details>
  <summary>点我查看功能列表</summary>

  - 绑定账号：wws bind/set/绑定 [服务器+游戏昵称]：
  - 查询账号绑定列表：wws [查询/查]绑定/绑定列表 [me/@群友]：
  - 切换删除绑定账号：wws [切换/删除]绑定 [序号]
  - 查询账号总体战绩：wws [(服务器+游戏昵称)/@群友/me]
  - 查询账号历史记录：wws [(服务器+游戏昵称)/@群友/me] record
  - 查询账号近期战绩：wws [(服务器+游戏昵称)/@群友/me] recent [日期]
  - 查询单船总体战绩：wws [(服务器+游戏昵称)/@群友/me] ship [船名]
  - 查询单船近期战绩：wws [(服务器+游戏昵称)/@群友/me] ship [船名] recent [日期]
  - 查询服务器排行榜：wws [服务器+战舰名] rank/ship.rank
  - 查询军团详细信息：wws [(服务器+军团名)/@群友/me] clan
  - 查询军团历史记录：wws [(服务器+军团名)/@群友/me] clan record
  - 查询舰船中英文名：wws [搜/查船名] [国家][等级][类型]
  - 添加游戏战绩监控: wws [添加监控] [服务器] [游戏昵称] [备注名]
  - 查询游戏战绩监控: wws [查询监控]
  - 删除游戏战绩监控: wws [删除监控] [监控序号]
  - 重置全部战绩监控: wws [重置监控](该指令仅限superuser使用)
  - 检查版本更新：wws 检查更新
  - 更新：wws 更新Hikari
  - 查看帮助：wws help
  - 噗噗：一言

  </details>
## 在Windows系统上快速部署

  `windows安装python版本请勿大于3.11,建议版本3.10`

1. 下载Hikari的最新Release并解压到合适文件夹
2. 复制一份`.env.prod-example`文件，并将其重命名为`.env.prod`,打开并按其中注释编辑
    >只显示了.env，没有后面的后缀？请百度`windows如何显示文件后缀名`
    ```
    API_TOKEN = xxxxxxxx #无需引号，TOKEN即回复您的邮件所带的一串由[数字+冒号+英文/数字]组成的字符串
    SUPERUSERS=["QQ号"]
    ```
   - 最后TOKEN应该长这样 `API_TOKEN = 123764323:ba1f2511fc30423bdbb183fe33`

3. 双击`启动.bat`


## 更新
实验性更新指令：`wws 更新Hikari`
请确保在能登录上服务器的情况下使用
以下是旧更新方法
1. 按不同版本
   - Windows一键包：下载最新一键包，复制旧版本中`accounts`文件夹和`env.prod`文件替换至新版文件夹中即可
   - 完整版：以管理员身份运行`更新.bat`或执行`./manage.sh update`
      >等效于在cmd中执行如下代码
      ```
      pip install --upgrade hikari-bot
      git pull
      ```
   - 插件版：在cmd中执行如下代码
      ```
      pip install --upgrade hikari-bot
      ```
2. **对比`.env.prod-example`中新增的配置项，并同步至你本地的`env.prod`**
    - install结束后会打印当前版本
    - 您也可以通过`pip show hikari-bot`查看当前Hikari版本
    - 如果没有更新到最新版请等待一会儿，镜像站一般每五分钟同步
    - 从0.3.2.2版本开始，您没有填写的配置将按.env文件中的默认配置执行，具体逻辑为
      - 私聊、频道默认禁用
      - 群聊默认开启，默认屏蔽官方交流群



## 可能会遇到的问题

### 出现ZoneInfoNotFoundError报错
>
>您可以在[这里](https://github.com/nonebot/nonebot2/issues/78)找到相关解决办法
>
### Recent和绑定提示'鉴权失败'
1. 检查Token是否配置正确，token格式为`XXXXX:XXXXXX`
2. 如果配置正确可能是Token失效了，请重新申请



### Ubuntu系统下部署字体不正常(针对一些云服务器的Ubuntu镜像，不保证成功，只是提供一个解决方案)
  1. 执行以下命令，完善字体库并将中文设置成默认语言（部分Ubuntu可能不需要该步骤，可直接从第二步开始）
  ```
  sudo apt install fonts-noto  
  sudo locale-gen zh_CN zh_CN.UTF-8  
  sudo update-locale LC_ALL=zh_CN.UTF-8 LANG=zh_CN.UTF-8  
  sudo fc-cache -fv
  ```
  
  2. 在你的Windows电脑上打开`C:\Windows\fonts`文件夹，找到里面的微软雅黑字体，将其复制出来，放在任意目录，应该会得到`msyh.ttc`，`mshybd.ttc`，`msyhl.ttc`三个文件。（不会有人还用Win7吧？）

  3. 进入到`/usr/share/fonts`文件夹下，创建一个文件夹命名为`msyh`，然后进入其中
  ```
  cd /usr/share/fonts 
  sudo mkdir msyh 
  cd msyh
  ```
  
  4. 将三个字体文件上传到`msyh`文件夹中(过程中遇到的问题请自行解决)

  5. 执行以下命令（此时你应该是在`msyh`文件夹下），加载字体
  ```
  sudo mkfontscale 
  sudo mkfontdir 
  sudo fc-cache -fv
  ```
  
  6. （可选，若不正常可尝试）重启Hikari。


## 贡献代码

请向dev分支提交PR

## 鸣谢

感谢以下开发者及项目做出的贡献与支持

<a href="https://github.com//benx1n/HikariBot/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=benx1n/HikariBot" />
</a>

[Nonebot2](https://github.com/nonebot/nonebot2)  
[go-cqhttp](https://github.com/Mrs4s/go-cqhttp)  
[战舰世界API平台](https://wows.shinoaki.com/)  

## 开源相关
MIT
修改、分发代码时请保留原作者相关信息

## 赞助
<p align="left">
  <a href="https://afdian.net/a/JustOneSummer?tab=home"><img src="https://hikari-resource.oss-cn-shanghai.aliyuncs.com/%E7%88%B1%E5%8F%91%E7%94%B5.png" alt="afdian" ></a>
</p>
