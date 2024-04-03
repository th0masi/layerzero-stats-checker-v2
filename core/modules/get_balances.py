import random

from ankr import AnkrWeb3
from ankr.types import GetAccountBalanceRequest
from core.database import DBManager


class AnkrBalance:
    def __init__(self, wallet: str):
        self.wallet = wallet
        self.api_keys = [
            'c32e5338e51b4f3e0499b4c343d6414a1c7bbe1c6b53cef6c0524a9a97e3900a',
            'a5d19a7c8044e8201a9760ad597d38d001c0ad34dabb0327a26696c01f7ca0d1',
            '469daf21be94ebfbbdfdb42df04d899a42a232e61d909084f994079e7c51eba4',
            '0080018436bd26a9e7657f6984ae544e57a888295a12b39e2569eb1fb525a15a',
            '51d933fe230e39f9b03704baec6d38faac91c2c3ccb09d4d7508882795d8d2a9',
            '7c0f852da6f6d3883214da97992d3b8a1c57200715360a0ed0c5132309229a90',
            '2f442545351937a6ad11c159cb85852c16586cb844e49eb4185c6a0a78a01609',
            '1449e6002bb99da784f012ebdcbf9e9f6c9b38600cf4dcf025c79c436ababc07',
            '9ac8a23d97e91a753322205247ecfae69e8d031787ac9bcb36322a98ecc4c0ac',
            'a134707f53adff2761dbff6d1403ec4091c7780b1b73aadd66c011d3e6f834ba',
            'edf5fb40bea2d5871621f236c80c188986ee99a88fb6ee928cf6454aa74cb918',
            'fe55f7f59e50a8bd2c1868706f01e56887ecacefef932dabeae3962e271e3f2c',
            '4fee3fe83fe0e278d547527343c99f62580baae5517d5670dc224516b51e3072',
            'b9b71cfb4277a649f710d27481c75971676e51eec38d974e919166d4a9868c66',
            'ad17b6a4bfc71b6a0310325ff140d164316c367031429100351db734da5f6412',
            'fb759011e7b1523b3b47bfefaac2c30281a61dbbc6a9671535e1f16ef1d043c4',
            'dd055a0930fd44a0b94e4f1faf5ec606d0e760e185da4a354e690b163965096d',
        ]

    async def get_balance(self):
        balance_usd = 0

        random.shuffle(self.api_keys)

        for key in self.api_keys:
            try:
                ankr_w3 = AnkrWeb3(key)

                assets = ankr_w3.token.get_account_balance(
                    request=GetAccountBalanceRequest(
                        walletAddress=self.wallet
                    )
                )

                for asset in assets:
                    if asset.tokenSymbol in ['USDC', 'USDT', 'DAI']:
                        balance = asset.balance
                    else:
                        balance = asset.balanceUsd

                        if float(balance) > 1000000:
                            balance = float(0)

                    balance_usd += float(balance)

                    return balance_usd

            except Exception:
                continue

        return balance_usd

    async def run(self):
        try:
            balance_usd = await self.get_balance()

            db_manager = DBManager()
            await db_manager.update_balance(
                address=self.wallet,
                balance=float(balance_usd),
            )

            return True

        except Exception:
            return False
