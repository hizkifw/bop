import discord
import datetime
import discord_slash.utils.manage_components as mc
from discord_slash.model import ButtonStyle
from music import Song, Playlist, PlayerInstance

ERR_NOT_IN_VC = 'You must be in a voice channel to use this command.'
ERR_NO_PLAYER = 'Nothing is playing.'
ERR_UNKNOWN = 'An unknown error has occurred.'

def format_duration(seconds: int) -> str:
    duration = str(datetime.timedelta(seconds=seconds))

    # Trim hour if 0
    if duration.startswith('0:'):
        duration = duration[2:]

    return duration

async def now_playing(player: PlayerInstance) -> discord.Embed:
    idx = player.playlist.get_index()
    np = player.playlist.now_playing()
    if np is None:
        return discord.Embed(
            description=ERR_NO_PLAYER
        )

    embed = discord.Embed(
        title=await np.get_title(),
        url=np.url,
    )
    embed.set_author(
        name=f'Now playing #{idx+1}'
    )
    embed.add_field(
        name='Duration',
        value=format_duration(await np.get_duration())
    )
    embed.add_field(
        name='Requested by',
        value=f'<@{np.requester_id}>'
    )

    return embed

async def format_song(song: Song):
    title = await song.get_title()
    url = song.url
    requester = song.requester_id
    duration = format_duration(await song.get_duration())

    return f'[{title}]({url}) | {duration} | <@{requester}>'

async def queue(player: PlayerInstance) -> discord.Embed:
    current_index = player.playlist.get_index()
    slice_start = max(0, current_index - 5)
    slice_end = current_index + 5
    full_list = player.playlist.get_list()
    partial_list = full_list[slice_start:slice_end]
    partial_index = current_index - slice_start

    message = ''
    for idx, song in enumerate(partial_list):
        display_idx = slice_start + idx + 1
        song_str = await format_song(song)

        if idx == partial_index:
            message += '__Now playing:__\n**'
        message += f'{display_idx}. {song_str}'
        if idx == partial_index:
            message += '**'
        message += '\n'

    embed = discord.Embed(
        title='Queue',
        description=message,
    )
    embed.set_footer(text='{} songs in queue'.format(len(full_list)))
    return embed

def player_controls():
    return mc.create_actionrow(
        mc.create_button(
            style=ButtonStyle.gray,
            label="Prev",
            emoji="⏪️",
        ),
        mc.create_button(
            style=ButtonStyle.gray,
            label="Play/Pause",
            emoji="⏯️",
        ),
        mc.create_button(
            style=ButtonStyle.gray,
            label="Skip",
            emoji="⏩️",
        )
    )

