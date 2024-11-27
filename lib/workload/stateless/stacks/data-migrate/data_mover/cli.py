import logging

import click

from data_mover.data_mover import DataMover

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


@click.group()
def cli():
    pass


@cli.command()
@click.option(
    "--source",
    required=True,
    help="The source to copy from.",
)
@click.option(
    "--destination",
    required=True,
    help="The destination to copy to.",
)
def move(source, destination):
    """
    Copy files from the source to the destination and delete the source if successful.
    This command calls `aws s3 sync` directly, so it expects the AWS cli to be installed.
    """
    dm = DataMover(source, destination, logger=logger)
    dm.sync()
    dm.delete()


@cli.command()
@click.option(
    "--source",
    required=True,
    help="The source to copy from.",
)
@click.option(
    "--destination",
    required=True,
    help="The destination to copy to.",
)
def copy(source, destination):
    """
    Copy files from the source to the destination and keep the source if successful.
    This command calls `aws s3 sync` directly, so it expects the AWS cli to be installed.
    """
    dm = DataMover(source, destination, logger=logger)
    dm.sync()


if __name__ == "__main__":
    cli()
