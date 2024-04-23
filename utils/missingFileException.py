class MissingFileException(Exception):
    "Raised when the file is not found in the db"
    
    def __init__(self, filename, message = f"File not found in the db : "):
        super(MissingFileException, self).__init__(message + filename)