import aiofiles
import aiohttp
import asyncio
import os
import re


async def read_file(file_path: str) -> str:
    async with aiofiles.open(file=file_path, mode="r") as f:
        async for line in f:
            yield line


async def get_url(url: str, session: aiohttp.ClientSession, q: asyncio.Queue) -> str:
    async with session.get(url=url) as response:
        html: str = await response.text()
        await q.put(html)


def get_href_contents(html: str, pattern: re.Pattern):
    for group in re.findall(pattern=pattern, string=html):
        yield group


async def write_urls_to_file(file_path: str, q: asyncio.Queue) -> None:
    pattern: re.Pattern = re.compile(
        r"href=\"(?P<href_content>.*?)\"", re.IGNORECASE | re.MULTILINE
    )
    while True:
        html: str = await q.get()
        async with aiofiles.open(file=file_path, mode="a") as f:
            for url in get_href_contents(html=html, pattern=pattern):
                await f.write(f"{url}\n")
        q.task_done()


async def main(file_path: str, output_file_path: str):
    q: asyncio.Queue = asyncio.Queue()
    async with aiohttp.ClientSession() as session:
        producers = [
            asyncio.create_task(get_url(url=url, session=session, q=q))
            async for url in read_file(file_path=file_path)
        ]
        consumer: asyncio.Task = asyncio.create_task(
            write_urls_to_file(file_path=output_file_path, q=q)
        )
        await asyncio.gather(*producers)
        await q.join()
        consumer.cancel()


if __name__ == "__main__":
    asyncio.run(
        main(
            file_path=os.getenv("FILE_PATH", "./urls.txt"),
            output_file_path=os.getenv("OUTPUT_FILE_PATH", "./foundurls.txt"),
        )
    )
