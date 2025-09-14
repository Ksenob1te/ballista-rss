class RSSServiceException(Exception):
    pass

class DatabaseException(RSSServiceException):
    pass

class ExternalAPIException(RSSServiceException):
    pass