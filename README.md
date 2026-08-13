# LeetCode Accountability Bot

A Discord bot for keeping you and a friend honest about LeetCode and system design
practice. Log sessions with `/checkin`, compare progress with `/leaderboard`, and get
a daily nudge in a shared channel if either of you hasn't checked in yet.

## Commands

- `/checkin` — log a practice session (LeetCode or System Design), with optional
  topic, difficulty, minutes spent, and notes. Replies with your current streak.
- `/stats [member]` — current streak, longest streak, days practiced this week, and
  totals by type. Defaults to you; pass a member to check theirs.
- `/leaderboard` — everyone who has checked in, ranked by current streak then total
  sessions — the head-to-head view.
- `/history [member] [limit]` — recent sessions, most recent first.
- `/reminderinfo` — when the next daily reminder fires, which channel it posts to, and
  who it would ping right now. Flags misconfiguration. Only you see the reply.
- `/testreminder` — fire the daily reminder immediately instead of waiting for the
  scheduled time. Posts for real in the reminder channel.

Every night at a configured time, the bot posts in one channel and `@`-mentions
anyone who hasn't logged a session that day.

## Testing the reminder

Rather than waiting until `REMINDER_HOUR`, run `/reminderinfo` to confirm the channel
and tracked users resolve correctly, then `/testreminder` to send one immediately. If
something's misconfigured — wrong channel ID, bot lacks permission to post there,
empty `TRACKED_USER_IDS` — `/testreminder` tells you exactly which, instead of failing
silently the way a missed scheduled run would.

## One-time setup

### 1. Create the Discord bot
1. Go to https://discord.com/developers/applications -> **New Application**.
2. **Bot** tab -> **Reset Token** -> copy it (this is `DISCORD_BOT_TOKEN`). Keep it
   secret — anyone with it can control the bot.
3. **OAuth2 -> URL Generator**: check scopes `bot` and `applications.commands`; under
   Bot Permissions check `Send Messages`, `Embed Links`, `Use Slash Commands`. Open
   the generated URL and invite the bot to your shared server.

### 2. Get the IDs you need
Turn on Developer Mode first: Discord **User Settings -> Advanced -> Developer Mode**.
- Right-click the channel for reminders -> **Copy Channel ID** -> `REMINDER_CHANNEL_ID`.
- Right-click each friend (yourself included) -> **Copy User ID** -> comma-separate
  them into `TRACKED_USER_IDS`.

### 3. Configure
```powershell
copy .env.example .env
```
Fill in `DISCORD_BOT_TOKEN`, `REMINDER_CHANNEL_ID`, `TRACKED_USER_IDS`, and adjust
`APP_TIMEZONE` / `REMINDER_HOUR` / `REMINDER_MINUTE` to taste.

### 4. Install & run locally (to test)
```powershell
pip install -r requirements.txt
python bot.py
```
Slash commands sync to every server the bot is in on startup — they usually show up
within a minute or two.

## Deploying so it runs 24/7

The bot needs a persistent connection to Discord, so it must run as a long-lived
process rather than a scheduled task. [Railway](https://railway.app) is the easiest
free-tier option with persistent storage:

1. Push this repo to GitHub.
2. In Railway: **New Project -> Deploy from GitHub repo**, pick the repo.
3. Railway detects the `Procfile` and runs `python bot.py` as a worker automatically.
4. **Variables** tab: add everything from `.env.example` (same names/values).
5. **Add a Volume**: Settings -> Volumes -> mount at `/data`. Set the `DB_PATH`
   variable to `/data/leetcode.db` so check-ins survive future deploys — without a
   volume, the SQLite file resets every time you redeploy.
6. Deploy. Check the logs for `Logged in as ...` to confirm it's connected.

Fly.io and Render work too (Render's free tier has no persistent disk, so use Railway
or Fly.io if you want check-in history to survive redeploys without paying).

## Notes
- `.env` and `*.db` are gitignored — never commit your bot token or local data.
- Data lives in one SQLite file (`leetcode.db` by default). For two people this is
  plenty; no external database needed. A relative `DB_PATH` resolves against the
  project folder, not your shell's working directory, so the database stays in the
  same place no matter where you launch the bot from.
- To add more people to the reminder ping later, just extend `TRACKED_USER_IDS` —
  everyone can still use `/checkin` and show up on `/leaderboard` regardless.
