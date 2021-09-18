import asyncio
import discord
import random
import time
import util
from yt_dlp import YoutubeDL

async def extract_info(url):
    def _extract(_url):
        try:
            opts = {
                'extract_flat': True,
                'skip_download': True,
            }
            with YoutubeDL(opts) as ydl:
                return ydl.extract_info(_url, download=False, process=False)
        except:
            return None

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _extract, url)

class Song():
    def __init__(self, url, requester_id=None):
        self.url = url
        self.info = None
        self.info_expiry = 0
        self.is_valid = True
        self.requester_id = requester_id

    async def get_info(self):
        if self.info is None or time.time() > self.info_expiry:
            self.info = await extract_info(self.url)
            self.info_expiry = time.time() + (3 * 60 * 60)

            if self.info is None:
                self.is_valid = False
        return self.info

    async def get_title(self):
        if await self.get_info() is not None:
            return self.info['title']
        return '(error)'

    async def _get_audio_url(self):
        if await self.get_info() is not None:
            formats = self.info['formats']
            # Prefer opus
            for fmt in formats:
                if fmt['format_id'] == '251':
                    return fmt['url']
            # Fall back to any audio otherwise
            for fmt in formats:
                if 'audio' in fmt['format_note'] or 'acodec' != 'none':
                    return fmt['url']
        return None

    async def get_audio_url(self):
        for _ in range(3):
            url = await self._get_audio_url()

            # Check if URL is valid
            if await util.is_url_ok(url):
                return url
            else:
                # Force refetch info if URL isn't valid
                self.info_expiry = 0

        return None

    async def get_duration(self):
        if await self.get_info() is not None:
            return self.info['duration']
        return 0

class Playlist():
    def __init__(self):
        self.song_list = []
        self.current_index = 0

    def _remove_invalids(self):
        [self.song_list for x in self.song_list if x.is_valid == True]

    def insert(self, song):
        self.song_list.append(song)

    def clear(self):
        self.song_list.clear()
        self.current_index = 0

    def shuffle(self):
        current_song = self.song_list.pop(self.current_index)
        random.shuffle(self.song_list)
        self.song_list.insert(0, current_song)
        self.current_index = 0

    def now_playing(self):
        self._remove_invalids()
        if self.current_index >= len(self.song_list) or self.current_index < 0:
            return None
        return self.song_list[self.current_index]

    def get_list(self):
        self._remove_invalids()
        return self.song_list

    def get_index(self):
        return self.current_index

    def jump(self, number, *, relative=True):
        new_index = number if not relative else self.current_index + number
        new_index = min(new_index, len(self.song_list))
        new_index = max(new_index, 0)
        self.current_index = new_index
        return self.now_playing()

    def has_next(self):
        return self.current_index + 1 < len(self.song_list)

    def has_prev(self):
        return self.current_index - 1 > 0

    def go_next(self):
        return self.jump(1)

    def go_prev(self):
        return self.jump(-1)

class PlayerInstance():
    def __init__(self, voice_client: discord.VoiceClient):
        self.voice_client = voice_client
        self.playlist = Playlist()
        self.skip_next_callback = False

    async def queue_url(self, url, requester_id=None):
        queued_songs = []

        # Check type of URL
        if 'youtu.be' in url or '/watch?v=' in url:
            # Force youtube-dl to extract video instead of playlist
            url = url.replace('&list=', '&_list=')
            song = Song(url, requester_id)
            queued_songs.append(song)
        elif 'youtube.com/playlist' in url:
            # Fetch playlist
            info = await extract_info(url)
            for entry in info['entries']:
                song = Song('https://youtu.be/{}'.format(entry['id']), requester_id)
                queued_songs.append(song)

        for song in queued_songs:
            self.playlist.insert(song)

        return queued_songs

    def is_playing(self):
        return self.voice_client.is_playing()

    async def play_next(self):
        if not self.playlist.has_next():
            return False
        self.playlist.go_next()
        return await self.play()

    async def play(self):
        song = self.playlist.now_playing()
        if song is None:
            return False

        url = await song.get_audio_url()
        if url is None:
            return await self.play_next()

        source = await discord.FFmpegOpusAudio.from_probe(
            url,
            before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
        )

        self.skip_next_callback = True
        if self.voice_client.is_playing():
            self.voice_client.stop()

        loop = asyncio.get_running_loop()
        def handle_next(error):
            if self.skip_next_callback:
                self.skip_next_callback = False
                return
            asyncio.run_coroutine_threadsafe(self.play_next(), loop)
        self.voice_client.play(source, after=handle_next)
        await asyncio.sleep(1)
        self.skip_next_callback = False

        return True

    async def pause(self):
        self.voice_client.pause()

    async def resume(self):
        self.voice_client.resume()

    async def stop(self):
        if self.voice_client.is_playing():
            self.skip_next_callback = True
            self.voice_client.stop()
