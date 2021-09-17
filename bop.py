import os
import discord
import datetime
import json
import discord_slash.utils.manage_components as mc
from music import Song, Playlist, PlayerInstance
from discord_slash import SlashCommand, SlashContext, ComponentContext
from discord_slash.model import ButtonStyle

client = discord.Client(intents=discord.Intents.default())
slash = SlashCommand(client, sync_commands=True)
guild_ids = json.loads(os.environ.get('GUILD_IDS'))
players: dict[int, PlayerInstance] = {}

ERR_NOT_IN_VC = 'You must be in a voice channel to use this command.'
ERR_NO_PLAYER = 'Nothing is playing.'
ERR_UNKNOWN = 'An unknown error has occurred.'

@client.event
async def on_ready():
    print(f'Logged in as {client.user.name}#{client.user.discriminator}')
    print('Ready!')

async def connect_vc(ctx: SlashContext):
    voice_channel = ctx.author.voice.channel if ctx.author.voice is not None else None
    if voice_channel is None:
        return False

    if ctx.voice_client is not None and ctx.voice_client.is_connected():
        await ctx.voice_client.move_to(voice_channel)
    else:
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

async def embed_now_playing(player):
    np = player.playlist.now_playing()
    if np is None:
        return discord.Embed(
            description=ERR_NO_PLAYER
        )

    embed = discord.Embed(
        title=await np.get_title(),
        url=np.url,
    )
    embed.set_author(name='Now playing')
    return embed

async def create_player_components():
    action_row = mc.create_actionrow(
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

@slash.component_callback()
async def handle_component(ctx: ComponentContext):
    pass

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
async def play(ctx: SlashContext, etc=None, *, url):
    await ctx.defer()
    player = await get_player_or_connect(ctx, reply=True)
    if player is None:
        return

    queue_ended = not player.playlist.has_next()

    n_queued = await player.queue_url(url)
    await ctx.send(
        content='{} songs queued'.format(n_queued)
    )

    # Don't disturb the player if it's already playing
    if player.is_playing():
        return

    # If it isn't playing because it reached the end of the queue,
    # play the song that was just added to the queue
    if queue_ended:
        return await player.play_next()

    # Otherwise resume playback
    await player.resume()

@slash.slash(
    name='queue',
    description='Show the current queue',
    guild_ids=guild_ids
)
async def queue_list(ctx: SlashContext):
    player = get_player(ctx)
    if player is None:
        return await ctx.send(content=ERR_NO_PLAYER)

    await ctx.defer()
    current_index = player.playlist.get_index()
    slice_start = max(0, current_index - 1)
    slice_end = current_index + 5
    full_list = player.playlist.get_list()
    partial_list = full_list[slice_start:slice_end]
    partial_index = current_index - slice_start

    message = ''
    for idx, song in enumerate(partial_list):
        display_idx = slice_start + idx + 1
        title = await song.get_title()
        url = song.url
        duration = str(datetime.timedelta(seconds=await song.get_duration()))

        # Trim hour if 0
        if duration.startswith('0:'):
            duration = duration[2:]

        if idx == partial_index:
            message += '__Now playing:__\n**'
        message += f'{display_idx}. [{title}]({url}) | {duration}'
        if idx == partial_index:
            message += '**'
        message += '\n'

    embed = discord.Embed(
        title='Queue',
        description=message,
    )
    embed.set_footer(text='{} songs in queue'.format(len(full_list)))
    await ctx.send(embed=embed)

@slash.slash(
    name='clear',
    description='Remove all songs from the current queue',
    guild_ids=guild_ids
)
async def queue_clear(ctx: SlashContext):
    player = get_player(ctx)
    if player is None:
        return await ctx.send(content=ERR_NO_PLAYER)

    await player.stop()
    player.playlist.clear()

    await ctx.send(content='Queue cleared!')

@slash.slash(
    name='shuffle',
    description='Shuffle the order of songs in the queue',
    guild_ids=guild_ids
)
async def queue_shuffle(ctx: SlashContext):
    player = get_player(ctx)
    if player is None:
        return await ctx.send(content=ERR_NO_PLAYER)

    player.playlist.shuffle()
    await ctx.send(content='Queue shuffled!')

@slash.slash(
    name='skip',
    description='Skip current song',
    options=[
#        {
#            'name': 'number',
#            'description': 'How many songs to skip',
#            'type': 4, # integer
#            'required': False
#        }
    ],
    guild_ids=guild_ids
)
async def skip(ctx: SlashContext, *, number=1):
    await ctx.defer()
    player = await get_player_or_connect(ctx, reply=True)
    if player is None:
        return

    if await player.play_next():
        await ctx.send(embed=await embed_now_playing(player))
    else:
        await ctx.send(content='End of queue')

@slash.slash(
    name='pause',
    description='Pause the current song',
    guild_ids=guild_ids
)
async def pause(ctx: SlashContext):
    player = get_player(ctx)
    if player is None:
        return await ctx.send(content=ERR_NO_PLAYER)

    if player.is_playing():
        await player.pause()

    await ctx.send(content='Paused')

@slash.slash(
    name='resume',
    description='Resume playback',
    guild_ids=guild_ids
)
async def resume(ctx: SlashContext):
    player = get_player(ctx)
    if player is None:
        return await ctx.send(content=ERR_NO_PLAYER)

    if not player.is_playing():
        await player.resume()

    await ctx.send(embed=await embed_now_playing(player))

print('Starting bot')
client.run(os.environ.get('BOT_TOKEN'))

print('Quit')
