import asyncio

from aiohttp import ClientTimeout
from aiohttp_socks import ProxyConnector
from core.database import DBManager
from core.utils import unix_timestamp_to_datetime
from pyuseragents import random as random_useragent
import aiohttp
from better_proxy import Proxy
import random
from typing import List


class Copilot:
    def __init__(
            self,
            wallet: str,
            proxies: List[str]
    ):
        self.wallet = wallet
        self.proxies = proxies
        self.copilot_url = 'https://nftcopilot.com/p-api/layer-zero-rank/check'

    async def run(self) -> bool:
        try:
            query = {
                "address": self.wallet,
                "addresses": [self.wallet],
                "c": 'check'
            }

            response_data = await self.send_request(
                method='POST',
                url=self.copilot_url,
                data=query
            )

            if response_data and isinstance(response_data, list) and len(
                    response_data) > 0:
                copilot_data = response_data[0]
                last_update = int(copilot_data.get('rankUpdatedAt', 0))
                rank = int(copilot_data.get('rank', 0))
                volume = float(copilot_data.get('volume', 0.0))
                distinct_months = int(copilot_data.get('distinctMonths', 0))

                last_update_str = unix_timestamp_to_datetime(last_update)

                db_manager = DBManager()
                await db_manager.update_copilot(
                    address=self.wallet,
                    rank=rank,
                    volume=volume,
                    months=distinct_months,
                    last_update=last_update_str,
                )

                return True

        except Exception:
            return False

    async def get_headers(self):
        return {
            "Content-Type": 'application/json',
            "User-Agent":   random_useragent(),
            "origin":       'https://nftcopilot.com',
            "referer":      (f'https://nftcopilot.com/'
                             f'layer-zero-rank-check?'
                             f'address={self.wallet}'),
        }

    async def send_request(
            self,
            method: str,
            url: str,
            data: dict
    ):
        headers = await self.get_headers()
        proxy_str = random.choice(
            self.proxies
        )
        proxy = Proxy.from_str(proxy_str)
        connector = ProxyConnector.from_url(proxy.as_url)
        timeout = ClientTimeout(total=20)

        async with aiohttp.ClientSession(
                connector=connector,
                timeout=timeout
        ) as session:
            for attempt in range(10):  # Повторять запрос до 10 раз
                try:
                    async with session.request(
                            method,
                            url,
                            json=data,
                            headers=headers
                    ) as response:
                        return await response.json()
                except Exception as e:
                    if attempt < 9:
                        await asyncio.sleep(
                            random.uniform(0.5, 1.5))

            return None
