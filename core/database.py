import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Tuple, Union
import aiosqlite
from core.enums import SortType


def format_date(date_str):
    if not date_str:
        return None

    date_obj = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    formatted_date = date_obj.strftime("%d.%m.%Y")
    return formatted_date


class DBManager:
    def __init__(self):
        current_file_path = Path(__file__).parent.absolute()
        root_path = current_file_path.parent
        self.db_path = root_path / "data" / "database.db"

    def exists(self) -> bool:
        return os.path.exists(self.db_path)

    async def create_database(
        self, address_list: List[str], name_list: Optional[List[str]] = None
    ):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """CREATE TABLE IF NOT EXISTS wallets (
                id INTEGER PRIMARY KEY,
                address TEXT NOT NULL UNIQUE,
                wname TEXT,
                current_rank INTEGER,
                balance_usd FLOAT,
                prev_rank INTEGER,
                count_txn INTEGER,
                stargate_volume FLOAT,
                core_volume FLOAT,
                months INTEGER,
                protocol_count INTEGER,
                protocol_list TEXT,
                is_mainnet BOOLEAN,
                src_chains_count INTEGER,
                src_chains_list TEXT,
                dst_chains_count INTEGER,
                dst_chains_list TEXT,
                last_activity DATETIME,
                last_update DATETIME
            )"""
            )

            await db.commit()

            for address in address_list:
                name = (
                    name_list[address_list.index(address)]
                    if name_list and len(name_list) > address_list.index(address)
                    else None
                )
                await db.execute(
                    """
                    INSERT INTO wallets (address, wname) VALUES (?, ?)
                    ON CONFLICT(address) DO NOTHING
                """,
                    (address, name),
                )

            await db.commit()

    async def create_proxy_table(self, proxy_list: List[str]):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """CREATE TABLE IF NOT EXISTS proxies (
                id INTEGER PRIMARY KEY,
                proxy TEXT NOT NULL UNIQUE
            )"""
            )
            await db.commit()

            for proxy in proxy_list:
                await db.execute(
                    """
                    INSERT INTO proxies (proxy) VALUES (?)
                    ON CONFLICT(proxy) DO NOTHING
                """,
                    (proxy,),
                )
            await db.commit()

    async def delete_database(self):
        if self.db_path.exists():
            os.remove(self.db_path)

    async def get_all_proxies(self) -> List[str]:
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("SELECT proxy FROM proxies")
                rows = await cursor.fetchall()
                return [row[0] for row in rows]
        except:
            return []

    async def update_mainnet(self, address: str, is_mainnet: bool):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """UPDATE wallets SET is_mainnet = ? WHERE address = ?""",
                (
                    is_mainnet,
                    address,
                ),
            )
            await db.commit()

    async def update_copilot(
        self, address: str, rank: int, volume: float, months: int, last_update: str
    ):
        async with aiosqlite.connect(self.db_path) as db:
            current_rank = await db.execute(
                """SELECT current_rank FROM wallets WHERE address = ?""", (address,)
            )
            current_rank_result = await current_rank.fetchone()

            if current_rank_result and (
                current_rank_result[0] is None or current_rank_result[0] == 0
            ):
                await db.execute(
                    """UPDATE wallets SET 
                    prev_rank = ?
                    WHERE address = ? AND (prev_rank IS NULL OR prev_rank = 0)
                    """,
                    (rank, address),
                )

            await db.execute(
                """UPDATE wallets SET 
                current_rank = ?,
                stargate_volume = ?,
                months = ?,
                last_update = ?
                WHERE address = ?""",
                (rank, volume, months, last_update, address),
            )

            await db.commit()

    async def update_layerzero(
        self,
        address: str,
        last_activity: str,
        src_chains_list: str,
        dst_chains_list: str,
        protocol_list: str,
        dst_chains_count: int,
        src_chains_count: int,
        protocol_count: int,
        count_txn: int,
    ):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """UPDATE wallets SET
                last_activity = ?,
                src_chains_list = ?,
                dst_chains_list = ?,
                protocol_list = ?,
                dst_chains_count = ?,
                src_chains_count = ?,
                protocol_count = ?,
                count_txn = ?
                WHERE address = ?""",
                (
                    last_activity,
                    json.dumps(src_chains_list),
                    json.dumps(dst_chains_list),
                    json.dumps(protocol_list),
                    dst_chains_count,
                    src_chains_count,
                    protocol_count,
                    count_txn,
                    address,
                ),
            )
            await db.commit()

    async def update_core(
        self,
        address: str,
        volume: float,
    ):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """UPDATE wallets SET
                core_volume = ?
                WHERE address = ?""",
                (
                    volume,
                    address,
                ),
            )
            await db.commit()

    async def update_balance(
        self,
        address: str,
        balance: float,
    ):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """UPDATE wallets SET
                balance_usd = ?
                WHERE address = ?""",
                (
                    balance,
                    address,
                ),
            )
            await db.commit()

    async def get_wallets(self):
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("SELECT address FROM wallets")
                rows = await cursor.fetchall()
                return [row[0] for row in rows]
        except:
            return []

    async def get_all_wallets_names(self):
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("SELECT wname FROM wallets")
                rows = await cursor.fetchall()
                return [row[0] for row in rows]
        except:
            return []

    async def get_wallets_count(self):
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT count(1) FROM wallets")
            rows = await cursor.fetchall()
            return rows[0][0]

    async def get_all_wallets(self) -> Dict[str, Dict]:
        wallets_dict = {}
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT * FROM wallets")
            wallets = await cursor.fetchall()

            if wallets:
                columns = [description[0] for description in cursor.description]
                for wallet in wallets:
                    wallet_data = dict(zip(columns, wallet))
                    wallet_address = wallet_data["address"]

                    core_volume = wallet_data.get("core_volume", 0) or 0
                    stargate_volume = wallet_data.get("stargate_volume", 0) or 0
                    volume = core_volume + stargate_volume

                    last_activity = wallet_data.get("last_activity", None)
                    last_update = wallet_data.get("last_update", None)

                    wallet_data["volume"] = round(volume, 2)
                    wallet_data["balance_usd"] = round(
                        wallet_data["balance_usd"] or 0, 2
                    )
                    wallet_data["last_activity"] = format_date(last_activity)
                    wallet_data["last_update"] = format_date(last_update)

                    wallets_dict[wallet_address] = wallet_data

        return wallets_dict

    async def find_wallet(self, address: str) -> Optional[Dict]:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT * FROM wallets WHERE address = ?", (address,)
            )

            wallet_row = await cursor.fetchone()
            if wallet_row:
                columns = [description[0] for description in cursor.description]
                wallet_data = dict(zip(columns, wallet_row))

                core_volume = wallet_data.get("core_volume", 0) or 0
                stargate_volume = wallet_data.get("stargate_volume", 0) or 0
                volume = core_volume + stargate_volume

                wallet_data["volume"] = round(volume, 2)

                if wallet_data.get("last_activity"):
                    wallet_data["last_activity"] = format_date(
                        wallet_data["last_activity"]
                    )
                if wallet_data.get("last_update"):
                    wallet_data["last_update"] = format_date(
                        wallet_data["last_update"]
                    )

                if wallet_data and "src_chains_list" in wallet_data:
                    _src_chains_list = (
                        wallet_data.get("src_chains_list", "") or ""
                    ).split(",")
                    wallet_data["src_chains_list"] = [
                        item.strip('"') for item in _src_chains_list
                    ]

                if wallet_data and "dst_chains_list" in wallet_data:
                    _dst_chains_list = (
                        wallet_data.get("dst_chains_list", "") or ""
                    ).split(",")
                    wallet_data["dst_chains_list"] = [
                        item.strip('"') for item in _dst_chains_list
                    ]

                if wallet_data and "protocol_list" in wallet_data:
                    _protocol_list = (
                            wallet_data.get("protocol_list", "") or ""
                    ).split(",")
                    wallet_data["protocol_list"] = [
                        item.strip('"') for item in _protocol_list
                    ]

                return wallet_data

        return None

    async def analyze_wallets_by_type(
        self, sort_type: SortType
    ) -> Dict[str, Tuple[int, int]]:
        results = {}
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT {} FROM wallets".format(sort_type.value))
            rows = await cursor.fetchall()
            all_wallets = len(rows)

            for row in rows:
                networks = row[0].strip('"').split(",") if row[0] else []
                for network in networks:
                    network = network.capitalize()
                    if network not in results:
                        results[network] = [1, all_wallets - 1]
                    else:
                        results[network][0] += 1
                        results[network][1] -= 1

            sorted_results = sorted(results.items(), key=lambda item: item[1][0])
            sorted_dict = {k.capitalize(): v for k, v in sorted_results}

            return sorted_dict

    async def filter_wallets_by_type(
        self, sort_type: SortType, name: str, exists: bool
    ) -> List[str]:
        filtered_wallets = []
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT address, {} FROM wallets".format(sort_type.value)
            )
            rows = await cursor.fetchall()

            for row in rows:
                networks = row[1].strip('"').split(",") if row[1] else []
                if (exists and name in networks) or (
                    not exists and name not in networks
                ):
                    filtered_wallets.append(row[0])

        return filtered_wallets

    async def exists_wallet_with_wname(self) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT 1 FROM wallets WHERE wname IS NOT NULL LIMIT 1"
            )
            wallet = await cursor.fetchone()

            return wallet is not None

    async def wallets_without_txn_this_month(
        self, only_count: bool = True
    ) -> Union[int, List[str]]:
        current_month = datetime.now().month
        current_year = datetime.now().year
        query_base = "SELECT address FROM wallets WHERE strftime('%m', last_activity) != '{:02d}' OR strftime('%Y', last_activity) != '{}'"
        query = query_base.format(current_month, current_year)

        if only_count:
            query = f"SELECT COUNT(address) FROM ({query})"

        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(query)
            if only_count:
                result = await cursor.fetchone()
                return result[0] if result else 0
            else:
                rows = await cursor.fetchall()
                return [row[0] for row in rows]

    async def wallets_without_txn_mainnet(
        self, only_count: bool = True
    ) -> Union[int, List[str]]:
        query = "SELECT address FROM wallets WHERE is_mainnet = False"

        if only_count:
            query = f"SELECT COUNT(address) FROM ({query})"

        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(query)
            if only_count:
                result = await cursor.fetchone()
                return result[0] if result else 0
            else:
                rows = await cursor.fetchall()
                return [row[0] for row in rows]

    async def get_date_last_update(self) -> Optional[str]:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        query = "SELECT MAX(last_update) FROM wallets WHERE last_update < ?"

        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(query, (now,))
            nearest_update = await cursor.fetchone()

            if nearest_update and nearest_update[0]:
                date_obj = datetime.strptime(nearest_update[0], "%Y-%m-%d %H:%M:%S")
                return date_obj.strftime("%d.%m.%Y")
            else:
                return None

    async def get_wallets_by_rank_range(
        self, min_rank: int, max_rank: int, only_count: bool = True
    ) -> Union[int, List[str]]:
        query = f"""
        SELECT address, current_rank 
        FROM wallets 
        WHERE current_rank IS NOT NULL 
        AND current_rank > {min_rank} 
        AND current_rank <= {max_rank}
        """

        if only_count:
            query = f"SELECT COUNT(address) FROM ({query})"

        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(query)
            if only_count:
                result = await cursor.fetchone()
                return result[0] if result else 0
            else:
                rows = await cursor.fetchall()
                return [row[0] for row in rows]

    async def get_wallets_with_extreme_ranks(self) -> Tuple[int, int]:
        query = """
            SELECT MIN(current_rank), MAX(current_rank) 
            FROM wallets 
            WHERE current_rank IS NOT NULL AND current_rank > 0
        """

        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(query)
            result = await cursor.fetchone()
            min_rank, max_rank = result if result else (None, None)
            return min_rank, max_rank

    async def get_total_volume(self, volume_type: str) -> float:
        query = f"""
            SELECT SUM({volume_type}) 
            FROM wallets 
            WHERE {volume_type} IS NOT NULL
        """

        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(query)
            result = await cursor.fetchone()
            total_volume = result[0] if result else 0

            return round(total_volume, 2) if total_volume else 0.0

    async def get_wallets_by_volume_range(
        self,
        volume_type: str,
        min_volume: float,
        max_volume: float,
        only_count: bool = True,
    ) -> Union[int, List[str]]:
        if only_count:
            query = f"""
            SELECT COUNT(address) 
            FROM wallets 
            WHERE {volume_type} IS NOT NULL 
            AND {volume_type} > {min_volume} 
            AND {volume_type} <= {max_volume}
            """
        else:
            query = f"""
            SELECT address 
            FROM wallets 
            WHERE {volume_type} IS NOT NULL 
            AND {volume_type} > {min_volume} 
            AND {volume_type} <= {max_volume}
            """

        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(query)
            if only_count:
                result = await cursor.fetchone()
                return result[0] if result else 0
            else:
                rows = await cursor.fetchall()
                return [row[0] for row in rows]

    async def get_total_txn_count(self) -> int:
        query = """
            SELECT SUM(count_txn)
            FROM wallets
            WHERE count_txn IS NOT NULL
        """

        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(query)
            result = await cursor.fetchone()
            total_txn_count = result[0] if result else 0

            return total_txn_count if total_txn_count else 0
