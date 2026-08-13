import logging
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

import db

load_dotenv()

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("leetcode-bot")

TOKEN = os.environ["DISCORD_BOT_TOKEN"]

intents = discord.Intents.default()


class LeetcodeBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        db.init_db()
        await self.load_extension("cogs.checkin")
        await self.load_extension("cogs.stats")
        await self.load_extension("cogs.reminders")
        await self.tree.sync()
        log.info("Slash commands synced")

    async def on_ready(self):
        log.info("Logged in as %s (%s)", self.user, self.user.id)


def main():
    bot = LeetcodeBot()
    bot.run(TOKEN)


if __name__ == "__main__":
    main()
