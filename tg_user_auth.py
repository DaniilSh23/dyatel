import asyncio
from pyrogram import Client

from collector.settings import TG_API_ID, TG_API_HASH


async def main():
    async with Client("media/session_files/my_session", TG_API_ID, TG_API_HASH) as app:
        # await app.send_message(f"+79869940327", "**Тестовое сообщение по номеру тлф**")
        await app.send_message("me", "**Тестовое сообщение. Синхронизация сервиса прошла успешно**")


asyncio.run(main())



