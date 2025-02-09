from typing import Set


class ParsionException(Exception):
    pass


class ParsionGeneratorError(ParsionException):
    pass


class ParsionInternalError(ParsionException):
    pass


class ParsionSelfCheckError(ParsionException):
    pass


class ParsionParseError(Exception):
    def __init__(self,
                 msg: str,
                 start: int,
                 pos: int,
                 end: int,
                 expect: Set[str]):
        super().__init__(self, msg, start, pos, end)
        self.start = start
        self.pos = pos
        self.end = end
        self.expect = expect
