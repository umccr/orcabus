import logging
import sys

import click

from data_mover.data_mover import DataMover

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


def main():
    try:
        cli(standalone_mode=False)
        sys.exit(0)
    except Exception as e:
        DataMover.send_failure(str(e))
        logger.error(str(e))
        sys.exit(1)


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
    data_mover = DataMover(source, destination, logger=logger)
    data_mover.sync()
    data_mover.delete()
    data_mover.send_output(command="move")


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
    data_mover = DataMover(source, destination, logger=logger)
    data_mover.sync()
    data_mover.send_output(command="copy")


if __name__ == "__main__":
    main()
