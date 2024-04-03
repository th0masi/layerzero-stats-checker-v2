import json
import uuid

from aiohttp import ClientTimeout
from aiohttp_socks import ProxyConnector
from core.database import DBManager
from core.utils import unix_timestamp_to_datetime
from fake_useragent import UserAgent
import aiohttp
from loguru import logger
from better_proxy import Proxy
import random
from typing import List


class LayerZero:
    def __init__(
            self,
            wallet: str,
            proxies: List[str]
    ):
        self.wallet = wallet
        self.proxies = proxies
        self.l0_url = 'https://layerzeroscan.com/api/trpc/messages.list'

    async def run(self) -> bool:
        query = {
            "filters": {
                "address": self.wallet,
                "stage": "mainnet",
                "created": {}
            }
        }
        url_with_params = f"{self.l0_url}?input={json.dumps(query)}"

        try:
            data = await self.send_request(method='GET', url=url_with_params)

            messages = data.get('result', {}).get('data', {}).get('messages',
                                                                  None)
            if not messages:
                return False

            dst_chain_list = set()
            src_chain_list = set()
            protocol_names = set()
            created_date = None

            for message in messages:
                try:
                    dst_chain_list.add(message.get('dstChainKey').lower())
                    src_chain_list.add(message.get('srcChainKey').lower())

                    src_protocol_ = message.get('srcUaProtocol', None)
                    if src_protocol_:
                        src_protocol_name = src_protocol_.get('name', None)

                    else:
                        dst_protocol_ = message.get('dstUaProtocol', None)
                        src_protocol_name = dst_protocol_.get('name', None)

                    if src_protocol_name:
                        protocol_names.add(src_protocol_name.lower())

                except Exception as e:
                    logger.error(e)
                    pass

                if not created_date and message.get(
                        'mainStatus') == 'DELIVERED':
                    created_timestamp = int(message.get('created'))
                    created_date = unix_timestamp_to_datetime(
                        timestamp=created_timestamp,
                        del_=False,
                    )

            db_manager = DBManager()
            await db_manager.update_layerzero(
                address=self.wallet,
                last_activity=created_date,
                dst_chains_list=','.join(dst_chain_list),
                src_chains_list=','.join(src_chain_list),
                dst_chains_count=len(dst_chain_list),
                src_chains_count=len(src_chain_list),
                count_txn=len(messages),
                protocol_count=len(protocol_names),
                protocol_list=','.join(protocol_names),
            )

            return True
        except Exception as e:
            logger.error(f'LAYERZERO | Возникла ошибка: {e}')
            return False

    async def get_headers(self):
        ua = UserAgent()
        return {
            "Content-Type": 'application/json',
            "User-Agent":   ua.random,
            "referer": f'https://layerzeroscan.com/address/{self.wallet}',
            "baggage": (
                f"sentry-environment=vercel-production,"
                f"sentry-release=8db980a63760b2e079aa1e8cc36420b60474005a,"
                f"sentry-public_key=7ea9fec73d6d676df2ec73f61f6d88f0,"
                f"sentry-trace_id={uuid.uuid4()}"
            )
        }

    async def send_request(
            self,
            method: str,
            url: str,
    ):
        headers = await self.get_headers()
        timeout = ClientTimeout(total=10)

        random.shuffle(self.proxies)

        for proxy in self.proxies:
            proxy = Proxy.from_str(proxy)
            connector = ProxyConnector.from_url(proxy.as_url)

            async with aiohttp.ClientSession(
                    connector=connector,
                    timeout=timeout
            ) as session:
                try:
                    async with session.request(
                            method,
                            url,
                            headers=headers
                    ) as response:
                        return await response.json()

                except Exception:
                    continue
