import logging
import os
from datetime import datetime, time

import discord
from discord import app_commands
from discord.ext import commands, tasks

import db
from config import TZ

log = logging.getLogger("leetcode-bot")

REMINDER_HOUR = int(os.environ.get("REMINDER_HOUR", "18"))
REMINDER_MINUTE = int(os.environ.get("REMINDER_MINUTE", "0"))
REMINDER_CHANNEL_ID = int(os.environ["REMINDER_CHANNEL_ID"])
TRACKED_USER_IDS = [uid.strip() for uid in os.environ.get("TRACKED_USER_IDS", "").split(",") if uid.strip()]

REMINDER_TIME = time(hour=REMINDER_HOUR, minute=REMINDER_MINUTE, tzinfo=TZ)


class ReminderError(Exception):
    """Config/permission problem that would make the daily reminder silently fail."""


class Reminders(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.daily_reminder.start()

    def cog_unload(self):
        self.daily_reminder.cancel()

    async def send_reminder(self):
        """Post the reminder. Returns the message text sent.

        Raises ReminderError on the misconfigurations that would otherwise make the
        scheduled run do nothing at all.
        """
        if not TRACKED_USER_IDS:
            raise ReminderError(
                "TRACKED_USER_IDS is empty — nobody would be reminded. "
                "Add Discord user IDs to it in your .env."
            )

        channel = self.bot.get_channel(REMINDER_CHANNEL_ID)
        if channel is None:
            raise ReminderError(
                f"Can't see channel {REMINDER_CHANNEL_ID}. Check REMINDER_CHANNEL_ID "
                f"is correct and the bot has access to that channel."
            )

        missing = [uid for uid in TRACKED_USER_IDS if not db.checked_in_today(uid)]
        if missing:
            mentions = " ".join(f"<@{uid}>" for uid in missing)
            text = (
                f"{mentions} — no LeetCode/system design check-in logged today yet. "
                f"Use `/checkin` before the day's out!"
            )
        else:
            text = "Everyone's checked in today. Nice work."

        try:
            await channel.send(text)
        except discord.Forbidden as e:
            raise ReminderError(
                f"Missing permission to post in #{channel.name}. Give the bot "
                f"'Send Messages' there."
            ) from e
        return text

    @tasks.loop(time=REMINDER_TIME)
    async def daily_reminder(self):
        try:
            await self.send_reminder()
        except ReminderError as e:
            log.error("Daily reminder failed: %s", e)

    @daily_reminder.before_loop
    async def before_daily_reminder(self):
        await self.bot.wait_until_ready()

    @app_commands.command(
        name="testreminder",
        description="Fire the daily reminder right now to test it",
    )
    async def testreminder(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            await self.send_reminder()
        except ReminderError as e:
            await interaction.followup.send(f"Reminder failed: {e}", ephemeral=True)
            return
        await interaction.followup.send("Reminder sent to the reminder channel.", ephemeral=True)

    @app_commands.command(
        name="reminderinfo",
        description="Show when the next daily reminder fires and who it will ping",
    )
    async def reminderinfo(self, interaction: discord.Interaction):
        next_run = self.daily_reminder.next_iteration
        channel = self.bot.get_channel(REMINDER_CHANNEL_ID)

        pending = [uid for uid in TRACKED_USER_IDS if not db.checked_in_today(uid)]

        embed = discord.Embed(title="Reminder settings", color=discord.Color.blurple())
        embed.add_field(
            name="Scheduled for",
            value=f"{REMINDER_HOUR:02d}:{REMINDER_MINUTE:02d} {TZ.key}",
            inline=False,
        )
        embed.add_field(
            name="Next run",
            value=(
                f"<t:{int(next_run.timestamp())}:R>" if next_run else "not scheduled"
            ),
            inline=False,
        )
        embed.add_field(
            name="Channel",
            value=channel.mention if channel else f"⚠️ can't see channel {REMINDER_CHANNEL_ID}",
            inline=False,
        )
        embed.add_field(
            name="Tracked",
            value=" ".join(f"<@{uid}>" for uid in TRACKED_USER_IDS) or "⚠️ nobody (TRACKED_USER_IDS is empty)",
            inline=False,
        )
        embed.add_field(
            name="Would ping right now",
            value=" ".join(f"<@{uid}>" for uid in pending) or "nobody — everyone's checked in",
            inline=False,
        )
        embed.set_footer(text=f"Bot time: {datetime.now(TZ):%Y-%m-%d %H:%M %Z}")

        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(Reminders(bot))
