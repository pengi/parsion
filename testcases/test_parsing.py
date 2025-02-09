from typing import Any, List, Tuple
import pytest
from parsion import Parsion, ParsionLexerError, \
    ParsionParseError, ParsionGeneratorError


class ExprLang(Parsion):
    LEXER_RULES = [
        (None,       r'(\s+)', lambda x: None),
        ('INT',      r'([0-9]+|0x[0-9a-fA-F]+)', lambda x: int(x, base=0)),

        ('+',        r'(\+)', lambda x: None),
        ('-',        r'(-)', lambda x: None),
        ('*',        r'(\*)', lambda x: None),
        ('/',        r'(\/)', lambda x: None),

        ('(',        r'([\(])', lambda x: None),
        (')',        r'([\)])', lambda x: None)
    ]
    GRAMMAR_RULES = [
        ('entry',       'entry',        'expr'),
        (None,          'expr',         'expr1'),
        ('expr_add',    'expr1',        'expr1 _+ expr2'),
        ('expr_sub',    'expr1',        'expr1 _- expr2'),
        (None,          'expr1',        'expr2'),
        ('expr_mult',   'expr2',        'expr2 _* expr3'),
        ('expr_div',    'expr2',        'expr2 _/ expr3'),
        (None,          'expr2',        'expr3'),
        ('expr_neg',    'expr3',        '_- expr4'),
        (None,          'expr3',        'expr4'),
        ('expr_int',    'expr4',        'INT'),
        (None,          'expr4',        '_( expr _)'),
    ]


class ExprLangInt(ExprLang):
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


class ExprLangAST(ExprLang):
    """
    Same language as ExprLang, but track syntax tree
    """

    def expr_add(self, lhs: Any, rhs: Any) -> Tuple[str, Any, Any]:
        return ('expr_add', lhs, rhs)

    def expr_sub(self, lhs: Any, rhs: Any) -> Tuple[str, Any, Any]:
        return ('expr_sub', lhs, rhs)

    def expr_mult(self, lhs: Any, rhs: Any) -> Tuple[str, Any, Any]:
        return ('expr_mult', lhs, rhs)

    def expr_div(self, lhs: Any, rhs: Any) -> Tuple[str, Any, Any]:
        return ('expr_div', lhs, rhs)

    def expr_neg(self, v: Any) -> Tuple[str, Any]:
        return ('expr_neg', v)

    def expr_int(self, v: Any) -> Tuple[str, Any]:
        return ('expr_int', v)


def test_simple_parse() -> None:
    lang = ExprLangInt()
    assert lang.parse("(12+3)*4") == (12 + 3) * 4
    assert lang.parse("(12+3-1)*4") == (12 + 3 - 1) * 4
    assert lang.parse("(12+3-1)*(32*-2)") == (12 + 3 - 1) * (32 * -2)
    assert lang.parse("(12+3-1+55*23*45)/(3*-2)") == \
        (12 + 3 - 1 + 55 * 23 * 45) // (3 * -2)


def test_simple_parse_ast() -> None:
    lang = ExprLangAST()
    assert lang.parse("(12+3)*(4-1)/-12") == \
        ('expr_div',
            ('expr_mult',
                ('expr_add',
                    ('expr_int', 12),
                    ('expr_int', 3)
                 ),
                ('expr_sub',
                    ('expr_int', 4),
                    ('expr_int', 1)
                 )
             ),
            ('expr_neg',
                ('expr_int', 12)
             )
         )


def test_parse_errors() -> None:
    lang = ExprLangInt()

    # Start position depends on innermost parse rule in generic handler.
    # In general, `pos`, and maybe `end` are probably the only useful values
    # in a grammar without error isolation

    # Missing token
    with pytest.raises(ParsionParseError) as e:
        lang.parse("(12+3")
    assert isinstance(e.value, ParsionParseError)
    assert (e.value.start, e.value.pos, e.value.end) == (4, 5, 5)

    # Extra token
    with pytest.raises(ParsionParseError) as e:
        lang.parse("(12+4))+8")
    assert isinstance(e.value, ParsionParseError)
    assert (e.value.start, e.value.pos, e.value.end) == (5, 6, 7)


def test_lexing_errors() -> None:
    lang = ExprLangInt()

    # Missing token
    with pytest.raises(ParsionLexerError):
        lang.parse("(12+3x")


def test_shift_reduce_conflict() -> None:
    class ShiftReduceLang(Parsion):  # pragma: no cover
        LEXER_RULES = [
            (sym, f'({sym})', lambda x: x)
            for sym in ['A', 'B', 'C', 'D']
        ]
        GRAMMAR_RULES = [
            (None,          'entry',        'expr'),
            ('op_A',        'expr',         'expr A expr'),
            ('op_B',        'expr',         'expr B expr'),
            ('lit_C',       'expr',         'C'),
            ('lit_D',       'expr',         'D')
        ]

        def op_A(self, *a: List[Any]) -> Any:
            return None

        def op_B(self, *a: List[Any]) -> Any:
            return None

        def lit_C(self, *a: List[Any]) -> Any:
            return None

        def lit_D(self, *a: List[Any]) -> Any:
            return None

    with pytest.raises(ParsionGeneratorError):
        ShiftReduceLang()
