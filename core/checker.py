import asyncio
import sys
from typing import List

from core.database import DBManager
from core.modules.coreb import Core
from core.modules.dune import Dune
from core.modules.get_balances import AnkrBalance
from core.modules.layerzero import LayerZero
from core.modules.mainnet import Mainnet
from core.pproxy import ProxyManager
from core.utils import get_current_block_core, load_file
from loguru import logger


async def check_all_wallets():
    db = DBManager()
    proxy_list = await db.get_all_proxies()
    logger.info(f'Загружено {len(proxy_list)} прокси')

    db_manager = DBManager()
    dune = Dune()
    wallets = await db_manager.get_wallets()
    semaphore = asyncio.Semaphore(10)

    px_manager = ProxyManager(proxy_list)
    valid_proxies = await px_manager.run()

    if valid_proxies is None:
        logger.error(f'Нет валидных прокси, загрузите другие')
        sys.exit(1)

    logger.info(f'Отобрал {len(valid_proxies)} валидных прокси для работы')
    logger.info(f'Получаю данные для {len(wallets)} кошельков...')

    await dune.update_databases()
    await dune.check_all_wallets(wallets)

    for i in range(0, len(wallets), 10):
        wallet_group = wallets[i:i + 10]
        await process_wallets_group(wallet_group, valid_proxies, semaphore)
        if i + 10 < len(wallets):
            await asyncio.sleep(1)
        logger.info(f'Проверил 10 кошельков')

    logger.success(f'Получил данные для всех {len(wallets)} кошельков!')


async def process_wallets_group(
        wallet_addresses: List[str],
        valid_proxies: List[str],
        semaphore
):
    tasks = [check_wallet(address, valid_proxies) for address in
             wallet_addresses]
    await asyncio.gather(*tasks)


async def check_wallet(
        wallet_address: str,
        valid_proxies: List[str]
):
    service_names = ['BALANCE', 'LAYERZERO', 'MAINNET', 'CORE']

    balance = AnkrBalance(
        wallet=wallet_address,
    )

    layerzero = LayerZero(
        wallet=wallet_address,
        proxies=valid_proxies
    )

    mainnet = Mainnet(
        wallet=wallet_address,
    )

    current_block = get_current_block_core()

    core = Core(
        wallet=wallet_address,
        current_block=current_block,
    )

    tasks = [balance.run(), layerzero.run(),
             mainnet.run(), core.run()]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    failed_services = [name for result, name in zip(results, service_names) if
                       result is False]

    if failed_services:
        failed_services_str = ', '.join(failed_services)
        logger.error(f"{wallet_address} | Не удалось "
                     f"получить данные: {failed_services_str}")
