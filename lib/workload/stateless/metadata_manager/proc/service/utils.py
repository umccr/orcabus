import logging
import os
from django.core.management import call_command

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def clean_model_history():
    """
    The function will clean history for which where models have a history feature enabled

    When django uses the `save()` function, history table might be populated despite no changes (e.g.
    update_or_create). The history feature provided by django-simple-history track all signal that django sends to
    save model thus create duplicates. This clean function will remove these duplicates and only retain changes.
    """
    logger.info('removing duplicate history records')
    call_command("clean_duplicate_history", "--auto", stdout=open(os.devnull, 'w'))
    logger.info('duplicated history removed successfully')
