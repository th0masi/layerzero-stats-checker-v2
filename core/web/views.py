import csv
import datetime
import tempfile

from core.enums import SortType
from flask import render_template, request, send_file, redirect

from core.database import DBManager
from flask import Blueprint

from core.pproxy import ProxyManager
from core.web.subprocess import (
    is_updater_started,
    start_updater_process,
    LOGFILE_PATH,
)


async def index():
    db = DBManager()
    is_checking = is_updater_started()
    db_exists = db.exists()
    if not is_checking and (not db_exists or (await db.get_wallets_count()) == 0):
        return render_template(
            "main.html",
            empty=True,
            refresh_disabled=True,
            eye_disabled=True,
            stats_disabled=True,
            download_disabled=True,
        )

    is_names = db_exists and await db.exists_wallet_with_wname()
    logs = []

    return render_template(
        "wallet.html",
        is_names=is_names,
        logs=logs,
        is_checking=is_checking,
        form_disabled=is_checking,
        refresh_disabled=is_checking,
        download_disabled=is_checking,
    )


async def get_wallet_list():
    db = DBManager()
    if not db.exists() or (await db.get_wallets_count()) == 0:
        return []

    data_wallets = await db.get_all_wallets()
    wallets_list = list(data_wallets.values())
    return {"results": wallets_list, "isUpdaterStarted": is_updater_started()}


def _render_form(
    proxy_error=False,
    **kwargs,
):
    db = DBManager()
    db_exists = db.exists()
    return render_template(
        "form.html",
        download_disabled=True,
        eye_disabled=True,
        refresh_disabled=True,
        stats_disabled=not db_exists,
        db_exists=db_exists,
        proxy_error=proxy_error,
        **kwargs,
    )


async def form():
    db = DBManager()
    if request.method != "POST":
        if db.exists():
            wallets = await db.get_wallets()
            proxies = await db.get_all_proxies()
            wallets_names = await db.get_all_wallets_names()

            wallets_value = "\n".join(wallets)
            id_value = "\n".join(
                map(lambda s: str(s) if s else "", wallets_names)
            ).rstrip()
            proxy_value = "\n".join(proxies)
        else:
            wallets_value = ""
            id_value = ""
            proxy_value = ""
        return _render_form(
            wallets_value=wallets_value,
            proxy_value=proxy_value,
            id_value=id_value
        )

    address_list = list(
        map(
            lambda s: s.strip(),
            filter(bool, request.form.get("addressList", "").strip().split("\n")),
        )
    )
    # delete
    id_list = list(
        map(
            lambda s: s.strip(),
            filter(bool, request.form.get("idList", "").strip().split("\n")),
        )
    )
    proxy_list = list(
        map(
            lambda s: s.strip(),
            filter(bool, request.form.get("proxyList", "").strip().split("\n")),
        )
    )

    # Validate form
    is_any_proxy_valid = await ProxyManager(proxy_list).is_any_proxy_valid()
    if not is_any_proxy_valid or not any(address_list):
        return _render_form(
            proxy_error=not is_any_proxy_valid,
        )

    #  Start updater
    db_manager = DBManager()
    await db_manager.delete_database()
    await db_manager.create_proxy_table(proxy_list)
    await db_manager.create_database(
        address_list=address_list,
        name_list=id_list,
    )
    start_updater_process()
    return redirect("/")


async def update_data():
    start_updater_process()
    return redirect("/")


async def stats():
    db = DBManager()
    num_wallets = await db.get_wallets_count()
    num_txn = await db.get_total_txn_count()
    without_txn_this_month = await db.wallets_without_txn_this_month()
    without_txn_mainnet = await db.wallets_without_txn_mainnet()
    last_update_date = await db.get_date_last_update()
    min_rank, max_rank = await db.get_wallets_with_extreme_ranks()
    less_100k_rank = await db.get_wallets_by_rank_range(
        min_rank=0,
        max_rank=100000,
    )
    less_500k_rank = await db.get_wallets_by_rank_range(
        min_rank=100000,
        max_rank=500000,
    )
    less_1kk_rank = await db.get_wallets_by_rank_range(
        min_rank=500000,
        max_rank=1000000,
    )
    more_1kk_rank = await db.get_wallets_by_rank_range(
        min_rank=1000000,
        max_rank=5000000,
    )

    total_stargate_volume = await db.get_total_volume(volume_type="stargate_volume")

    total_core_volume = await db.get_total_volume(volume_type="core_volume")

    total_volume = round(total_stargate_volume + total_core_volume, 2)

    less_1k_volume_stargate = await db.get_wallets_by_volume_range(
        volume_type="stargate_volume",
        min_volume=0,
        max_volume=1000,
    )

    less_5k_volume_stargate = await db.get_wallets_by_volume_range(
        volume_type="stargate_volume",
        min_volume=0,
        max_volume=5000,
    )

    less_5k_volume_core = await db.get_wallets_by_volume_range(
        volume_type="core_volume",
        min_volume=0,
        max_volume=5000,
    )
    dst_chain_list = await db.analyze_wallets_by_type(sort_type=SortType.DSTCHAIN)

    src_chain_list = await db.analyze_wallets_by_type(sort_type=SortType.SRCHAIN)

    protocol_list = await db.analyze_wallets_by_type(sort_type=SortType.PROTOCOL)

    return render_template(
        "stats.html",
        num_wallets=num_wallets,
        num_txn=num_txn,
        without_txn_this_month=without_txn_this_month,
        without_txn_mainnet=without_txn_mainnet,
        last_update_date=last_update_date,
        min_rank=min_rank,
        max_rank=max_rank,
        less_100k=less_100k_rank,
        less_500k=less_500k_rank,
        less_1kk=less_1kk_rank,
        more_1kk=more_1kk_rank,
        total_stargate_volume=total_stargate_volume,
        total_core_volume=total_core_volume,
        total_volume=total_volume,
        less_1k_volume_stargate=less_1k_volume_stargate,
        less_5k_volume_stargate=less_5k_volume_stargate,
        less_5k_volume_core=less_5k_volume_core,
        dst_chain_list=dst_chain_list,
        src_chain_list=src_chain_list,
        protocol_list=protocol_list,
        download_disabled=True,
        refresh_disabled=True,
        eye_disabled=True,
    )


async def walletItem(address):
    db_manager = DBManager()
    wallet_data = await db_manager.find_wallet(address=address)
    last_activity = wallet_data["last_activity"]

    last_activity_date = datetime.datetime.strptime(last_activity, "%d.%m.%Y")

    current_date = datetime.datetime.now()

    is_tx_in_current_month = (
        last_activity_date.month == current_date.month
        and last_activity_date.year == current_date.year
    )

    return render_template(
        "wallet-item.html",
        wallet=wallet_data,
        is_tx_in_current_month=is_tx_in_current_month,
        download_disabled=True,
    )


async def logs_page():
    return render_template(
        "logs.html",
    )


def get_logs_view():
    with open(LOGFILE_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()
    return lines


async def download():
    tmp_file = tempfile.NamedTemporaryFile(delete=False)
    db_manager = DBManager()

    filter_wallets_type = request.args.get("type")
    filter_enabled = request.args.get("enabled", "1") == "1"
    filter_source = request.args.get("source")
    filter_destination = request.args.get("destination")
    filter_protocol = request.args.get("protocol")

    if filter_wallets_type == "all":
        name = "all-wallets"
        wallets = await db_manager.get_wallets()
    elif filter_protocol is not None:
        name = filter_protocol.lower()
        wallets = await db_manager.filter_wallets_by_type(
            sort_type=SortType.PROTOCOL,
            name=name,
            exists=filter_enabled,
        )
    elif filter_destination is not None:
        name = filter_destination.lower()
        wallets = await db_manager.filter_wallets_by_type(
            sort_type=SortType.DSTCHAIN, name=name, exists=filter_enabled
        )
    elif filter_source is not None:
        name = filter_source.lower()
        wallets = await db_manager.filter_wallets_by_type(
            sort_type=SortType.SRCHAIN, name=name, exists=filter_enabled
        )
    else:
        name = filter_wallets_type
        wallets = await download_uniq(filter_wallets_type)

    tmp_file.writelines([f"{w}\n".encode() for w in wallets])
    tmp_file.close()

    return send_file(
        tmp_file.name,
        download_name=(
            f"{len(wallets)}-wallets-"
            f"{'include' if filter_enabled else  'without'}-"
            f"{name if name else filter_wallets_type}.txt"
        ),
        mimetype="text/plain",
        as_attachment=True,
    )


async def download_uniq(filter_wallets_type):
    db = DBManager()
    wallets = []
    if filter_wallets_type == "without_txn_this_month":
        wallets = await db.wallets_without_txn_this_month(only_count=False)
    elif filter_wallets_type == "without_txn_mainnet":
        wallets = await db.wallets_without_txn_mainnet(only_count=False)
    elif filter_wallets_type == "less_100k":
        wallets = await db.get_wallets_by_rank_range(
            min_rank=0, max_rank=100000, only_count=False
        )
    elif filter_wallets_type == "less_500k":
        wallets = await db.get_wallets_by_rank_range(
            min_rank=100000, max_rank=500000, only_count=False
        )
    elif filter_wallets_type == "less_1kk":
        wallets = await db.get_wallets_by_rank_range(
            min_rank=500000, max_rank=1000000, only_count=False
        )
    elif filter_wallets_type == "more_1kk":
        wallets = await db.get_wallets_by_rank_range(
            min_rank=1000000, max_rank=5000000, only_count=False
        )
    elif filter_wallets_type == "less_1k_volume_stargate":
        wallets = await db.get_wallets_by_volume_range(
            volume_type="stargate_volume",
            min_volume=0,
            max_volume=1000,
            only_count=False,
        )
    elif filter_wallets_type == "less_5k_volume_stargate":
        wallets = await db.get_wallets_by_volume_range(
            volume_type="stargate_volume",
            min_volume=0,
            max_volume=5000,
            only_count=False,
        )
    elif filter_wallets_type == "less_5k_volume_core":
        wallets = await db.get_wallets_by_volume_range(
            volume_type="core_volume", min_volume=0, max_volume=5000, only_count=False
        )

    return wallets


async def export_csv():
    db = DBManager()
    wallets = await db.get_all_wallets()
    wallets_list = list(wallets.values())

    tmp_file = tempfile.NamedTemporaryFile(
        mode="w+", delete=False, suffix=".csv", encoding="utf-8-sig"
    )

    fieldnames = [
        "Кошелёк",
        "Ранг",
        "Объём STG",
        "Объём CORE",
        "Транз.",
        "Протоколы",
        "Период",
        "Баланс",
        "Активность",
        "Обновлено",
    ]

    writer = csv.DictWriter(
        tmp_file,
        fieldnames=fieldnames,
        delimiter=";",
        quotechar='"',
        quoting=csv.QUOTE_MINIMAL,
        lineterminator="\n",
    )

    writer.writeheader()

    for wallet in wallets_list:
        writer.writerow(
            {
                "Кошелёк": wallet["address"],
                "Ранг": wallet["current_rank"],
                "Объём STG": wallet["stargate_volume"],
                "Объём CORE": wallet["core_volume"],
                "Транз.": wallet["count_txn"],
                "Протоколы": wallet["protocol_count"],
                "Период": wallet["months"],
                "Баланс": f"{wallet['balance_usd']}",
                "Активность": wallet["last_activity"],
                "Обновлено": wallet["last_update"],
            }
        )

    tmp_file.seek(0)
    tmp_file_name = tmp_file.name
    tmp_file.close()

    return send_file(
        tmp_file_name,
        as_attachment=True,
        download_name=f"{len(wallets_list)}-wallets.csv",
        mimetype="text/csv",
    )


blueprint = Blueprint("blueprint", __name__)

blueprint.route("/")(index)
blueprint.route("/getWalletList")(get_wallet_list)
blueprint.route("/form", methods=["GET", "POST"])(form)
blueprint.route("/stats")(stats)
blueprint.route("/wallet/<string:address>")(walletItem)
blueprint.route("/download")(download)
blueprint.route("/updateData")(update_data)
blueprint.route("/exportCsv")(export_csv)
blueprint.route("/logs")(logs_page)
blueprint.route("/getLogs")(get_logs_view)
