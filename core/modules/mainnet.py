import asyncio

from core.database import DBManager
from data.CONFIG import MAINNET_RPCS
from web3 import Web3


class Mainnet:
    def __init__(self, wallet: str):
        self.wallet = wallet
        self.rpcs = MAINNET_RPCS

    async def run(self) -> bool:
        is_mainnet = False

        try:
            for rpc in MAINNET_RPCS:
                nonce = await self.get_nonce(
                    rpc=rpc
                )

                if nonce > 0:
                    is_mainnet = True
                    break

            db_manager = DBManager()
            await db_manager.update_mainnet(
                address=self.wallet,
                is_mainnet=is_mainnet
            )

            return True

        except Exception:
            return False

    async def get_nonce(
            self,
            rpc,
    ):
        w3 = Web3(Web3.HTTPProvider(rpc))
        try:
            nonce = await asyncio.to_thread(
                w3.eth.get_transaction_count,
                w3.to_checksum_address(self.wallet),
                'latest'
            )
            return nonce

        except Exception:
            return 0
