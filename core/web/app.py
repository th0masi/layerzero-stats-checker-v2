import json
import signal

from core.database import DBManager
from core.utils import format_number, regex_replace
from flask import Flask

from core.consts import (
    ALL_SOURCE_NETWORKS,
    ALL_DESTINATION_NETWORKS,
    ALL_PROTOCOLS,
)

from core.web.subprocess import updater_process, is_updater_started

app = Flask(
    __name__,
    static_url_path="",
    static_folder="../static",
    template_folder="../templates",
)

app.jinja_env.filters["format_number"] = format_number
app.jinja_env.filters["regex_replace"] = regex_replace


@app.context_processor
def inject_base_template_context():
    checker_started = is_updater_started()
    db = DBManager()
    db_exists = db.exists()
    return dict(
        all_source_networks=ALL_SOURCE_NETWORKS,
        all_destination_networks=ALL_DESTINATION_NETWORKS,
        all_protocols=ALL_PROTOCOLS,
        checker_started=checker_started,
        db_exists=db_exists,
        refresh_disabled=checker_started or not db_exists,
        eye_disabled=not db_exists,
        stats_disabled=not db_exists,
        form_disabled=checker_started,
        download_disabled=not db_exists,
        json_state=json.dumps(
            {
                "isUpdaterStarted": checker_started,
            }
        ),
    )


def handler(signal_number, frame):
    if updater_process is not None:
        updater_process.kill()
    exit(0)


signal.signal(signal.SIGINT, handler)
