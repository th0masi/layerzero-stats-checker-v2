import asyncio
from pathlib import Path

from core.checker import check_all_wallets
from multiprocessing import Process
import loguru


updater_process = None


def is_updater_started():
    global updater_process
    return updater_process is not None and updater_process.is_alive()


LOGFILE_PATH = "./logs/main.log"


async def _run_updater():
    logfile_path = Path(LOGFILE_PATH)

    if not logfile_path.parent.exists():
        logfile_path.parent.mkdir(parents=True, exist_ok=True)

    if logfile_path.exists():
        logfile_path.unlink()

    loguru.logger.add(logfile_path)
    await check_all_wallets()


def start_updater():
    asyncio.run(_run_updater())


def start_updater_process():
    global updater_process
    updater_process = Process(target=start_updater)
    updater_process.start()
