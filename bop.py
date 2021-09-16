import os
import discord
from music import Song, Playlist, PlayerInstance
from discord_slash import SlashCommand, SlashContext

client = discord.Client(intents=discord.Intents.default())
slash = SlashCommand(client, sync_commands=True)
guild_ids = [730136766748819609]
players: dict[int, PlayerInstance] = {}

ERR_NOT_IN_VC = 'You must be in a voice channel to use this command.'
ERR_UNKNOWN = 'An unknown error has occurred.'

@client.event
async def on_ready():
    print('Ready!')

async def connect_vc(ctx: SlashContext):
    voice_channel = ctx.author.voice.channel if ctx.author.voice is not None else None
    if voice_channel is None:
        return False

    voice_client = await voice_channel.connect()
    players[voice_channel.id] = PlayerInstance(voice_client)
    return True

def get_player(ctx: SlashContext):
    if ctx.voice_client is None:
        return None

    vc_id = ctx.voice_client.channel.id
    if vc_id in players:
        return players[vc_id]
    return None

async def get_player_or_connect(ctx: SlashContext, *, reply=False):
    player = get_player(ctx)
    if player is None:
        if not await connect_vc(ctx):
            if reply:
                await ctx.send(content=ERR_NOT_IN_VC)
            return None
        player = get_player(ctx)

    if player is None and reply:
        await ctx.send(content=ERR_UNKNOWN)

    return player

@slash.slash(
    name='join',
    description='Join the VC',
    guild_ids=guild_ids
)
async def join(ctx: SlashContext):
    if not await connect_vc(ctx):
        return await ctx.send(content=ERR_NOT_IN_VC)

    await ctx.send(content='Hi!')

@slash.slash(
    name='leave',
    description='Leave the VC',
    guild_ids=guild_ids
)
async def leave(ctx: SlashContext):
    voice_channel = ctx.author.voice.channel if ctx.author.voice is not None else None
    if voice_channel is None:
        await ctx.send(content=ERR_NOT_IN_VC)
        return

    await ctx.voice_client.disconnect()
    players[voice_channel.id] = None

    await ctx.send(content='Bye!')

@slash.slash(
    name='play',
    description='Add a song to the queue',
    options=[
        {
            'name': 'url',
            'description': 'YouTube video or playlist URL. Search coming soon.',
            'type': 3, # string
            'required': True
        }
    ],
    guild_ids=guild_ids
)
async def play(ctx: SlashContext, *, url):
    await ctx.defer()
    player = await get_player_or_connect(ctx, reply=True)
    if player is None:
        return

    n_queued = await player.queue_url(url)

    if not player.is_playing():
        await player.play()

    return await ctx.send(content='{} songs queued'.format(n_queued))

@slash.slash(
    name='queue',
    description='Song queue',
    options=[

    ],
    guild_ids=guild_ids
)
async def queue(ctx: SlashContext):
    player = get_player(ctx)
    if player is None:
        return ctx.send(content='Nothing is playing')

    await ctx.defer()
    current_index = player.playlist.get_index()
    slice_start = max(0, current_index - 1)
    slice_end = current_index + 5
    partial_list = player.playlist.get_list()[slice_start:slice_end]
    partial_index = current_index - slice_start

    message = ''
    for idx, song in enumerate(partial_list):
        display_idx = slice_start + idx + 1
        title = await song.get_title()
        url = song.url
        duration = await song.get_duration()

        if idx == partial_index:
            message += '__Now Playing:__\n'

        message += f'{display_idx}. [{title}]({url}) | {duration}\n'

    embed = discord.Embed(
        title='Queue',
        description=message,
    )
    await ctx.send(embed=embed)

@slash.slash(
    name='skip',
    description='Skip current song',
    guild_ids=guild_ids
)
async def skip(ctx: SlashContext):
    await ctx.defer()
    player = await get_player_or_connect(ctx, reply=True)
    if player is None:
        return

    if await player.play_next():
        await ctx.send(content='Skipped')
    else:
        await ctx.send(content='End of queue')

print('Starting bot')
client.run(os.environ.get('BOT_TOKEN'))

print('Quit')
