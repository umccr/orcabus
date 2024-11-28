import logging

from pg_dd.pg_dd import PgDDLocal, PgDDS3
import click

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


@click.group()
def cli():
    pass


@cli.command()
@click.option(
    "--exists-ok/--no-exists-ok",
    default=True,
    help="If the file already exists, do not download it.",
)
def download(exists_ok):
    """
    Download S3 CSV dumps to the local directory.
    """
    PgDDS3(logger=logger).download_local(exists_ok)


@cli.command()
@click.option(
    "--database",
    help="Specify the database to upload, uploads all databases by default.",
)
@click.option(
    "--dump-db/--no-dump-db",
    default=False,
    help="Dump from the database first before uploading.",
)
def upload(database, dump_db):
    """
    Uploads local CSV dumps to S3.
    """
    if dump_db:
        PgDDLocal(logger=logger).write_to_dir(database)

    PgDDS3(logger=logger).write_to_bucket(database)


@cli.command()
@click.option(
    "--database", help="Specify the database to dump, dumps all databases by default."
)
def dump(database):
    """
    Dump from the local database to CSV files.
    """
    PgDDLocal(logger=logger).write_to_dir(database)


@cli.command()
@click.option(
    "--download-exists-ok/--no-download-exists-ok",
    default=True,
    help="Download the CSV files from S3 if they are not already in the local directory.",
)
@click.option(
    "--only-empty/--no-only-empty",
    default=True,
    help="Only load into tables that are empty and exist in the database.",
)
def load(download_exists_ok, only_empty):
    """
    Load local CSV files into the database.
    """
    if download_exists_ok:
        PgDDS3(logger=logger).download_local(download_exists_ok)

    PgDDLocal(logger=logger).load_to_database(only_empty)


if __name__ == "__main__":
    cli()
