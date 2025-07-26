#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr  4 19:06:08 2018

@author: mparvin
"""

import subprocess
import configparser
import os
# noinspection PyPackageRequirements
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
# noinspection PyPackageRequirements
from telegram import ParseMode
import logging
from pathlib import Path


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
def runCMD(bot, update):
    if not isAdmin(bot, update):
        return
    commandname = update.message.text[1:]  # 去掉实际指令开头的斜杠
    usercommand = CMD_DICT[commandname]
    executeCommand(usercommand, bot)


def startCMD(bot, update):
    if not isAdmin(bot, update):
        return
    bot.sendMessage(
        text="这里是tflowbot，你的服务器的私人助手, 请执行/help以浏览我所能提供的服务",
        chat_id=ADMINCID,
    )


def helpCMD(bot, update):
    if not isAdmin(bot, update):
        return

    # 获取脚本所在目录的绝对路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    help_file = os.path.join(script_dir, "assets", "help.md")

    with open(help_file, "r", encoding="utf-8") as file:
        help_text = file.read()

    bot.sendMessage(text=help_text, chat_id=ADMINCID, parse_mode=ParseMode.MARKDOWN)


def topCMD(bot, update):
    if not isAdmin(bot, update):
        return
    cmdOut = str(subprocess.check_output("top -n 1", shell=True), "utf-8")
    bot.sendMessage(text=cmdOut, chat_id=ADMINCID)
    bot.sendMessage(text=cmdOut, chat_id=ADMINCID)


def HTopCMD(bot, update):
    # Is this user admin?
    if not isAdmin(bot, update):
        return
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


def error(update, error):
    """Log Errors caused by Updates."""
    LOGGING.warning('Update "%s" caused error "%s"', update, error)


def isAdmin(bot, update):
    chat_id = update.message.chat_id
    if str(chat_id) == ADMINCID:
        return True

    update.message.reply_text(
        "You cannot use this bot, because you are not Admin!!!!"
    )
    alertMessage = """Some one try to use this bot with this information:\n chat_id is {} and username is {} """.format(
        update.message.chat_id, update.message.from_user.username
    )
    bot.sendMessage(text=alertMessage, chat_id=ADMINCID)
    return False


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
    dp.add_handler(CommandHandler("top", topCMD))
    dp.add_handler(CommandHandler("htop", HTopCMD))
    dp.add_handler(CommandHandler("help", helpCMD))

    for key in CMD_DICT.keys():
        dp.add_handler(CommandHandler(key, runCMD))

    # dp.add_handler(MessageHandler(Filters.text, runCMD))

    dp.add_error_handler(error)
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
