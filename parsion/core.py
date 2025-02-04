from .lex import ParsionLexer
from .parser import ParsionParser
from .parsegen import ParsionFSM


class ParsionBase:
    LEXER_RULES = []
    SELF_CHECK = True

    def __init__(self, lexer, parser):
        self.lexer = lexer
        self.parser = parser
        if self.SELF_CHECK:
            self._self_check()

    def parse(self, input):
        tokens = self.lexer.tokenize(input)
        return self.parser.parse(tokens, self)

    def _self_check(self):
        from .self_check import run_self_check
        run_self_check(self)

    def entry(self, v):
        return v


class Parsion(ParsionBase):
    GRAMMAR_RULES = []

    def __init__(self):
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
    STATIC_GRAMMAR = None
    STATIC_TABLE = None
    STATIC_ERROR_HANDLERS = None

    def __init__(self):
        super().__init__(
            ParsionLexer(self.LEXER_RULES),
            ParsionParser(
                self.STATIC_GRAMMAR,
                self.STATIC_TABLE,
                self.STATIC_ERROR_HANDLERS
            )
        )
