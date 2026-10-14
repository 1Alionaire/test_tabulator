import time
from django.core.management.base import BaseCommand
from django.db import close_old_connections
from django.db.models import Q
from main.time_signal import update_main_project_overdue_status
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Launch update_main_project_overdue_status with interval"

    def handle(self, *args, **opts):
        interval = 300
        while True:
            close_old_connections()  # иначе соединение с БД со временем «протухнет»
            try:
                update_main_project_overdue_status()
            except Exception:
                logger.exception("update_main_project_overdue_status error")  # цикл не прерывается
            time.sleep(interval)