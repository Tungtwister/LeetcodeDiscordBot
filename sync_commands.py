"""Maintenance script for the bot's slash-command registrations.

Discord keeps two separate sets of commands: global ones (slow to propagate, up to
an hour) and per-guild ones (instant). If the same command exists in both, it shows
up twice in the Discord picker. Normal runs of bot.py never need this script — reach
for it when the command list is wrong.

    python sync_commands.py --list           # show what Discord currently has
    python sync_commands.py --clear-global   # drop global copies, keep guild ones
    python sync_commands.py --clear-guild    # drop guild copies, keep global ones
"""

import argparse
import asyncio
import os
import sys

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.environ["DISCORD_BOT_TOKEN"]
GUILD_ID = os.environ.get("GUILD_ID", "").strip()

EXTENSIONS = ("cogs.checkin", "cogs.stats", "cogs.reminders")


async def run(action):
    bot = commands.Bot(command_prefix="!", intents=discord.Intents.default())
    for ext in EXTENSIONS:
        await bot.load_extension(ext)

    await bot.login(TOKEN)

    guild = discord.Object(id=int(GUILD_ID)) if GUILD_ID else None

    if action == "list":
        pass
    elif action == "clear-global":
        bot.tree.clear_commands(guild=None)
        await bot.tree.sync()
        print("Cleared global commands.")
        if guild:
            bot.tree.copy_global_to(guild=guild)
    elif action == "clear-guild":
        if not guild:
            print("GUILD_ID is not set — nothing to clear.")
        else:
            bot.tree.clear_commands(guild=guild)
            await bot.tree.sync(guild=guild)
            print(f"Cleared guild commands for {GUILD_ID}.")

    global_cmds = await bot.tree.fetch_commands()
    print(f"\nGlobal commands ({len(global_cmds)}): "
          f"{', '.join('/' + c.name for c in global_cmds) or 'none'}")

    if guild:
        guild_cmds = await bot.tree.fetch_commands(guild=guild)
        print(f"Guild commands  ({len(guild_cmds)}): "
              f"{', '.join('/' + c.name for c in guild_cmds) or 'none'}")

    await bot.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--list", action="store_true", help="show current registrations")
    group.add_argument("--clear-global", action="store_true", help="remove global copies")
    group.add_argument("--clear-guild", action="store_true", help="remove guild copies")
    args = parser.parse_args()

    if args.clear_global:
        action = "clear-global"
    elif args.clear_guild:
        action = "clear-guild"
    else:
        action = "list"

    asyncio.run(run(action))


if __name__ == "__main__":
    main()
