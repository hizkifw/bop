import asyncio
import discord
import random
import time
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
    def __init__(self, url):
        self.url = url
        self.info = None
        self.info_expiry = 0
        self.is_valid = True

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

    async def get_audio_url(self):
        if await self.get_info() is not None:
            for fmt in self.info['formats']:
                if fmt['format_id'] == '251':
                    return fmt['url']
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

    def has_next(self):
        return self.current_index + 1 < len(self.song_list)

    def has_prev(self):
        return self.current_index - 1 > 0

    def go_next(self):
        if self.has_next():
            self.current_index += 1
        return self.now_playing()

    def go_prev(self):
        if self.has_prev():
            self.current_index -= 1
        return self.now_playing()

class PlayerInstance():
    def __init__(self, voice_client: discord.VoiceClient):
        self.voice_client = voice_client
        self.playlist = Playlist()
        self.is_skipping = False

    async def queue_url(self, url):
        # Check type of URL
        if 'youtu.be' in url or '/watch?v=' in url:
            # Force youtube-dl to extract video instead of playlist
            url = url.replace('&list=', '&_list=')
            self.playlist.insert(Song(url))
            return 1
        elif 'youtube.com/playlist' in url:
            # Fetch playlist
            info = await extract_info(url)
            n = 0
            for entry in info['entries']:
                song = Song('https://youtu.be/{}'.format(entry['id']))
                self.playlist.insert(song)
                n += 1
            return n

        return 0

    def is_playing(self):
        return self.voice_client.is_playing()

    async def play_next(self):
        if not self.playlist.has_next():
            return False
        self.playlist.go_next()
        self.is_skipping = True
        await self.play()
        return True

    async def play(self):
        song = self.playlist.now_playing()
        if song is None:
            return False
        url = await song.get_audio_url()
        source = await discord.FFmpegOpusAudio.from_probe(
            url,
            before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
        )

        if self.voice_client.is_playing():
            self.voice_client.stop()

        loop = asyncio.get_running_loop()
        def handle_next(error):
            if self.is_skipping:
                self.is_skipping = False
                return
            asyncio.run_coroutine_threadsafe(self.play_next(), loop)
        self.voice_client.play(source, after=handle_next)
        await asyncio.sleep(1)
        self.is_skipping = False

    async def pause(self):
        self.voice_client.pause()

    async def resume(self):
        self.voice_client.resume()

    async def stop(self):
        if self.voice_client.is_playing():
            self.is_skipping = True
            self.voice_client.stop()
