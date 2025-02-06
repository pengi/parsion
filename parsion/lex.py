
import re
from typing import Any, Callable, Generator, List, Optional, Set, Tuple
from .exceptions import ParsionException


class ParsionLexerError(ParsionException):
    intput: str
    pos: int

    def __init__(self, message: str, input: str, pos: int):
        super().__init__(message)
        self.input = input
        self.pos = pos

    def __str__(self) -> str:
        """
        Format lexer error

        >>> str(ParsionLexerError("msg", "my input", 3))
        "msg (pos 3 in 'my input')"
        """
        return f'{self.args[0]} (pos {self.pos} in {self.input!r})'


class ParsionToken:
    name: str
    value: Any
    start: int
    end: int

    def __init__(self, name: str, value: Any, start: int, end: int):
        self.name = name
        self.value = value
        self.start = start
        self.end = end

    def __str__(self) -> str:
        """
        Format token as string

        >>> str(ParsionToken("my_name", "my_value", 12, 14))
        "[@ 12 my_name: 'my_value']"

        >>> str(ParsionToken("my_name", None, 12, 14))
        '[@ 12 my_name]'
        """
        if self.value is None:
            return f'[@{self.start:>3} {self.name}]'
        else:
            return f'[@{self.start:>3} {self.name}: {self.value!r}]'


class ParsionEndToken(ParsionToken):
    def __init__(self, pos: int):
        super().__init__('$END', '$END', pos, pos)


class ParsionLexer:
    rules: List[Tuple[Optional[str], re.Pattern[str],
                      Callable[[str], Optional[Any]]]]

    def __init__(self,
                 rules: List[Tuple[
                     Optional[str],
                     str,
                     Callable[[str], Optional[Any]]
                 ]]):
        self.rules = [
            (name, re.compile(regexp), handler)
            for (name, regexp, handler)
            in rules
        ]

    def next_token(self, input: str, pos: int) -> Optional[ParsionToken]:
        for name, regexp, handler in self.rules:
            m = regexp.match(input, pos)
            if m is not None:
                if name is None:
                    return self.next_token(input, m.end(1))
                else:
                    return ParsionToken(
                        name,
                        handler(m.group(1)),
                        m.start(1),
                        m.end(1)
                    )
        return None

    def tokenize(self, input: str) -> Generator[ParsionToken, None, None]:
        pos = 0
        while pos < len(input):
            token = self.next_token(input, pos)
            if token is None:
                raise ParsionLexerError('Invalid input', input, pos)
            pos = token.end
            yield token
        yield ParsionEndToken(pos)

    def get_token_set(self) -> Set[str]:
        return {
            rule[0]
            for rule
            in self.rules
            if rule[0] is not None
        }.union({'$END'})
