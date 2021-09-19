from urllib import request
from urllib.error import HTTPError
from urllib.parse import urlparse
from yt_dlp import YoutubeDL
import concurrent.futures
import asyncio
import re

pattern_url = re.compile(r'^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$')
def is_url(url: str) -> bool:
    return pattern_url.match(url) is not None

async def is_url_ok(url: str) -> int:
    def _request(_url: str):
        try:
            req = request.Request(_url, method='HEAD')
            res = request.urlopen(req)
            return True, res.code
        except HTTPError as err:
            return False, err.code

    loop = asyncio.get_running_loop()
    with concurrent.futures.ThreadPoolExecutor() as pool:
        return await loop.run_in_executor(pool, _request, url)

async def youtube_extract_info(url: str):
    def _extract(_url: str):
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
    with concurrent.futures.ThreadPoolExecutor() as pool:
        return await loop.run_in_executor(pool, _extract, url)
