import aiofiles
import aiohttp
import asyncio
import os


async def read_file(file_path: str) -> str:
    async with aiofiles.open(file=file_path, mode="r") as f:
        async for line in f:
            yield line


async def get_url(url: str, session: aiohttp.ClientSession, q: asyncio.Queue) -> str:
    async with session.get(url=url) as response:
        html: str = await response.text()
        await q.put(html)


async def print_html(q: asyncio.Queue):
    while True:
        html: str = await q.get()
        q.task_done()
        print(html[:50])


async def main(file_path: str):
    q: asyncio.Queue = asyncio.Queue()
    async with aiohttp.ClientSession() as session:
        producers = [
            asyncio.create_task(get_url(url=url, session=session, q=q))
            async for url in read_file(file_path=file_path)
        ]
        consumer: asyncio.Task = asyncio.create_task(print_html(q=q))
        await asyncio.gather(*producers)
        await q.join()
        consumer.cancel()


if __name__ == "__main__":
    asyncio.run(main(file_path=os.getenv("FILE_PATH", "./urls.txt")))
