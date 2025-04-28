class SampleSheetParsingError(Exception):
    """
    Exception raised when a sample sheet parsing fails
    """

    def __init__(self, message="Sample sheet parsing failed"):
        self.message = message