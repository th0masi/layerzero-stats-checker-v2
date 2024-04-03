import json
import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional
import os

from core.database import DBManager
from data.CONFIG import CORE_RPCS
from web3 import Web3
from web3.middleware import geth_poa_middleware


async def load_file(path: str) -> Optional[List[str]]:
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return None

    with open(path, "r", encoding="utf-8") as file:
        lines = [line.strip() for line in file.readlines()]
        lines = [line for line in lines if line]

    return lines if lines else None


async def load_json(path: Path):
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return None

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def unix_timestamp_to_datetime(
    timestamp: int,
    del_: bool = True,
) -> str:
    if del_:
        timestamp = timestamp / 1000.0

    dt = datetime.utcfromtimestamp(timestamp)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def get_current_block_core():
    current_block = 1000000000
    for rpc in CORE_RPCS:
        try:
            w3 = Web3(Web3.HTTPProvider(rpc), middlewares=[])
            w3.middleware_onion.inject(geth_poa_middleware, layer=0)

            current_block = w3.eth.block_number

        except Exception:
            continue

    return current_block


def is_valid_wallet(wallet):
    return re.match(r"^0x[a-fA-F0-9]{40}$", wallet) is not None


async def check_wallets(
        is_reset_db: bool,
        wallets: List[str],
        names: List[str]
):
    if not names:
        wallets = [wallet for wallet in wallets if is_valid_wallet(wallet)]
        if not wallets:
            raise ValueError("Неверный формат кошельков")

    unique_wallets = []
    unique_names = []
    seen_wallets = set()

    if is_reset_db:
        db_manager = DBManager()
        existing_wallets = await db_manager.get_wallets()
        wallets = [wallet for wallet in wallets if wallet not in existing_wallets]

    for wallet, name in zip(wallets, names if names else [""] * len(wallets)):
        if wallet not in seen_wallets and is_valid_wallet(wallet):
            seen_wallets.add(wallet)
            unique_wallets.append(wallet)
            if names:
                unique_names.append(name)
        elif not is_valid_wallet(wallet):
            raise ValueError(f"Неверный формат кошелька: {wallet}")

    return unique_wallets, unique_names if names else []


def format_number(value):
    if not value:
        return value

    if isinstance(value, int):
        return "{:,}".format(value).replace(",", " ")
    else:
        return "{:,.2f}".format(value).replace(",", " ")


def regex_replace(s, find, replace):
    return re.sub(find, replace, s)
