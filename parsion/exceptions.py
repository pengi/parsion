class ParsionException(Exception):
    pass


class ParsionGeneratorError(ParsionException):
    pass


class ParsionInternalError(ParsionException):
    pass


class ParsionSelfCheckError(ParsionException):
    pass


class ParsionParseError(Exception):
    pass
