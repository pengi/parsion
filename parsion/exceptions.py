class ParsionException(Exception):
    pass

class ParsionInternalError(Exception):
    pass

class ParsionSelfCheckError(ParsionException):
    pass
