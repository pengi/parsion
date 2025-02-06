from typing import Any
import pytest
from parsion import Parsion, ParsionSelfCheckError


class BaseLang(Parsion):
    LEXER_RULES = [
        (None,       r'(\s+)', lambda x: None),
        ('INT',      r'([0-9]+|0x[0-9a-fA-F]+)', lambda x: int(x, base=0))
    ]
    GRAMMAR_RULES = [
        ('entry',         'entry',        'expr'),
        ('expr_int',      'expr',         'INT'),
        ('expr_int_expr', 'expr',         'INT expr')
    ]


def test_working() -> None:
    """
    Self check of base language fixture
    """
    class TestLang(BaseLang):
        def expr_int(self, v: int) -> int:
            return v

        def expr_int_expr(self, v: int, e: int) -> int:
            return v + e

    lang = TestLang()
    assert lang.parse("1 3 4 5") == 1 + 3 + 4 + 5


def test_extra_arg() -> None:
    class TestLang(BaseLang):
        def expr_int(self, v: int) -> int:  # pragma: no cover
            return v

        def expr_int_expr(self,
                          v: int,
                          e: int,
                          extra: Any
                          ) -> int:  # pragma: no cover
            return v + e

    with pytest.raises(ParsionSelfCheckError):
        TestLang()


def test_missing_arg() -> None:
    class TestLang(BaseLang):
        def expr_int(self, v: int) -> int:  # pragma: no cover
            return v

        def expr_int_expr(self, v: int) -> int:  # pragma: no cover
            return v

    with pytest.raises(ParsionSelfCheckError):
        TestLang()


def test_default_value_expected() -> None:
    class TestLang(BaseLang):
        def expr_int(self, v: int) -> int:
            return v

        def expr_int_expr(self, v: int, e: int = 12) -> int:
            return v + e

    lang = TestLang()
    assert lang.parse("1 3 4 5") == 1 + 3 + 4 + 5


def test_default_value_extra() -> None:
    class TestLang(BaseLang):
        def expr_int(self, v: int) -> int:
            return v

        def expr_int_expr(self, v: int, e: int, extra: int = 12) -> int:
            return v + e

    lang = TestLang()
    assert lang.parse("1 3 4 5") == 1 + 3 + 4 + 5


def test_default_value_error() -> None:
    class TestLang(BaseLang):
        def expr_int(self, v: int) -> int:  # pragma: no cover
            return v

        def expr_int_expr(self,
                          v: int,
                          e: int,
                          c: int,
                          d: int,
                          f: int,
                          extra: int = 12
                          ) -> int:  # pragma: no cover
            return v + e

    with pytest.raises(ParsionSelfCheckError):
        TestLang()


def test_variable_args() -> None:
    class TestLang(BaseLang):
        def expr_int(self, v: int) -> int:
            return v

        def expr_int_expr(self, *args: int) -> int:
            return sum(args)

    lang = TestLang()
    assert lang.parse("1 3 4 5") == 1 + 3 + 4 + 5


def test_variable_args_error() -> None:
    class TestLang(BaseLang):
        def expr_int(self, v: int) -> int:  # pragma: no cover
            return v

        def expr_int_expr(self,
                          a: int,
                          b: int,
                          c: int,
                          d: int,
                          *args: int
                          ) -> int:  # pragma: no cover
            return sum(args)

    with pytest.raises(ParsionSelfCheckError):
        TestLang()


def test_missing_func() -> None:
    class TestLang(BaseLang):
        def expr_int(self, v: int) -> int:  # pragma: no cover
            return v

    with pytest.raises(ParsionSelfCheckError):
        TestLang()


def test_self_check_disabled() -> None:
    class TestLang(BaseLang):
        SELF_CHECK = False

        def expr_int(self, v: int) -> int:
            return v

    # Parser generation should work
    lang = TestLang()

    # Missing handler not triggered, should work
    assert lang.parse('12') == 12

    # Missing handler is triggered
    with pytest.raises(AttributeError):
        lang.parse('12 13')


def test_invalid_anonymous_rule() -> None:
    class TestLang(BaseLang):
        GRAMMAR_RULES = [
            ('entry',         'entry',        'expr'),
            ('expr_int',      'expr',         'INT'),
            (None, 'expr',         'INT expr')
        ]

        def expr_int(self, v: int) -> int:  # pragma: no cover
            return v

    with pytest.raises(ParsionSelfCheckError):
        TestLang()
