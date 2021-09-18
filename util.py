from urllib import request
from urllib.error import HTTPError
import asyncio

async def is_url_ok(url: str) -> int:
    def _request(_url: str):
        try:
            req = request.Request(_url, method='HEAD')
            res = request.urlopen(req)
            return True, res.code
        except HTTPError as err:
            return False, err.code

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _request, url)
