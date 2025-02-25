#!/usr/bin/env python
"""
    The MIT License (MIT)

    Copyright (c) 2023 pkjmesra

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.

"""
# pylint: disable=unused-argument, wrong-import-position
# This program is dedicated to the public domain under the CC0 license.

"""Simple inline keyboard bot with multiple CallbackQueryHandlers.

This Bot uses the Application class to handle the bot.
First, a few callback functions are defined as callback query handler. Then, those functions are
passed to the Application and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.
Usage:
Example of a bot that uses inline keyboard that has multiple CallbackQueryHandlers arranged in a
ConversationHandler.
Send /start to initiate the conversation.
Press Ctrl-C on the command line to stop the bot.
"""
import html
import json
import logging
import re
import sys
import traceback
from datetime import datetime
from subprocess import Popen

from telegram import __version__ as TG_VER
from telegram.constants import ParseMode

start_time = datetime.now()
MINUTES_5_IN_SECONDS = 300

from pkscreener.classes.MenuOptions import MenuRenderStyle, menu, menus
from pkscreener.classes.WorkflowManager import run_workflow
from pkscreener.Telegram import get_secrets

try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)  # type: ignore[assignment]

if __version_info__ < (20, 0, 0, "alpha", 1):
    raise RuntimeError(
        f"This example is not compatible with your current PTB version {TG_VER}. To view the "
        f"{TG_VER} version of this example, "
        f"visit https://docs.python-telegram-bot.org/en/v{TG_VER}/examples.html"
    )
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (Application, CallbackQueryHandler, CommandHandler,
                          ContextTypes, ConversationHandler, MessageHandler,
                          filters)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# Stages
START_ROUTES, END_ROUTES = range(2)
# Callback data
ONE, TWO, THREE, FOUR = range(4)

m0 = menus()
m1 = menus()
m2 = menus()
m3 = menus()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send message on `/start`."""
    # Get user that sent /start and log his name
    user = update.message.from_user
    logger.info("User %s started the conversation.", user.first_name)
    # Build InlineKeyboard where each button has a displayed text
    # and a string as callback_data
    # The keyboard is a list of button rows, where each row is in turn
    # a list (hence `[[...]]`).
    mns = m0.renderForMenu(asList=True)
    inlineMenus = []
    for mnu in mns:
        if mnu.menuKey in ["X", "B", "Z"]:
            inlineMenus.append(
                InlineKeyboardButton(
                    mnu.keyTextLabel().split("(")[0],
                    callback_data="C" + str(mnu.menuKey),
                )
            )
    keyboard = [inlineMenus]
    reply_markup = InlineKeyboardMarkup(keyboard)
    # Send message with text and appended InlineKeyboard
    await update.message.reply_text(
        f"Welcome {user.first_name}, {(user.username)}! Please choose a menu option by selecting a button from below.\n\nYou can also explore a wide variety of all other scanners by typing in \n   /X or \nbacktest with /B",
        reply_markup=reply_markup,
    )
    await context.bot.send_message(
        chat_id=int(f"-{Channel_Id}"),
        text=f"Name: {user.first_name}, Username:@{user.username} with ID: {str(user.id)} started using the bot!",
        parse_mode=ParseMode.HTML,
    )
    # Tell ConversationHandler that we're in state `FIRST` now
    return START_ROUTES


async def XScanners(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show new choice of buttons"""
    query = update.callback_query
    data = query.data.upper().replace("CX", "X").replace("CB", "B")
    if data not in ["X", "B"]:
        return start(update, context)
    midSkip = "1" if data == "X" else "N"
    menuText = (
        m1.renderForMenu(
            m0.find(data),
            skip=[
                "W",
                "E",
                "M",
                "Z",
                "0",
                "2",
                midSkip,
                "3",
                "4",
                "6",
                "7",
                "9",
                "10",
                "13",
            ],
            renderStyle=MenuRenderStyle.STANDALONE,
        )
        .replace("     ", "")
        .replace("    ", "")
        .replace("\t", "")
    )
    mns = m1.renderForMenu(
        m0.find(data),
        skip=["W", "E", "M", "Z", "0", "2", midSkip, "3", "4", "6", "7", "9", "10", "13"],
        asList=True,
    )
    inlineMenus = []
    await query.answer()
    for mnu in mns:
        inlineMenus.append(
            InlineKeyboardButton(
                mnu.menuKey, callback_data=str(f"{query.data}_{mnu.menuKey}")
            )
        )
    keyboard = [inlineMenus]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text=menuText, reply_markup=reply_markup)
    return START_ROUTES


async def Level2(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show new choice of buttons"""
    inlineMenus = []
    menuText = "Something went wrong! Please try again..."
    mns = []
    query = update.callback_query
    await query.answer()
    preSelection = query.data.upper().replace("CX", "X").replace("CB", "B")
    selection = preSelection.split("_")
    preSelection = f"{selection[0]}_{selection[1]}"
    if selection[0].upper() not in ["X","B"]:
        return start(update, context)
    if len(selection) == 2 or (len(selection) == 3 and selection[2] == "P"):
        if str(selection[1]).isnumeric():
            # It's only level 2
            menuText = m2.renderForMenu(
                m1.find(selection[1]),
                skip=[
                    "0",
                    "8",
                    "9",
                    "10",
                    "11",
                    "12",
                    "13",
                    "14",
                    "15",
                    "16",
                    "17",
                    "18",
                    "19",
                    "20",
                    "21",
                    "22",
                    "23",
                    "24",
                    "25",
                    "26",
                    "27",
                    "28",
                    "42",
                    "M",
                    "Z",
                ],
                renderStyle=MenuRenderStyle.STANDALONE,
            )
            menuText = menuText + "\nN > More options"
            mns = m2.renderForMenu(
                m1.find(selection[1]),
                skip=[
                    "0",
                    "8",
                    "9",
                    "10",
                    "11",
                    "12",
                    "13",
                    "14",
                    "15",
                    "16",
                    "17",
                    "18",
                    "19",
                    "20",
                    "21",
                    "22",
                    "23",
                    "24",
                    "25",
                    "26",
                    "27",
                    "28",
                    "42",
                    "M",
                    "Z",
                ],
                asList=True,
                renderStyle=MenuRenderStyle.STANDALONE,
            )
            mns.append(menu().create("N", "More Options", 2))
        elif selection[1] == "N":
            selection.extend(["", ""])
    elif len(selection) == 3:
        if selection[2] == "N":
            menuText = m2.renderForMenu(
                m1.find(selection[1]),
                skip=[
                    "0",
                    "1",
                    "2",
                    "3",
                    "4",
                    "5",
                    "6",
                    "7",
                    "14",
                    "15",
                    "16",
                    "17",
                    "18",
                    "19",
                    "20",
                    "21",
                    "22",
                    "23",
                    "24",
                    "25",
                    "26",
                    "27",
                    "28",
                    "42",
                    "M",
                    "Z",
                ],
                renderStyle=MenuRenderStyle.STANDALONE,
            )
            menuText = menuText + "\nP > Previous Options"
            menuText = menuText + "\nM > More Options"
            mns = m2.renderForMenu(
                m1.find(selection[1]),
                skip=[
                    "0",
                    "1",
                    "2",
                    "3",
                    "4",
                    "5",
                    "6",
                    "7",
                    "14",
                    "15",
                    "16",
                    "17",
                    "18",
                    "19",
                    "20",
                    "21",
                    "22",
                    "23",
                    "24",
                    "25",
                    "26",
                    "27",
                    "28",
                    "42",
                    "M",
                    "Z",
                ],
                asList=True,
                renderStyle=MenuRenderStyle.STANDALONE,
            )
            mns.append(menu().create("P", "Previous Options", 2))
            mns.append(menu().create("M", "More Options", 2))
        elif selection[2] == "M":
            menuText = m2.renderForMenu(
                m1.find(selection[1]),
                skip=[
                    "0",
                    "1",
                    "2",
                    "3",
                    "4",
                    "5",
                    "6",
                    "7",
                    "8",
                    "9",
                    "10",
                    "11",
                    "12",
                    "13",
                    "21",
                    "22",
                    "23",
                    "24",
                    "25",
                    "26",
                    "27",
                    "28",
                    "42",
                    "M",
                    "Z",
                ],
                renderStyle=MenuRenderStyle.STANDALONE,
            )
            menuText = menuText + "\nP > Previous Options"
            mns = m2.renderForMenu(
                m1.find(selection[1]),
                skip=[
                    "0",
                    "1",
                    "2",
                    "3",
                    "4",
                    "5",
                    "6",
                    "7",
                    "8",
                    "9",
                    "10",
                    "11",
                    "12",
                    "13",
                    "21",
                    "22",
                    "23",
                    "24",
                    "25",
                    "26",
                    "27",
                    "28",
                    "42",
                    "M",
                    "Z",
                ],
                asList=True,
                renderStyle=MenuRenderStyle.STANDALONE,
            )
            mns.append(menu().create("P", "Previous Options", 2))
        elif str(selection[2]).isnumeric():
            preSelection = f"{selection[0]}_{selection[1]}_{selection[2]}"
            if selection[2] in ["6", "7"]:
                menuText = m3.renderForMenu(
                    m2.find(selection[2]),
                    renderStyle=MenuRenderStyle.STANDALONE,
                    skip=["0"],
                )
                mns = m3.renderForMenu(
                    m2.find(selection[2]),
                    asList=True,
                    renderStyle=MenuRenderStyle.STANDALONE,
                    skip=["0"],
                )
            else:
                if selection[2] == "4":  # Last N days
                    selection.extend(["4", ""])
                elif selection[2] == "5":  # RSI range
                    selection.extend(["67", "71"])
                elif selection[2] == "8":  # CCI range
                    selection.extend(["-100", "150"])
                elif selection[2] == "9":  # Vol gainer ratio
                    selection.extend(["2.5", ""])
                elif selection[2] in [
                    "1",
                    "2",
                    "3",
                    "10",
                    "11",
                    "12",
                    "13",
                    "14",
                    "15",
                    "16",
                    "17",
                    "18",
                    "19",
                    "20"
                ]:  # Vol gainer ratio
                    selection.extend(["", ""])
    elif len(selection) == 4:
        preSelection = query.data.upper().replace("CX", "X").replace("CB", "B")
    optionChoices = ""
    if len(selection) <= 3:
        for mnu in mns:
            inlineMenus.append(
                InlineKeyboardButton(
                    mnu.menuKey,
                    callback_data="C" + str(f"{preSelection}_{mnu.menuKey}"),
                )
            )
        keyboard = [inlineMenus]
        reply_markup = InlineKeyboardMarkup(keyboard)
    elif len(selection) >= 4:
        optionChoices = (
            f"{selection[0]} > {selection[1]} > {selection[2]} > {selection[3]}"
        )
        menuText = f"Thank you for choosing {optionChoices}. You will receive the results soon! \n\nConsider donating to help keep this project going:\nUPI: 8007162973@APL \nor\nhttps://github.com/sponsors/pkjmesra?frequency=one-time&sponsor=pkjmesra\n\nSince it is running on a low-end server, it might take from a few seconds to a few minutes. You will get notified here when the results arrive!"

        mns = m0.renderForMenu(asList=True)
        for mnu in mns:
            if mnu.menuKey in ["X", "B", "Z"]:
                inlineMenus.append(
                    InlineKeyboardButton(
                        mnu.keyTextLabel().split("(")[0],
                        callback_data="C" + str(mnu.menuKey),
                    )
                )
        keyboard = [inlineMenus]
        reply_markup = InlineKeyboardMarkup(keyboard)
        options = ":".join(selection)
        await launchScreener(
            options=options,
            user=query.from_user,
            context=context,
            optionChoices=optionChoices,
            update=update,
        )
    try:
        if optionChoices != "":
            await context.bot.send_message(
                chat_id=int(f"-{Channel_Id}"),
                text=f"Name: <b>{query.from_user.first_name}</b>, Username:@{query.from_user.username} with ID: <b>@{str(query.from_user.id)}</b> submitted scan request <b>{optionChoices}</b> to the bot!",
                parse_mode=ParseMode.HTML,
            )
    except Exception:
        await start(update, context)
    await sendUpdatedMenu(
        menuText=menuText, update=update, context=context, reply_markup=reply_markup
    )
    return START_ROUTES


async def sendUpdatedMenu(menuText, update: Update, context, reply_markup):
    try:
        await update.callback_query.edit_message_text(
            text=menuText.replace("     ", "").replace("    ", "").replace("\t", ""),
            reply_markup=reply_markup,
        )
    except Exception:
        await start(update, context)


async def launchScreener(options, user, context, optionChoices, update):
    try:
        if str(optionChoices.upper()).startswith("X"):
            Popen(
                [
                    "pkscreener",
                    "-a",
                    "Y",
                    "-e",
                    "-p",
                    "-o",
                    str(options.upper()),
                    "-u",
                    str(user.id),
                ]
            )
        elif str(optionChoices.upper()).startswith("B"):
            optionChoices = optionChoices.replace(" ","").replace(">","_")
            while(optionChoices.endswith('_')):
                optionChoices = optionChoices[:-1]
            run_workflow(optionChoices,str(user.id),str(options.upper()))
    except Exception:
        await start(update, context)


async def BBacktests(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show new choice of buttons"""
    query = update.callback_query
    await query.answer()
    keyboard = [
        [
            InlineKeyboardButton("Try Scanners", callback_data=str("CX")),
            InlineKeyboardButton("Exit", callback_data=str("CZ")),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text="Backtesting NOT implemented yet in this Bot!\n\n\nYou can use backtesting by downloading the software from https://github.com/pkjmesra/PKScreener/",
        reply_markup=reply_markup,
    )
    return START_ROUTES


async def end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Returns `ConversationHandler.END`, which tells the
    ConversationHandler that the conversation is over.
    """
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        text="See https://github.com/pkjmesra/PKScreener/ for more details or join https://t.me/PKScreener. \n\n\nSee you next time!"
    )
    return ConversationHandler.END


# This can be your own ID, or one for a developer group/channel.
# You can use the /start command of this bot to see your chat id.
chat_idADMIN = 123456789
Channel_Id = 12345678
GROUP_CHAT_ID = 1001907892864


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a telegram message to notify the developer."""
    # Log the error before we do anything else, so we can see it even if something breaks.
    logger.error("Exception while handling an update:", exc_info=context.error)

    # traceback.format_exception returns the usual python message about an exception, but as a
    # list of strings rather than a single string, so we have to join them together.
    tb_list = traceback.format_exception(
        None, context.error, context.error.__traceback__
    )
    tb_string = "".join(tb_list)
    global start_time
    timeSinceStarted = datetime.now() - start_time
    if (
        "telegram.error.Conflict" in tb_string
    ):  # A newer 2nd instance was registered. We should politely shutdown.
        if (
            timeSinceStarted.total_seconds() >= MINUTES_5_IN_SECONDS
        ):  # shutdown only if we have been running for over 5 minutes
            print(
                f"Stopping due to conflict after running for {timeSinceStarted.total_seconds()/60} minutes."
            )
            try:
                context.application.stop()
                sys.exit(0)
            except RuntimeError:
                context.application.shutdown()
            sys.exit(0)
        else:
            print("Other instance running!")
            # context.application.run_polling(allowed_updates=Update.ALL_TYPES)
    # Build the message with some markup and additional information about what happened.
    # You might need to add some logic to deal with messages longer than the 4096 character limit.
    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    message = (
        f"An exception was raised while handling an update\n"
        f"<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}"
        "</pre>\n\n"
        f"<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n"
        f"<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n"
        f"<pre>{html.escape(tb_string)}</pre>"
    )

    try:
        # Finally, send the message
        if "telegram.error.Conflict" not in message:
            await context.bot.send_message(
                chat_id=int(f"-{Channel_Id}"), text=message, parse_mode=ParseMode.HTML
            )
    except Exception:
        try:
            if "telegram.error.Conflict" not in tb_string:
                await context.bot.send_message(
                    chat_id=int(f"-{Channel_Id}"), text=tb_string, parse_mode=ParseMode.HTML
                )
        except Exception:
            print(tb_string)


async def command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is not None and (abs(update.message.from_user.id) in [
        Channel_Id,
        GROUP_CHAT_ID,
    ] or update.message.from_user.username in ["GroupAnonymousBot"]):
        # We want to avoid sending any help message back to channel or group.
        return START_ROUTES
    msg = update.effective_message
    m = re.match("\s*/([0-9a-zA-Z_-]+)\s*(.*)", msg.text)
    cmd = m.group(1).lower()
    args = [arg for arg in re.split("\s+", m.group(2)) if len(arg)]
    if cmd.startswith("cx_") or cmd.startswith("cb_"):
        await Level2(update=update, context=context)
        return START_ROUTES
    if cmd.startswith("cx"):
        await XScanners(update=update, context=context)
        return START_ROUTES
    if cmd.startswith("cb"):
        await XScanners(update=update, context=context)
        return START_ROUTES
    if cmd.startswith("cz"):
        await end(update=update, context=context)
        return END_ROUTES

    if cmd == "start":
        await start(update=update, context=context)
        return START_ROUTES
    if cmd == "help":
        await help_command(update=update, context=context)
        return START_ROUTES
    if cmd in ["x","b"]:
        await shareUpdateWithChannel(update=update, context=context)
        m0.renderForMenu(
            selectedMenu=None,
            skip=["S", "T", "E", "U", "Z"],
            renderStyle=MenuRenderStyle.STANDALONE,
        )
        selectedMenu = m0.find(cmd.upper())
        cmdText = ""
        cmds = m1.renderForMenu(
            selectedMenu=selectedMenu,
            skip=(["W", "E", "M", "Z"] if cmd in ["x"] else ["W", "E", "M", "Z","N","0"]),
            asList=True,
            renderStyle=MenuRenderStyle.STANDALONE,
        )
        for cmd in cmds:
            if cmd in ["N","0"]:
                continue
            cmdText = (
                f"{cmdText}\n\n{cmd.commandTextKey()} for {cmd.commandTextLabel()}"
            )
        if cmd in ["x"]:
            cmdText = f"{cmdText}\n\nFor option 0 <Screen stocks by the stock name>, please type in the command in the following format\n/X_0 SBIN\n or \n/X_0_0 SBIN\nand hit send where SBIN is the NSE stock code.For multiple stocks, you can type in \n/X_0 SBIN,ICICIBANK,OtherStocks\nYou can put in any number of stocks separated by space or comma(,)."
        """Send a message when the command /help is issued."""
        await update.message.reply_text(f"Choose an option:\n{cmdText}")
        return START_ROUTES

    if update.message is None:
        await help_command(update=update, context=context)
        return START_ROUTES
    if "x_0" in cmd or "x_0_0" in cmd or "b_0" in cmd:
        await shareUpdateWithChannel(update=update, context=context)
        shouldScan = False
        if len(args) > 0:
            shouldScan = True
            selection = [cmd.split("_")[0].upper(), "0", "0", f"{','.join(args)}".replace(" ", "")]
        if shouldScan:
            options = ":".join(selection)
            await launchScreener(
                options=options,
                user=update.message.from_user,
                context=context,
                optionChoices=cmd.upper(),
                update=update,
            )
            await sendRequestSubmitted(cmd.upper(), update=update, context=context)
            return START_ROUTES
        else:
            if cmd in ["x"]:
                cmdText = "For option 0 <Screen stocks by the stock name>, please type in the command in the following format\n/X_0 SBIN or /X_0_0 SBIN and hit send where SBIN is the NSE stock code.For multiple stocks, you can type in /X_0 SBIN,ICICIBANK,OtherStocks . You can put in any number of stocks separated by space or comma(,)."
            """Send a message when the command /help is issued."""
            await update.message.reply_text(f"Choose an option:\n{cmdText}")
            return START_ROUTES

    if "x_" in cmd or "b_" in cmd:
        await shareUpdateWithChannel(update=update, context=context)
        selection = cmd.split("_")
        if len(selection) == 2:
            m0.renderForMenu(
                selectedMenu=None,
                skip=["S", "T", "E", "U", "Z"],
                renderStyle=MenuRenderStyle.STANDALONE,
            )
            selectedMenu = m0.find(selection[0].upper())
            m1.renderForMenu(
                selectedMenu=selectedMenu,
                skip=(["W", "E", "M", "Z"] if "x_" in cmd else ["W", "E", "M", "Z","N","0"]),
                asList=True,
                renderStyle=MenuRenderStyle.STANDALONE,
            )
            selectedMenu = m1.find(selection[1].upper())
            if "x_" in cmd and selectedMenu.menuKey == "N":  # Nifty prediction
                options = ":".join(selection)
                await launchScreener(
                    options=options,
                    user=update.message.from_user,
                    context=context,
                    optionChoices=cmd.upper(),
                    update=update,
                )
                await sendRequestSubmitted(cmd.upper(), update=update, context=context)
                return START_ROUTES
            elif "x_" in cmd and selectedMenu.menuKey == "0":  # a specific stock by name
                cmdText = "For option 0 <Screen stocks by the stock name>, please type in the command in the following format\n/X_0 SBIN or /X_0_0 SBIN and hit send where SBIN is the NSE stock code.For multiple stocks, you can type in /X_0 SBIN,ICICIBANK,OtherStocks. You can put in any number of stocks separated by space or comma(,)."
                """Send a message when the command /help is issued."""
                await update.message.reply_text(f"Choose an option:\n{cmdText}")
                return START_ROUTES
            cmds = m2.renderForMenu(
                selectedMenu=selectedMenu,
                skip=[
                    "21",
                    "22",
                    "23",
                    "24",
                    "25",
                    "26",
                    "27",
                    "28",
                    "42",
                    "M",
                    "Z",
                ],
                asList=True,
                renderStyle=MenuRenderStyle.STANDALONE,
            )
            cmdText = ""
            for cmd in cmds:
                cmdText = (
                    f"{cmdText}\n\n{cmd.commandTextKey()} for {cmd.commandTextLabel()}"
                )
            await update.message.reply_text(f"Choose an option:\n{cmdText}")
            return START_ROUTES
        elif len(selection) == 3:
            m0.renderForMenu(
                selectedMenu=None,
                skip=["S", "T", "E", "U", "Z"],
                renderStyle=MenuRenderStyle.STANDALONE,
            )
            selectedMenu = m0.find(selection[0].upper())
            m1.renderForMenu(
                selectedMenu=selectedMenu,
                skip=(["W", "E", "M", "Z"] if "x_" in cmd else ["W", "E", "M", "Z","N","0"]),
                asList=True,
                renderStyle=MenuRenderStyle.STANDALONE,
            )
            selectedMenu = m1.find(selection[1].upper())
            m2.renderForMenu(
                selectedMenu=selectedMenu,
                skip=[
                    "21",
                    "22",
                    "23",
                    "24",
                    "25",
                    "26",
                    "27",
                    "28",
                    "42",
                    "M",
                    "Z",
                ],
                asList=True,
                renderStyle=MenuRenderStyle.STANDALONE,
            )
            if selection[2] in ["6", "7"]:
                selectedMenu = m2.find(selection[2].upper())
                cmds = m3.renderForMenu(
                    selectedMenu=selectedMenu,
                    asList=True,
                    renderStyle=MenuRenderStyle.STANDALONE,
                    skip=["0"],
                )
                cmdText = ""
                for cmd in cmds:
                    cmdText = f"{cmdText}\n\n{cmd.commandTextKey()} for {cmd.commandTextLabel()}"
                await update.message.reply_text(f"Choose an option:\n{cmdText}")
                return START_ROUTES
            else:
                if selection[2] == "4":  # Last N days
                    selection.extend(["4", ""])
                elif selection[2] == "5":  # RSI range
                    selection.extend(["67", "71"])
                elif selection[2] == "8":  # CCI range
                    selection.extend(["-100", "150"])
                elif selection[2] == "9":  # Vol gainer ratio
                    selection.extend(["2.5", ""])
                elif selection[2] in [
                    "1",
                    "2",
                    "3",
                    "10",
                    "11",
                    "12",
                    "13",
                    "14",
                    "15",
                    "16",
                    "17",
                    "18",
                    "19",
                    "20"
                ]:  # Vol gainer ratio
                    selection.extend(["", ""])
        if len(selection) >= 4:
            options = ":".join(selection)
            await launchScreener(
                options=options,
                user=update.message.from_user,
                context=context,
                optionChoices=cmd.upper(),
                update=update,
            )
            await sendRequestSubmitted(cmd.upper(), update=update, context=context)
            return START_ROUTES
    if cmd == "y" or cmd == "h":
        await shareUpdateWithChannel(update=update, context=context)
        await launchScreener(
            options=f"{cmd.upper()}:",
            user=update.message.from_user,
            context=context,
            optionChoices=cmd.upper(),
            update=update,
        )
        await sendRequestSubmitted(cmd.upper(), update=update, context=context)
        return START_ROUTES
    await update.message.reply_text(f"{cmd.upper()} : Not implemented yet!")
    await help_command(update=update, context=context)


async def sendRequestSubmitted(optionChoices, update, context):
    menuText = f"Thank you for choosing {optionChoices}. You will receive the results soon! \n\nConsider donating to help keep this project going:\nUPI: 8007162973@APL \nor\nhttps://github.com/sponsors/pkjmesra?frequency=one-time&sponsor=pkjmesra\n\nSince it is running on a low-end server, it might take from a few seconds to a few minutes. You will get notified here when the results arrive!"
    await update.message.reply_text(menuText)
    await help_command(update=update, context=context)
    await shareUpdateWithChannel(
        update=update, context=context, optionChoices=optionChoices
    )


async def shareUpdateWithChannel(update, context, optionChoices=""):
    query = update.message
    message = f"Name: <b>{query.from_user.first_name}</b>, Username:@{query.from_user.username} with ID: <b>@{str(query.from_user.id)}</b> began using ({optionChoices}) the bot!"
    await context.bot.send_message(
        chat_id=int(f"-{Channel_Id}"), text=message, parse_mode=ParseMode.HTML
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    sentFrom = []
    if update.callback_query is not None:
        sentFrom.append(abs(update.callback_query.from_user.id))
    if update.message is not None and update.message.from_user is not None:
        sentFrom.append(abs(update.message.from_user.id))
    if update.channel_post is not None:
        if update.channel_post.chat is not None:
            sentFrom.append(abs(update.channel_post.chat.id))
        if update.channel_post.sender_chat is not None:
            sentFrom.append(abs(update.channel_post.sender_chat.id))

    if abs(int(Channel_Id)) in sentFrom or abs(int(GROUP_CHAT_ID)) in sentFrom:
        # We want to avoid sending any help message back to channel
        # or group in response to our own messages
        return

    cmds = m0.renderForMenu(
        selectedMenu=None,
        skip=["S", "T", "E", "U", "Z", "S"],
        asList=True,
        renderStyle=MenuRenderStyle.STANDALONE,
    )
    cmdText = ""
    for cmd in cmds:
        cmdText = f"{cmdText}\n\n{cmd.commandTextKey()} for {cmd.commandTextLabel()}"
    """Send a message when the command /help is issued."""
    await update.message.reply_text(
        f"You can begin by typing in /start and hit send!\n\nOR\n\nChoose an option:\n{cmdText}"
    )  #  \n\nThis bot restarts every hour starting at 5:30am IST until 10:30pm IST to keep it running on free servers. If it does not respond, please try again in a minutes to avoid the restart duration!
    query = update.message
    message = f"Name: <b>{query.from_user.first_name}</b>, Username:@{query.from_user.username} with ID: <b>@{str(query.from_user.id)}</b> began using the bot!"
    await context.bot.send_message(
        chat_id=int(f"-{Channel_Id}"), text=message, parse_mode=ParseMode.HTML
    )


def addCommandsForMenuItems(application):
    cmds0 = m0.renderForMenu(
        selectedMenu=None,
        skip=["S", "T", "E", "U", "Z"],
        asList=True,
        renderStyle=MenuRenderStyle.STANDALONE,
    )
    for mnu0 in cmds0:
        p0 = mnu0.menuKey.upper()
        application.add_handler(CommandHandler(p0, command_handler))
        selectedMenu = m0.find(p0)
        cmds1 = m1.renderForMenu(
            selectedMenu=selectedMenu,
            skip=(["W", "E", "M", "Z"] if p0 == "X" else ["W", "E", "M", "Z","N","0"]),
            asList=True,
            renderStyle=MenuRenderStyle.STANDALONE,
        )
        for mnu1 in cmds1:
            p1 = mnu1.menuKey.upper()
            if p1 in ["N","0"]:
                continue
            application.add_handler(CommandHandler(f"{p0}_{p1}", command_handler))
            selectedMenu = m1.find(p1)
            cmds2 = m2.renderForMenu(
                selectedMenu=selectedMenu,
                skip=[
                    "21",
                    "22",
                    "23",
                    "24",
                    "25",
                    "26",
                    "27",
                    "28",
                    "42",
                    "M",
                    "Z",
                ],
                asList=True,
                renderStyle=MenuRenderStyle.STANDALONE,
            )
            for mnu2 in cmds2:
                p2 = mnu2.menuKey.upper()
                application.add_handler(
                    CommandHandler(f"{p0}_{p1}_{p2}", command_handler)
                )
                if p2 in ["6", "7"]:
                    selectedMenu = m2.find(p2)
                    cmds3 = m3.renderForMenu(
                        selectedMenu=selectedMenu,
                        asList=True,
                        renderStyle=MenuRenderStyle.STANDALONE,
                        skip=["0"],
                    )
                    for mnu3 in cmds3:
                        p3 = mnu3.menuKey.upper()
                        application.add_handler(
                            CommandHandler(f"{p0}_{p1}_{p2}_{p3}", command_handler)
                        )


def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    global chat_idADMIN, Channel_Id
    Channel_Id, TOKEN, chat_idADMIN,GITHUB_TOKEN = get_secrets()
    # TOKEN = '1234567'
    # Channel_Id = 1001785195297
    application = Application.builder().token(TOKEN).build()
    # Setup conversation handler with the states FIRST and SECOND
    # Use the pattern parameter to pass CallbackQueries with specific
    # data pattern to the corresponding handlers.
    # ^ means "start of line/string"
    # $ means "end of line/string"
    # So ^ABC$ will only allow 'ABC'
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            START_ROUTES: [
                CallbackQueryHandler(XScanners, pattern="^" + str("CX") + "$"),
                CallbackQueryHandler(XScanners, pattern="^" + str("CB") + "$"),
                CallbackQueryHandler(Level2, pattern="^" + str("CX_")),
                CallbackQueryHandler(Level2, pattern="^" + str("CB_")),
                CallbackQueryHandler(end, pattern="^" + str("CZ") + "$"),
                CallbackQueryHandler(start, pattern="^"),
            ],
            END_ROUTES: [],
        },
        fallbacks=[CommandHandler("start", start)],
    )
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, help_command)
    )
    # application.add_handler(MessageHandler(filters.TEXT & filters.COMMAND, command_handler))
    # application.add_handler(MessageHandler(filters.COMMAND, command_handler))
    # Add ConversationHandler to application that will be used for handling updates
    addCommandsForMenuItems(application)
    application.add_handler(conv_handler)
    # ...and the error handler
    application.add_error_handler(error_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
