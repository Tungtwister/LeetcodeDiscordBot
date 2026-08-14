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

## Troubleshooting slash commands

**"The application did not respond"** — the bot process isn't running, or the running
process is older than the command you invoked. Discord waits 3 seconds for a reply and
gives up. Restart `bot.py` and make sure only one instance is running; two copies of
the bot (or one left over from an old folder) will fight over the same commands.

**A command doesn't appear** — set `GUILD_ID` in `.env`. Without it, commands register
globally and Discord can take an hour to show new ones. With it, they appear as soon as
the bot starts. Press Ctrl+R in Discord to reload the client's cached command list.

**A command appears twice** — it's registered both globally and per-guild. Drop the
global copies:
```powershell
python sync_commands.py --clear-global
```
`python sync_commands.py --list` shows exactly what Discord currently has registered,
which is the fastest way to tell a propagation delay from a real bug.

## Running it 24/7

The bot holds an open connection to Discord, so it needs a long-lived process — it
can't be a scheduled task that exits. When the process stops, every slash command
returns "The application did not respond".

Hosting options as of 2026:

| Option | Cost | Notes |
| --- | --- | --- |
| [Railway Free plan](https://railway.com/pricing) | $0 + usage | $1/mo of included credits; this bot uses ~$0.75-1.00/mo, so it usually fits. Easiest setup. |
| Your own PC | free | Offline whenever the machine sleeps. Fine for a small group. |
| Oracle Cloud Always Free | free | Genuinely free 24/7 VM, but you administer a Linux box. |
| [Fly.io](https://fly.io/docs/about/pricing/) | ~$2/mo | No free tier for accounts created after Oct 2024. |
| Render free tier | free | **Won't work** — free services sleep after 15 min idle. |

Railway bills per second for what you actually use: memory at $10/GB/month, CPU at
$20/vCPU/month, volumes at ~$0.16/GB/month. A Discord bot is idle almost always — it
just holds a websocket open — so CPU is effectively free (~0.03% of a vCPU measured)
and memory (~70 MB) is the whole bill. On the Free plan with no card on file, Railway
pauses the service if you exceed the credit rather than charging you.

### Option A — your own machine (free)

Run `python bot.py` and leave it running. To survive reboots on Windows, register a
scheduled task that runs at logon and restarts on failure. The bot is idle almost all
the time; it costs a few dozen MB of RAM.

### Option B — a cloud host (~$2-5/mo)

Any host that runs a background worker will do. The repo is already set up for it:
`Procfile` declares the worker command, and all config comes from environment
variables rather than files.

1. Push this repo to GitHub.
2. Point the host at the repo; it installs `requirements.txt` and runs the `Procfile`
   worker (`python bot.py`).
3. Set the environment variables from `.env.example` in the host's dashboard. Never
   commit the real values.
4. **Attach a persistent volume** and set `DB_PATH` to a path on it (e.g.
   `/data/leetcode.db`). Without one, every redeploy wipes your streak history,
   because the SQLite file lives on the container's ephemeral disk.
5. Check the logs for `Logged in as ...`.

Note that a cloud instance and a local instance running at the same time will both
answer every command, and they keep separate databases. Run one or the other.

## Notes
- `.env` and `*.db` are gitignored — never commit your bot token or local data.
- Data lives in one SQLite file (`leetcode.db` by default). For two people this is
  plenty; no external database needed. A relative `DB_PATH` resolves against the
  project folder, not your shell's working directory, so the database stays in the
  same place no matter where you launch the bot from.
- To add more people to the reminder ping later, just extend `TRACKED_USER_IDS` —
  everyone can still use `/checkin` and show up on `/leaderboard` regardless.
