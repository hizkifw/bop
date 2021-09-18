# bop

Discord music bot using discord.py, slash commands, and yt-dlp.

## Features

- Play music from YouTube videos and playlists
- Queue system with shuffle
- Skip songs

## Running the bot

Install [Docker](https://www.docker.com/), then pull and run the image:

```bash
docker pull hizkifw/discord-bop:latest
docker run --rm -e BOT_TOKEN="insert_bot_token_here" -e GUILD_IDS="[1234567890123456789]" hizkifw/discord-bop:latest
```

- `BOT_TOKEN`: discord bot token
- `GUILD_IDS`: json int array of guild ids, e.g. `[730136766748819609, 1189998819991197253]`
