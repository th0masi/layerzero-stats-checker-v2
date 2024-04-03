from datetime import datetime, timedelta
import json

import aiofiles
import aiosqlite
import ijson

from aiofiles import open as aio_open
from aiohttp import ClientSession, ClientTimeout
from core.database import DBManager
from core.utils import load_json
from loguru import logger
from pathlib import Path
from fake_useragent import UserAgent


class Dune:
    def __init__(self):
        current_file_path = Path(__file__).parent.absolute()
        root_path = current_file_path.parent.parent
        self.db_path = root_path / "data" / "database_dune.db"

        self.dune_url = 'https://core-hsr.dune.com/v1/graphql'
        self.api_dune_url = 'https://app-api.dune.com/v1/graphql'
        self.save_path_1500000 = Path('core/dune/1500000.json')
        self.save_path_3000000 = Path('core/dune/3000000.json')
        self.query1_path = Path('core/dune/query1.json')
        self.query1_id = 2464151
        self.query2_path = Path('core/dune/query2.json')
        self.query2_id = 2729909
        self.query3_path = Path('core/dune/query3.json')
        self.session = None

    async def create_db(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
            CREATE TABLE IF NOT EXISTS wallets (
            id INTEGER PRIMARY KEY,
            ua TEXT NOT NULL UNIQUE,
            rk INTEGER,
            rs INTEGER,
            tc INTEGER,
            amt REAL,
            cc TEXT,
            dwm TEXT,
            lzd INTEGER,
            ibt TEXT)
            ''')
            await db.commit()

    async def save_to_db(self, file_path: Path):
        async with aiosqlite.connect(self.db_path) as db:
            async with aiofiles.open(file_path, mode='r') as file:
                data = json.loads(await file.read())
                wallets = data['data']['get_execution']['execution_succeeded'][
                    'data']

                for wallet in wallets:
                    await db.execute('''
                    INSERT INTO wallets (ua, rk, rs, tc, amt, cc, dwm, lzd, ibt)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(ua) DO UPDATE SET
                    rk=excluded.rk,
                    rs=excluded.rs,
                    tc=excluded.tc,
                    amt=excluded.amt,
                    cc=excluded.cc,
                    dwm=excluded.dwm,
                    lzd=excluded.lzd,
                    ibt=excluded.ibt
                    ''',
                                     (wallet['ua'], wallet['rk'], wallet['rs'],
                                      wallet['tc'],
                                      wallet['amt'], wallet['cc'],
                                      wallet['dwm'], wallet['lzd'],
                                      wallet['ibt']))
                await db.commit()

    async def is_db_empty(self):
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('SELECT COUNT(*) FROM wallets')
            count = await cursor.fetchone()
            await cursor.close()
            return count[0] == 0

    async def init_session(self):
        if self.session is None or self.session.closed:
            self.session = ClientSession()

    async def close_session(self):
        if self.session:
            await self.session.close()

    @staticmethod
    async def get_headers():
        ua = UserAgent()
        return {
            "Content-Type": 'application/json',
            "origin":       'https://dune.com',
            "referer":      'https://dune.com/',
            "User-Agent":   ua.safari,
    }

    async def get_execution_id(
            self,
            query_id: int
    ) -> int:
        await self.init_session()
        payload = await load_json(self.query1_path)
        payload['variables']['query_id'] = query_id

        while True:
            try:
                async with self.session.post(
                        self.dune_url,
                        headers=await self.get_headers(),
                        json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        execution_id = data['data']['get_result_v4'][
                            'result_id']
                        return execution_id
                    else:
                        logger.error(f'Ошибка обновления базы '
                                     f'данных: {await response.text()} | '
                                     f'Cтатус запроса: {response.status}')
                        break
            except Exception as error:
                logger.error(f'Ошибка обновления базы данных: {error}')
                break

    async def download_database(
            self,
            query_path: Path,
            query_id: int,
            save_path: Path
    ) -> None:
        payload = await load_json(query_path)

        execution_id = await self.get_execution_id(query_id)
        logger.info(f'ID базы данных №{query_id}: {execution_id}')
        payload['variables']['execution_id'] = execution_id
        timeout = ClientTimeout(total=1000)

        while True:
            try:
                async with self.session.post(
                    self.api_dune_url,
                    headers=await self.get_headers(),
                    json=payload,
                    timeout=timeout,
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.success(f'База данных №{query_id} '
                                       f'успешно скачана!')
                        async with aio_open(save_path, 'w') as file:
                            await file.write(json.dumps(data))
                        break
                    else:
                        logger.error(f'Ошибка обновления базы данных: '
                                     f'{await response.text()} | '
                                     f'Cтатус запроса: {response.status}')
            except Exception as error:
                logger.error(f'Ошибка обновления базы данных: {error}')

    async def update_databases(self):
        logger.info('Обновляем данные с dune...')

        await self.create_db()

        db_is_empty = await self.is_db_empty()
        is_file_older = await self.is_file_older_than_12_hours(self.db_path)

        if db_is_empty or is_file_older:
            await self.download_database(
                query_path=self.query2_path,
                query_id=self.query1_id,
                save_path=self.save_path_1500000,
            )
            await self.save_to_db(self.save_path_1500000)
            self.save_path_1500000.unlink()

            await self.download_database(
                query_path=self.query3_path,
                query_id=self.query2_id,
                save_path=self.save_path_3000000,
            )
            await self.save_to_db(self.save_path_3000000)
            self.save_path_3000000.unlink()

        else:
            logger.info(
                f'Данные с DUNE были обновлены '
                f'менее 12 часов назад, пропускаем.')

        await self.close_session()
        logger.success('Данные с dune успешно загружены!')

    @staticmethod
    async def is_file_older_than_12_hours(
            file_path: Path
    ) -> bool:
        if not file_path.exists():
            return True

        file_mod_time = datetime.fromtimestamp(file_path.stat().st_mtime)
        now = datetime.now()
        if (now - file_mod_time) > timedelta(hours=12):
            return True

        return False

    async def check_all_wallets(
            self,
            wallet_list
    ):
        logger.info(f'Сначала проверяю данные по DUNE...')
        for wallet in wallet_list:
            await self.run(wallet)

        logger.info(f'Получил все данные по DUNE')

    async def run(
            self,
            wallet: str
    ) -> None:
        address = wallet.lower()
        wallet_data = await self.search_in_db(
            wallet_address=address
        )

        if wallet_data:
            await self.update_database(wallet, wallet_data)
        else:
            logger.error(f'{wallet} | Не нашли информацию о кошельке на DUNE')

    @staticmethod
    async def update_database(
            wallet: str,
            wallet_data: dict
    ) -> None:
        amt = wallet_data.get('amt', 0)
        rk = wallet_data.get('rk', 0)
        dwm = wallet_data.get('dwm', '')
        months = 0

        if dwm:
            try:
                months = int(dwm.split(' / ')[-1])
            except (IndexError, ValueError):
                months = 0

        now = datetime.now()
        last_update_str = now.strftime('%Y-%m-%d %H:%M:%S')

        db_manager = DBManager()
        await db_manager.update_copilot(
            address=wallet,
            rank=int(rk),
            volume=float(amt),
            months=int(months),
            last_update=last_update_str,
        )

    async def search_in_db(
            self,
            wallet_address: str
    ) -> dict:
        async with aiosqlite.connect(
                self.db_path) as db:
            async with db.execute(
                    'SELECT * FROM wallets WHERE LOWER(ua) = LOWER(?)',
                    (wallet_address,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    wallet_data = {
                        'ua': row[1],
                        'rk': row[2],
                        'rs': row[3],
                        'tc': row[4],
                        'amt': row[5],
                        'cc': row[6],
                        'dwm': row[7],
                        'lzd': row[8],
                        'ibt': row[9],
                    }
                    return wallet_data
        return {}
