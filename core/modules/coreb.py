import aiohttp
from core.database import DBManager
from data.CONFIG import CORE_API_KEYS


class Core:
    def __init__(
            self,
            wallet: str,
            current_block: int
    ):
        self.wallet = wallet
        self.current_block = current_block
        self.contracts = [
            '0xa4151b2b3e269645181dccf2d426ce75fcbdeca9',
            '0x900101d06a7426441ae63e9ab3b9b0f63be145f1'
        ]
        self.base_url = (f"https://openapi.coredao.org/api?"
                         f"module=account&"
                         f"&action=tokentx"
                         f"&address={self.wallet}"
                         f"&startblock=111111"
                         f"&endblock={self.current_block}"
                         f"&page=1"
                         f"&offset=100"
                         f"&sort=asc")
        self.base_address = '0x0000000000000000000000000000000000000000'

    async def run(self) -> bool:
        try:
            add_volume_wei = 0

            for contract in self.contracts:
                data = await self.get_data(contract_address=contract)
                if data:
                    volume_wei = self.calculate_data_value(data=data)
                    add_volume_wei += volume_wei

            db_manager = DBManager()
            await db_manager.update_core(
                address=self.wallet,
                volume=add_volume_wei / 10 ** 6,
            )

            return True

        except Exception:
            return False

    async def get_data(self, contract_address: str):
        async with aiohttp.ClientSession() as session:
            for api_key in CORE_API_KEYS:
                try:
                    url = (self.base_url +
                           f"&apiKey={api_key}" +
                           f"&contractaddress={contract_address}")

                    async with session.get(url) as response:
                        response.raise_for_status()
                        data = await response.json()

                        if 'status' in data and data['status'] == '0':
                            raise Exception(
                                f"API error: "
                                f"{data.get('message', 'Unknown error')}"
                            )

                        return data

                except Exception:
                    continue

        return None

    def calculate_data_value(self, data):
        total_value = 0

        if 'result' in data:
            if not data['result']:
                return total_value

            for transaction in data['result']:
                if transaction['from'] == self.base_address or \
                        transaction['to'] == self.base_address:
                    value = int(transaction['value'])
                    total_value += value

        return total_value
