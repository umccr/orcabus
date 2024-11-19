from pg_dd.pg_dd import PgDDLocal, PgDDS3
import click


@click.group()
def cli():
    pass


@cli.command()
def download():
    """
    Download S3 CSV dumps to the local directory.
    """
    PgDDS3().download_local()


@cli.command()
def upload():
    """
    Uploads local CSV dumps to S3.
    """
    PgDDS3().write_to_bucket()


@cli.command()
def dump():
    """
    Dump from the local database to CSV files.
    """
    PgDDLocal().write_to_dir()


@cli.command()
def load():
    """
    Load local CSV files into the database
    """
    PgDDLocal().load_to_database()


if __name__ == "__main__":
    cli()
