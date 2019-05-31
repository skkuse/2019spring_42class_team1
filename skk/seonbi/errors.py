class SourceNotFound(Exception):
    def __init__(self, message, errors):
        super().__init__('The source does not exist.')
        self.errors = errors
