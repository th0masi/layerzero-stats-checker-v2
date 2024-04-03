import logging

from core.database import DBManager
from core.pproxy import ProxyManager
from core.utils import check_wallets
from flask import Flask, render_template, request, jsonify, send_file

logging.getLogger('flask.app').setLevel(logging.WARNING)
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)
app.jinja_env.filters['format_number'] = format_number
app.jinja_env.filters['get_hours'] = get_hours


@app.route('/update_wallet')
def refresh_wallet():
    wallet_address = request.args.get('address')

    check_stat_by_wallet(wallet_address)
    return jsonify(
        {
            'status': 'success',
            'message': 'Data refreshed successfully'
        }
    )


@app.route('/refresh')
def refresh_all():
    check_stats()
    return jsonify(
        {
            'status': 'success',
            'message': 'Data refreshed successfully'
         }
    )


@app.route('/')
async def index():
    sort_column = request.args.get('sort', 'current_rank')
    db_manager = DBManager()
    metrics = await db_manager.get_statistics()
    wallets = await db_manager.get_sorted_wallets(
        sort_column=sort_column
    )

    return render_template(
        'index.html',
        metrics=metrics,
        wallets=wallets,
    )


@app.route('/check_data')
async def check_data_for_create_db():
    is_reset_db = True
    wallets = []
    names = []
    proxies = []

    try:
        if not proxies:
            # TODO пустой список прокси
            pass

        pm = ProxyManager(
            proxy_list=proxies
        )
        checked_proxy = pm.run()

        if not checked_proxy:
            # TODO нет валидных прокси
            pass

        wallets, names = await check_wallets(
            is_reset_db=is_reset_db,
            wallets=wallets,
            names=names,
        )

    except ValueError as e:
        # TODO здесь мы ловим ошибку: неверный формат кошельков
        pass

    return render_template(
        'index.html',
        wallets=wallets,
    )


@app.route('/update_db')
async def create_db():
    is_reset_db = True
    wallets = []
    names = []
    proxies = []
    db_manager = DBManager()

    # если включен свитчер - удалить старые данные
    if is_reset_db:
        await db_manager.delete_database()

    # создаем БД - таблица wallet (wallets/names)
    await db_manager.create_database(
        address_list=wallets,
        name_list=names,
    )

    # создаем таблицу proxies
    await db_manager.create_proxy_table(
        proxy_list=proxies,
    )

    return render_template(
        'index.html',
        wallets=wallets,
    )
