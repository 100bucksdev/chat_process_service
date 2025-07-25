import asyncio
from typing import Literal
from httpx import AsyncClient

from config import CHATS_MANAGER_URL


async def make_request(
    url: str,
    method: Literal['GET', 'POST', 'PUT', 'DELETE'] = 'GET',
    data: dict = None,
    base_url: str = CHATS_MANAGER_URL,
) -> dict:
    attempts = 3
    attempt = 0

    url = f'{base_url}{url}'

    while True:
        try:
            async with AsyncClient(timeout=120) as session:
                response = await session.request(method, url, json=data)
                content = response.json()
                return {
                    'status': response.status_code,
                    'headers': dict(response.headers),
                    'body': content,
                }
        except Exception as e:
            print(e)
            attempt += 1
            await asyncio.sleep(1)
            if attempt == attempts:
                return {
                    'status': 500,
                    'headers': {},
                    'body': {},
                }