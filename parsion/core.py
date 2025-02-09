from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from .exceptions import ParsionParseError
from .lex import ParsionLexer
from .parser import ParsionParser
from .parsegen import ParsionFSM


class ParsionBase:
    LEXER_RULES: List[Tuple[Optional[str], str,
                            Callable[[str], Optional[Any]]]] = []
    SELF_CHECK: bool = True

    lexer: ParsionLexer
    parser: ParsionParser

    def __init__(self, lexer: ParsionLexer, parser: ParsionParser):
        self.lexer = lexer
        self.parser = parser
        if self.SELF_CHECK:
            self._self_check()

    def parse(self, input: str) -> Any:
        tokens = self.lexer.tokenize(input)
        return self.parser.parse(tokens, self)

    def _self_check(self) -> None:
        from .self_check import run_self_check
        run_self_check(self)

    def entry(self, v: Any) -> Any:
        return v

    def default_error(self,
                      gen: str,
                      start: int,
                      pos: int,
                      end: int,
                      expect: Set[str]) -> Any:
        raise ParsionParseError(
            'Error parsing',
            start, pos, end, expect
        )


class Parsion(ParsionBase):
    GRAMMAR_RULES: List[Tuple[Optional[str], str, str]] = []

    parse_grammar: List[Tuple[str, Optional[str], List[bool]]]
    parse_table: List[Dict[str, Tuple[str, int]]]
    error_handlers: Dict[int, Dict[str, Tuple[str, str]]]

    def __init__(self) -> None:
        (
            self.parse_grammar,
            self.parse_table,
            self.error_handlers
        ) = ParsionFSM(self.GRAMMAR_RULES).export()

        super().__init__(
            ParsionLexer(self.LEXER_RULES),
            ParsionParser(
                self.parse_grammar,
                self.parse_table,
                self.error_handlers
            )
        )


class ParsionStatic(ParsionBase):
    STATIC_GRAMMAR: List[Tuple[str, Optional[str], List[bool]]] = []
    STATIC_TABLE: List[Dict[str, Tuple[str, int]]] = []
    STATIC_ERROR_HANDLERS: Dict[int, Dict[str, Tuple[str, str]]] = {}

    def __init__(self) -> None:
        super().__init__(
            ParsionLexer(self.LEXER_RULES),
            ParsionParser(
                self.STATIC_GRAMMAR,
                self.STATIC_TABLE,
                self.STATIC_ERROR_HANDLERS
            )
        )
