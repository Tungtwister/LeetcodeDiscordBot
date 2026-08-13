import discord
from discord import app_commands
from discord.ext import commands

import db


class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="stats", description="Show your (or someone else's) practice stats")
    @app_commands.describe(member="Whose stats to show (defaults to you)")
    async def stats(self, interaction: discord.Interaction, member: discord.Member = None):
        target = member or interaction.user
        s = db.user_stats(str(target.id))

        embed = discord.Embed(title=f"{target.display_name}'s stats", color=discord.Color.blurple())
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="Current streak", value=f"{s['current_streak']} \U0001F525", inline=True)
        embed.add_field(name="Longest streak", value=f"{s['longest_streak']} days", inline=True)
        embed.add_field(name="Days this week", value=f"{s['days_this_week']}/7", inline=True)
        embed.add_field(name="Total sessions", value=str(s["total"]), inline=True)
        embed.add_field(name="LeetCode", value=str(s["by_type"].get("leetcode", 0)), inline=True)
        embed.add_field(name="System Design", value=str(s["by_type"].get("system_design", 0)), inline=True)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="leaderboard", description="Compare everyone's streaks and totals")
    async def leaderboard(self, interaction: discord.Interaction):
        board = db.leaderboard()
        if not board:
            await interaction.response.send_message("No check-ins logged yet.")
            return

        lines = [
            f"**{i}. {row['username']}** — \U0001F525 {row['current_streak']} streak, "
            f"{row['total']} sessions total (last: {row['last_date']})"
            for i, row in enumerate(board, start=1)
        ]

        embed = discord.Embed(
            title="Leaderboard",
            description="\n".join(lines),
            color=discord.Color.gold(),
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="history", description="Show recent practice sessions")
    @app_commands.describe(member="Whose history to show (defaults to you)", limit="How many to show (default 5)")
    async def history(self, interaction: discord.Interaction, member: discord.Member = None, limit: int = 5):
        target = member or interaction.user
        rows = db.recent_sessions(str(target.id), limit=limit)
        if not rows:
            await interaction.response.send_message(f"{target.display_name} hasn't logged any sessions yet.")
            return

        lines = []
        for r in rows:
            label = "LeetCode" if r["session_type"] == "leetcode" else "System Design"
            bits = [f"**{r['session_date']}** — {label}"]
            if r["topic"]:
                bits.append(r["topic"])
            if r["difficulty"]:
                bits.append(r["difficulty"])
            if r["minutes"]:
                bits.append(f"{r['minutes']}m")
            lines.append(" · ".join(bits))

        embed = discord.Embed(
            title=f"{target.display_name}'s recent sessions",
            description="\n".join(lines),
            color=discord.Color.blurple(),
        )
        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Stats(bot))
