# hrms/apps.py
from django.apps import AppConfig
import logging
import os
import sys

logger = logging.getLogger(__name__)

class EmployeeDetailsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'hrms'

    def ready(self):
        # Only run this in runserver and main thread
        if 'runserver' in sys.argv and os.environ.get('RUN_MAIN') == 'true':
            from hrms.models import EmployeeDetails
            try:
                logger.info("💡 Checking birthdays on startup...")
                EmployeeDetails.send_birthday_wishes()
            except Exception as e:
                logger.error(f"❌ Error sending birthday emails on startup: {e}", exc_info=True)




# from django.apps import AppConfig


# class EmployeeDetailsConfig(AppConfig):
#     default_auto_field = 'django.db.models.BigAutoField'
#     name = 'hrms'