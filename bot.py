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

# Optional. Global command changes can take up to an hour to appear in the Discord
# client, which makes iterating painful. Syncing to a single guild is instant, so set
# GUILD_ID to your server's ID while developing.
GUILD_ID = os.environ.get("GUILD_ID", "").strip()

intents = discord.Intents.default()


class LeetcodeBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        db.init_db()
        await self.load_extension("cogs.checkin")
        await self.load_extension("cogs.stats")
        await self.load_extension("cogs.reminders")

        if GUILD_ID:
            guild = discord.Object(id=int(GUILD_ID))
            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild)
            log.info(
                "Synced %d commands to guild %s (appears immediately): %s",
                len(synced), GUILD_ID, ", ".join(f"/{c.name}" for c in synced),
            )
        else:
            synced = await self.tree.sync()
            log.info(
                "Synced %d commands globally (can take up to an hour to appear): %s",
                len(synced), ", ".join(f"/{c.name}" for c in synced),
            )

    async def on_ready(self):
        log.info("Logged in as %s (%s)", self.user, self.user.id)


def main():
    bot = LeetcodeBot()
    bot.run(TOKEN)


if __name__ == "__main__":
    main()
