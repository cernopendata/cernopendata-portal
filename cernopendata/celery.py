# -*- coding: utf-8 -*-

"""cernopendata base Invenio configuration."""

from celery.signals import worker_process_init
from flask_celeryext import create_celery_app

from .factory import create_app

celery = create_celery_app(create_app())


@worker_process_init.connect
def _reset_queue_connection_pools(**kwargs):
    """Reset stale cached connection pools on invenio-queues Queue objects after fork."""
    try:
        state = celery.app.extensions.get("invenio-queues")
        if state and hasattr(state, "queues"):
            for queue in state.queues.values():
                queue.__dict__.pop("connection_pool", None)
    except Exception:
        pass
