#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr  4 19:06:08 2018

@author: mparvin
@contributor: troyejames9
"""

import configparser
import logging
import os
import subprocess
from functools import wraps
from pathlib import Path

# noinspection PyPackageRequirements
from telegram import ParseMode
# noinspection PyPackageRequirements
from telegram.ext import Updater, CommandHandler


def load_ini(filename, dictname):
    conf = configparser.ConfigParser()
    conf.read(Path(__file__).parent / "assets" / filename)
    content = dict(conf[dictname])
    return content


CONFIG = load_ini("config", "SecretConfig")
CMD_DICT = load_ini("cmd.ini", "Commands")
# Get admin chat_id from CONFIG file
# For more security replies only send to admin chat_id
ADMINCID = CONFIG["admincid"]

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

LOGGING = logging.getLogger(__name__)


def admin_required(func):
    @wraps(func)
    def wrapper(bot, update, *args, **kwargs):
        chat_id = str(update.message.chat_id)
        if chat_id == ADMINCID:
            return func(bot, update, *args, **kwargs)
        else:
            update.message.reply_text(
                "该指令需管理员权限才能执行"
            )
            # alertMessage = (
            #     "Some one try to use this bot with this information:\n chat_id is {} and username is {}".format(
            #         chat_id, update.message.chat.username
            #     ))
            # bot.sendMessage(text=alertMessage, chat_id=ADMINCID)

    return wrapper


def executeCommand(command: str, bot):
    # 执行命令
    proc = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True,
    )
    cmdOut, cmdErr = proc.communicate()
    if cmdOut:
        bot.sendMessage(text=str(cmdOut, "utf-8"), chat_id=ADMINCID)
    else:
        bot.sendMessage(text=str(cmdErr, "utf-8"), chat_id=ADMINCID)


# This function run command and send output to user
@admin_required
def runCMD(bot, update):
    commandname = update.message.text[1:]  # 去掉实际指令开头的斜杠
    usercommand = CMD_DICT[commandname]
    executeCommand(usercommand, bot)


def startCMD(bot, update):
    bot.sendMessage(
        text="这里是tflowbot，你的服务器的私人助手, 请执行/help以浏览我所能提供的服务",
        chat_id=update.message.chat_id,
    )


def helpCMD(bot, update):
    # 获取脚本所在目录的绝对路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    help_file = os.path.join(script_dir, "assets", "help.md")

    with open(help_file, "r", encoding="utf-8") as file:
        help_text = file.read()

    bot.sendMessage(text=help_text, chat_id=update.message.chat_id, parse_mode=ParseMode.MARKDOWN)


@admin_required
def topCMD(bot):
    cmdOut = str(subprocess.check_output("top -n 1", shell=True), "utf-8")
    bot.sendMessage(text=cmdOut, chat_id=ADMINCID)
    bot.sendMessage(text=cmdOut, chat_id=ADMINCID)


@admin_required
def HTopCMD(bot, update):
    # Checking requirements on your system
    htopCheck = subprocess.call(["which", "htop"])
    if htopCheck != 0:
        bot.sendMessage(
            text="htop is not installed on your system, Please install it first and try again",
            chat_id=ADMINCID,
        )
        return
    ahaCheck = subprocess.call(["which", "aha"])
    if ahaCheck != 0:
        bot.sendMessage(
            text="aha is not installed on your system, Please install it first and try again",
            chat_id=ADMINCID,
        )
        return
    os.system("echo q | htop | aha --black --line-fix  > ./htop-output.html")
    with open("./htop-output.html", "rb") as fileToSend:
        bot.sendDocument(document=fileToSend, chat_id=ADMINCID)
    if os.path.exists("./htop-output.html"):
        os.remove("./htop-output.html")


def error_callback(bot, update, err):
    LOGGING.error(f'Update: {update} \nError: {err}')

    # 向管理员报告错误
    if update:
        error_msg = (
            f"⚠️ Bot Error:\n"
            f"Update: {update}\n\n"
            f"Error: {str(err)}"
        )
        bot.sendMessage(text=error_msg, chat_id=ADMINCID)


def main():
    request_kwargs = {
        'proxy_url': 'http://127.0.0.1:7890/',  # 替换为你的 mihomo 代理地址（如 socks5://127.0.0.1:7891）
    }
    updater = Updater(
        token=CONFIG["token"],
        request_kwargs=request_kwargs  # 新增代理配置
    )
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", startCMD))
    dp.add_handler(CommandHandler("help", helpCMD))
    for key in CMD_DICT.keys():
        dp.add_handler(CommandHandler(key, runCMD))

    dp.add_handler(CommandHandler("top", topCMD))
    dp.add_handler(CommandHandler("htop", HTopCMD))

    dp.add_error_handler(error_callback)
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
