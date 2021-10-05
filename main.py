import discord
import logging
import os
import sqlite3

from discord.ext import commands
from ext.context import Context
from typing import TypeVar, Generator, Iterable

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

ctx = TypeVar("ctx", bound=Context)


class BotBase(commands.Bot):
    def __init__(self, command_prefix, **kwargs):
        self.log = logger
        super().__init__(command_prefix, **kwargs)
        self.db1 = sqlite3.connect("achievements.db")
        self.db2 = sqlite3.connect("donation.db")
        self.base_color = 0xff6666

    def load_extension(self, names: Iterable, package=None):
        for name in names:
            super().load_extension(name)
            yield name

    async def start(self, *args, **kwargs):
        self.log.info("Started loading cogs.")
        loaded: Generator = self.load_extension([f"cogs.{file[:-3]}"for file in os.listdir("cogs")
                                                 if file.endswith(".py") and not file.startswith("_")])
        fl = [cog for cog in loaded]
        self.log.info("Finished loading %r cogs: %r", len(fl), fl,)
        await super().start(*args, **kwargs)

    async def close(self):
        self.db1.close()
        self.db2.close()
        await super().close()

    async def get_context(self, message: discord.Message, *, cls: ctx = Context) -> ctx:
        return await super().get_context(message=message, cls=cls)


bot = BotBase(command_prefix=['i!', "I!"],
              intents=discord.Intents.all(),
              case_insensitive=True,
              status=discord.Game(
                  name="Monitoring server . ."
                )
              ).run(os.getenv("TOKEN"))
