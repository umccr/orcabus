import logging
import subprocess


class DataMover:
    """
    A class to manage moving data.
    """

    def __init__(
        self,
        source: str,
        destination: str,
        repeat: int = 2,
        # 12 hours
        timeout: int = 43200,
        logger: logging.Logger = logging.getLogger(__name__),
    ):
        self.source = source
        self.destination = destination
        self.repeat = repeat
        self.timeout = timeout
        self.logger = logger

    def sync(self):
        """
        Sync destination and source.
        """
        self.logger.info(
            f"syncing {self.repeat} times from {self.source} to {self.destination}"
        )

        out = None
        for _ in range(self.repeat):
            out = subprocess.run(
                ["aws", "s3", "sync", self.source, self.destination],
                check=True,
                # 1 day
                timeout=self.timeout,
            )

        if out.stdout is not None:
            raise Exception("failed to sync - non-empty output")

    def delete(self):
        """
        Delete the source.
        """
        self.logger.info(f"deleting files from {self.source}")

        subprocess.run(
            ["aws", "s3", "rm", "--recursive", self.source],
            check=True,
            # 1 day
            timeout=self.timeout,
        )
