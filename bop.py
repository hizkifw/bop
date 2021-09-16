import os
import discord
from music import Song, Playlist, PlayerInstance
from discord_slash import SlashCommand, SlashContext

client = discord.Client(intents=discord.Intents.default())
slash = SlashCommand(client, sync_commands=True)
guild_ids = [730136766748819609]
players: dict[int, PlayerInstance] = {}

ERR_NOT_IN_VC = 'You must be in a voice channel to use this command.'

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

    player = get_player(ctx)
    if player is None:
        if not await connect_vc(ctx):
            return await ctx.send(content=ERR_NOT_IN_VC)
        player = get_player(ctx)

    if player is None:
        return await ctx.send(content='Error')

    n_queued = await player.queue_url(url)
    await player.play()
    return await ctx.send(content='{} songs queued'.format(n_queued))

print('Starting bot')
client.run(os.environ.get('BOT_TOKEN'))

print('Quit')
