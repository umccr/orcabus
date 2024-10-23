from django.core.management import BaseCommand

from app.tests.utils import clear_all_data


# https://docs.djangoproject.com/en/5.0/howto/custom-management-commands/
class Command(BaseCommand):
    help = "Delete all DB data"

    def handle(self, *args, **options):
        clear_all_data()

        print("Done")
