from typing import Any, List, Optional, Set
import pytest
from parsion import Parsion, ParsionSelfCheckError, ParsionGeneratorError
from parsion.exceptions import ParsionParseError


class ExprLang(Parsion):  # pragma: no cover
    LEXER_RULES = [
        (None,       r'(\s+)', lambda x: None),
        ('INT',      r'([0-9]+|0x[0-9a-fA-F]+)', lambda x: int(x, base=0)),

        ('+',        r'(\+)', lambda x: None),
        ('-',        r'(-)', lambda x: None),
        ('*',        r'(\*)', lambda x: None),
        ('/',        r'(\/)', lambda x: None),

        ('(',        r'([\(])', lambda x: None),
        (')',        r'([\)])', lambda x: None),
        (';',        r'(;)', lambda x: None)
    ]
    GRAMMAR_RULES = [
        ('entry',         'entry',        'stmts'),
        ('stmts_list',    'stmts',        'stmt _; stmts'),
        ('stmts_tail',    'stmts',        'stmt'),

        # proxy statement, to be able to isolate errors to top level
        (None,            'stmt',         'expr'),
        ('stmt_error',    'stmt',         '$ERROR'),

        (None,            'expr',         'expr1'),
        ('expr_add',      'expr1',        'expr1 _+ expr2'),
        ('expr_sub',      'expr1',        'expr1 _- expr2'),
        (None,            'expr1',        'expr2'),
        ('expr_mult',     'expr2',        'expr2 _* expr3'),
        ('expr_div',      'expr2',        'expr2 _/ expr3'),
        (None,            'expr2',        'expr3'),
        ('expr_neg',      'expr3',        '_- expr4'),
        (None,            'expr3',        'expr4'),
        ('expr_int',      'expr4',        'INT'),
        (None,            'expr4',        '_( expr _)'),
    ]

    def stmts_list(self,
                   expr: Optional[int],
                   list: List[Optional[int]]
                   ) -> List[Optional[int]]:
        return [expr] + list

    def stmts_tail(self,
                   expr: Optional[int]
                   ) -> List[Optional[int]]:
        return [expr]

    def expr_add(self, lhs: int, rhs: int) -> int:
        return lhs + rhs

    def expr_sub(self, lhs: int, rhs: int) -> int:
        return lhs - rhs

    def expr_mult(self, lhs: int, rhs: int) -> int:
        return lhs * rhs

    def expr_div(self, lhs: int, rhs: int) -> int:
        return lhs // rhs

    def expr_neg(self, v: int) -> int:
        return -v

    def expr_int(self, v: int) -> int:
        return v


class ExprLangErrorHandler(ExprLang):  # pragma: no cover
    def stmt_error(self,
                   gen: str,
                   start: int,
                   pos: int,
                   end: int,
                   expect: Set[str]) -> Any:
        assert gen == 'stmt'
        return None


class ExprDefaultErrorHandler(ExprLang):  # pragma: no cover
    def stmt_error(self,
                   gen: str,
                   start: int,
                   pos: int,
                   end: int,
                   expect: Set[str]) -> Any:
        # Pass error handler to default. Usually added directly
        return self.default_error(gen, start, pos, end, expect)


def test_simple_parse() -> None:
    lang = ExprLangErrorHandler()
    assert lang.parse("(12+3)*4; 1+3; 43*4") == [(12 + 3) * 4, 1 + 3, 43 * 4]


def test_simple_error_stmt() -> None:
    """
    Test that error in one statement is isolated to that statement
    """
    lang = ExprLangErrorHandler()
    assert lang.parse("(12+3)*4; 3+ *; 43*4") == [(12 + 3) * 4, None, 43 * 4]


def test_simple_default_error_stmt() -> None:
    """
    Test that the positions in the error are correctly reported
    """
    lang = ExprDefaultErrorHandler()
    input = "(12+3)*4; 3+ *; 43*4"
    with pytest.raises(ParsionParseError) as e:
        lang.parse(input)

    assert isinstance(e.value, ParsionParseError)
    assert input[e.value.start:e.value.pos] == "3+ "
    assert input[e.value.pos:e.value.end] == "*"

    # RHS of + is expr2, so all symbols that can generate expr2
    assert e.value.expect == {'expr2', 'expr3', 'expr4', '-', 'INT', '('}


def test_missing_error_handler() -> None:
    with pytest.raises(ParsionSelfCheckError):
        ExprLang()


def test_conflicing_error_handlers() -> None:
    class ConflictingErrorLang(Parsion):
        LEXER_RULES = [
            (sym, f'({sym})', lambda x: x)
            for sym in ['A', 'B', 'C', 'D']
        ]
        GRAMMAR_RULES = [
            (None,          'entry',        'stmt_a _C'),
            (None,          'entry',        'stmt_b _C'),
            ('error_a',     'stmt_a',       '$ERROR'),
            ('error_b',     'stmt_b',       '$ERROR'),
            (None,          'stmt_a',       'A'),
            (None,          'stmt_b',       'B')
        ]

        def error_a(self, *a: List[Any]) -> None:  # pragma: no cover
            return None

        def error_b(self, *a: List[Any]) -> None:  # pragma: no cover
            return None

    with pytest.raises(ParsionGeneratorError):
        ConflictingErrorLang()
