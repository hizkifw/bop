# bop

Discord music bot using discord.py, slash commands, and yt-dlp.

## Features

- Play music from YouTube videos and playlists
- Queue system with shuffle
- Skip songs
- Loop a song or the whole queue

## Running the bot

Install [Docker](https://www.docker.com/), then pull and run the image:

```bash
docker pull hizkifw/discord-bop:latest
docker run --rm -e BOT_TOKEN="insert_bot_token_here" -e GUILD_IDS="[1234567890123456789]" hizkifw/discord-bop:latest
```

- `BOT_TOKEN`: discord bot token
- `GUILD_IDS`: json int array of guild ids, e.g. `[730136766748819609, 1189998819991197253]`

## Command reference

<table>
  <tr>
    <th>Command</th>
    <th>Description</th>
  </tr>
  <tr>
    <td>
      <code>/join</code>
    </td>
    <td>
      Join the voice channel you are currently in.
    </td>
  </tr>
  <tr>
    <td>
      <code>/leave</code>
    </td>
    <td>
      Leave the voice channel it is currently in.
    </td>
  </tr>
  <tr>
    <td>
      <code>/play</code>
      <code>query</code>
    </td>
    <td>
      <p>
        Add a song to the end of the queue. <code>query</code> can either be a
        YouTube video or playlist URL, a search term, or a number.
      </p>
      <ul>
        <li>
          When given a playlist URL, will add all videos in the playlist to the
          back of the queue.
        </li>
        <li>
          When given a search term, will pick the top result from YouTube search
          and add it to the end of the queue.
        </li>
        <li>
          When given a number, will skip playback to that song number in the queue.
        </li>
      </ul>
    </td>
  </tr>
  <tr>
    <td>
      <code>/pause</code>
    </td>
    <td>
      Pause the current song.
    </td>
  </tr>
  <tr>
    <td>
      <code>/resume</code>
    </td>
    <td>
      Unpause the current song.
    </td>
  </tr>
  <tr>
    <td>
      <code>/np</code>
    </td>
    <td>
      Show the currently playing song.
    </td>
  </tr>
  <tr>
    <td>
      <code>/queue</code>
    </td>
    <td>
      Show the current queue.
    </td>
  </tr>
  <tr>
    <td>
      <code>/clear</code>
    </td>
    <td>
      Remove all songs from the queue and stop playback.
    </td>
  </tr>
  <tr>
    <td>
      <code>/remove</code>
      <code>number</code>
    </td>
    <td>
      Remove the specified song number from the queue.
    </td>
  </tr>
  <tr>
    <td>
      <code>/shuffle</code>
    </td>
    <td>
      Randomize the order of the songs in the current queue. This is not an on/off
      toggle. The shuffling happens once when the command is invoked.
    </td>
  </tr>
  <tr>
    <td>
      <code>/skip</code>
      <code>[number]</code>
    </td>
    <td>
      Skip the currently playing song and play the next song. If <code>number</code>
      is supplied, will skip that many songs. If <code>number</code> is negative, will
      skip backwards.
    </td>
  </tr>
  <tr>
    <td>
      <code>/loop</code>
      <code>mode</code>
    </td>
    <td>
      Enable/disable looping of the current song or the whole queue.
    </td>
  </tr>
</table>
