from __future__ import annotations

import logging
import signal
import sys
import threading

from must_dashboard.config import Settings
from must_dashboard.http import AppContext, DashboardServer
from must_dashboard.poller import EventHub, InverterPoller
from must_dashboard.storage import Storage


def main() -> int:
    settings = Settings.from_env()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    storage = Storage(settings.db_path)
    events = EventHub()
    poller = InverterPoller(settings, storage, events)
    context = AppContext(settings=settings, storage=storage, poller=poller)
    server = DashboardServer((settings.host, settings.port), context)

    def stop(*_args: object) -> None:
        # BaseServer.shutdown must run outside the serve_forever thread.
        threading.Thread(target=server.shutdown, name="dashboard-shutdown", daemon=True).start()

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    poller.start()
    logging.getLogger(__name__).info("dashboard listening at http://%s:%s", settings.host, settings.port)
    try:
        server.serve_forever(poll_interval=0.5)
    finally:
        poller.stop()
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
