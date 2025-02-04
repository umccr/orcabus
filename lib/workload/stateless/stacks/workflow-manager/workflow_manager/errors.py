class RerunDuplicationError(Exception):
    """
    Exception raised when a rerun duplication is not allowed.
    """

    def __init__(self, message="Duplication rerun is not allowed."):
        self.message = message
        super().__init__(self.message)
