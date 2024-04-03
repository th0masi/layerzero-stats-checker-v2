import asyncio
from asyncio import Task, create_task

import aiohttp
from aiohttp import ClientTimeout
from better_proxy import Proxy
from aiohttp_socks import ProxyConnector
from typing import List

from loguru import logger


class ProxyManager:
    def __init__(self, proxy_list: List[str]):
        self.proxy_list = proxy_list
        self.valid_proxies = []

    @staticmethod
    async def check_proxy(
        proxy: str,
    ) -> bool:
        proxy = Proxy.from_str(proxy)
        connector = ProxyConnector.from_url(proxy.as_url)
        timeout = ClientTimeout(total=10)
        async with aiohttp.ClientSession(
            connector=connector, timeout=timeout
        ) as session:
            async with session.get("https://nftcopilot.com//") as response:
                if response.status == 200:
                    return True

    async def check_proxies(self) -> List[str]:
        tasks = [self.check_proxy(proxy) for proxy in self.proxy_list]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        self.valid_proxies = [
            proxy for proxy, valid in zip(self.proxy_list, results) if valid
        ]
        return self.valid_proxies

    async def is_any_proxy_valid(self):
        """
        Fast checks if at least one proxy from the proxy list is valid
        :return:
        """
        tasks = [create_task(self.check_proxy(proxy)) for proxy in self.proxy_list]
        try:
            for t in asyncio.as_completed(tasks):
                try:
                    r = await t
                    if r:
                        return True
                except Exception as e:
                    logger.warning(e)
        finally:
            for t in tasks:
                t.cancel()
        return False

    async def run(self):
        self.proxy_list = [
            (
                f"http://{proxy}"
                if not proxy.startswith(("http://", "https://"))
                else proxy
            )
            for proxy in self.proxy_list
        ]
        valid_proxies = await self.check_proxies()

        if not valid_proxies:
            logger.error(
                "Все прокси оказались невалидными, загрузите другие "
                "прокси в data/proxies.txt для продолжения работы"
            )
            return None

        return valid_proxies
