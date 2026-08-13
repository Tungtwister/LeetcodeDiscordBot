import discord
from discord import app_commands
from discord.ext import commands

import db

SESSION_TYPES = [
    app_commands.Choice(name="LeetCode", value="leetcode"),
    app_commands.Choice(name="System Design", value="system_design"),
]

DIFFICULTIES = [
    app_commands.Choice(name="Easy", value="easy"),
    app_commands.Choice(name="Medium", value="medium"),
    app_commands.Choice(name="Hard", value="hard"),
]


class Checkin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="checkin", description="Log a practice session")
    @app_commands.choices(session_type=SESSION_TYPES, difficulty=DIFFICULTIES)
    @app_commands.describe(
        session_type="What kind of practice",
        topic="Problem name or system design topic",
        difficulty="LeetCode difficulty (optional)",
        minutes="Minutes spent (optional)",
        notes="Any notes (optional)",
    )
    async def checkin(
        self,
        interaction: discord.Interaction,
        session_type: app_commands.Choice[str],
        topic: str = None,
        difficulty: app_commands.Choice[str] = None,
        minutes: int = None,
        notes: str = None,
    ):
        user_id = str(interaction.user.id)
        db.add_session(
            user_id=user_id,
            username=interaction.user.display_name,
            session_type=session_type.value,
            topic=topic,
            difficulty=difficulty.value if difficulty else None,
            minutes=minutes,
            notes=notes,
        )
        streak = db.current_streak(user_id)

        embed = discord.Embed(title="Checked in", color=discord.Color.green())
        embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
        embed.add_field(name="Type", value=session_type.name, inline=True)
        if topic:
            embed.add_field(name="Topic", value=topic, inline=True)
        if difficulty:
            embed.add_field(name="Difficulty", value=difficulty.name, inline=True)
        if minutes:
            embed.add_field(name="Minutes", value=str(minutes), inline=True)
        if notes:
            embed.add_field(name="Notes", value=notes, inline=False)
        embed.set_footer(text=f"Current streak: {streak} day{'s' if streak != 1 else ''} \U0001F525")

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Checkin(bot))
