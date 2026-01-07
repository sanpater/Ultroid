# Ultroid - UserBot
# Copyright (C) 2021-2025 TeamUltroid
#
# This file is a part of < https://github.com/TeamUltroid/Ultroid/ >
# PLease read the GNU Affero General Public License in
# <https://github.com/TeamUltroid/pyUltroid/blob/main/LICENSE>.

import os
import sys
import telethonpatch
from .version import __version__

run_as_module = __package__ in sys.argv or sys.argv[0] == "-m"


class ULTConfig:
    lang = "en"
    thumb = "resources/extras/ultroid.jpg"


if run_as_module:
    import time

    from .configs import Var
    from .startup import *
    from .startup._database import UltroidDB
    from .startup.BaseClient import UltroidClient
    from .startup.connections import validate_session, vc_connection
    from .startup.funcs import _version_changes, autobot, enable_inline, update_envs
    from .version import ultroid_version

    if not os.path.exists("./plugins"):
        LOGS.error(
            "'plugins' folder not found!\nMake sure that, you are on correct path."
        )
        exit()

    start_time = time.time()
    _ult_cache = {}
    _ignore_eval = []

    udB = UltroidDB()
    update_envs()

    LOGS.info(f"Connecting to {udB.name}...")
    if udB.ping():
        LOGS.info(f"Connected to {udB.name} Successfully!")

    BOT_MODE = udB.get_key("BOTMODE")
    DUAL_MODE = udB.get_key("DUAL_MODE")

    USER_MODE = udB.get_key("USER_MODE")
    if USER_MODE:
        DUAL_MODE = False

    if BOT_MODE:
        if DUAL_MODE:
            udB.del_key("DUAL_MODE")
            DUAL_MODE = False
        ultroid_bot = None

        if not udB.get_key("BOT_TOKEN"):
            LOGS.critical(
                '"BOT_TOKEN" not Found! Please add it, in order to use "BOTMODE"'
            )

            sys.exit()
    else:
        ultroid_bot = UltroidClient(
            validate_session(Var.SESSION, LOGS),
            udB=udB,
            app_version=ultroid_version,
            device_model="Ultroid",
        )
        ultroid_bot.run_in_loop(autobot())

    if USER_MODE:
        asst = ultroid_bot
    else:
        asst = UltroidClient("asst", bot_token=udB.get_key("BOT_TOKEN"), udB=udB)

    if BOT_MODE:
        ultroid_bot = asst
        if udB.get_key("OWNER_ID"):
            try:
                ultroid_bot.me = ultroid_bot.run_in_loop(
                    ultroid_bot.get_entity(udB.get_key("OWNER_ID"))
                )
            except Exception as er:
                LOGS.exception(er)
    elif not asst.me.bot_inline_placeholder and asst._bot:
        ultroid_bot.run_in_loop(enable_inline(ultroid_bot, asst.me.username))

    # ─────────────────────────────
    # SEPARATE VC CLIENT
    # ─────────────────────────────
    from telethon import TelegramClient
    from telethon.sessions import StringSession
    try:
        from pytgcalls import PyTgCalls
    except ImportError:
        os.system("pip3 install -q py-tgcalls==2.2.8")
        from pytgcalls import PyTgCalls
    
    class VCClient:
        def __init__(self, udB):
            # Fetch isolated credentials
            self.api_id = udB.get_key("VC_API_ID") or udB.get_key("API_ID") or Var.API_ID
            self.api_hash = udB.get_key("VC_API_HASH") or udB.get_key("API_HASH") or Var.API_HASH
            self.session_str = udB.get_key("VC_SESSION")

        # Decide session type
            if self.session_str:
                self.client = TelegramClient(
                    StringSession(self.session_str),
                    self.api_id,
                    self.api_hash
                )
                session_mode = "StringSession"
            else:
                self.client = TelegramClient(
                    "vc",  # fallback file-based session
                    self.api_id,
                    self.api_hash
                )
                session_mode = "LocalSession"

        # Setup VC Layer
            self.tgcalls = PyTgCalls(self.client)
            LOGS.info(f"VCClient initialized with {session_mode} using udB credentials.")

        async def start(self):
            await self.tgcalls.start()
            LOGS.info("VCClient started successfully with isolated Telethon session.")


    # Instantiate and start (non-blocking)
    try:
        vcclient = VCClient(udB)
        ultroid_bot.run_in_loop(vcclient.start())
    except:
        vcclient = None

    _version_changes(udB)

    HNDLR = udB.get_key("HNDLR") or "."
    DUAL_HNDLR = udB.get_key("DUAL_HNDLR") or "/"
    SUDO_HNDLR = udB.get_key("SUDO_HNDLR") or HNDLR

else:
    from logging import getLogger

    LOGS = getLogger("pyUltroid")
    ultroid_bot = asst = udB = vcclient = None
    print("pyUltroid 2022 © TeamUltroid")
