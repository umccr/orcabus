import json

from django.core.management import BaseCommand

from django.db.models import Q

from app.models import Library


# https://docs.djangoproject.com/en/5.0/howto/custom-management-commands/
class Command(BaseCommand):
    help = "Delete all DB data"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="List all libraries that will be deleted without actually deleting them",
        )

    def handle(self, *args, **options):
        all_libraries = Library.objects.all().filter(
            Q(library_id__icontains="_rerun") | Q(library_id__icontains="_topup"))

        print("Libraries contain matching pattern:")
        print(json.dumps([library.library_id for library in all_libraries], indent=4))

        if not options["dry_run"]:
            print("Deleting all libraries")
            all_libraries.delete()
        else:
            print("Dry run: not deleting libraries")

        print('Completed')
