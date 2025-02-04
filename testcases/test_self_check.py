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


def test_working():
    """
    Self check of base language fixture
    """
    class TestLang(BaseLang):
        def expr_int(self, v):
            return v

        def expr_int_expr(self, v, e):
            return v + e

    lang = TestLang()
    assert lang.parse("1 3 4 5") == 1 + 3 + 4 + 5


def test_extra_arg():
    class TestLang(BaseLang):
        def expr_int(self, v):  # pragma: no cover
            return v

        def expr_int_expr(self, v, e, extra):  # pragma: no cover
            return v + e

    with pytest.raises(ParsionSelfCheckError):
        TestLang()


def test_missing_arg():
    class TestLang(BaseLang):
        def expr_int(self, v):  # pragma: no cover
            return v

        def expr_int_expr(self, v):  # pragma: no cover
            return v

    with pytest.raises(ParsionSelfCheckError):
        TestLang()


def test_default_value_expected():
    class TestLang(BaseLang):
        def expr_int(self, v):
            return v

        def expr_int_expr(self, v, e=12):
            return v + e

    lang = TestLang()
    assert lang.parse("1 3 4 5") == 1 + 3 + 4 + 5


def test_default_value_extra():
    class TestLang(BaseLang):
        def expr_int(self, v):
            return v

        def expr_int_expr(self, v, e, extra=12):
            return v + e

    lang = TestLang()
    assert lang.parse("1 3 4 5") == 1 + 3 + 4 + 5


def test_default_value_error():
    class TestLang(BaseLang):
        def expr_int(self, v):  # pragma: no cover
            return v

        def expr_int_expr(self, v, e, c, d, f, extra=12):  # pragma: no cover
            return v + e

    with pytest.raises(ParsionSelfCheckError):
        TestLang()


def test_variable_args():
    class TestLang(BaseLang):
        def expr_int(self, v):
            return v

        def expr_int_expr(self, *args):
            return sum(args)

    lang = TestLang()
    assert lang.parse("1 3 4 5") == 1 + 3 + 4 + 5


def test_variable_args_error():
    class TestLang(BaseLang):
        def expr_int(self, v):  # pragma: no cover
            return v

        def expr_int_expr(self, a, b, c, d, *args):  # pragma: no cover
            return sum(args)

    with pytest.raises(ParsionSelfCheckError):
        TestLang()


def test_missing_func():
    class TestLang(BaseLang):
        def expr_int(self, v):  # pragma: no cover
            return v

    with pytest.raises(ParsionSelfCheckError):
        TestLang()


def test_self_check_disabled():
    class TestLang(BaseLang):
        SELF_CHECK = False

        def expr_int(self, v):
            return v

    # Parser generation should work
    lang = TestLang()

    # Missing handler not triggered, should work
    assert lang.parse('12') == 12

    # Missing handler is triggered
    with pytest.raises(AttributeError):
        lang.parse('12 13')


def test_invalid_anonymous_rule():
    class TestLang(BaseLang):
        GRAMMAR_RULES = [
            ('entry',         'entry',        'expr'),
            ('expr_int',      'expr',         'INT'),
            (None, 'expr',         'INT expr')
        ]

        def expr_int(self, v):  # pragma: no cover
            return v

    with pytest.raises(ParsionSelfCheckError):
        TestLang()
