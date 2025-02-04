import pytest
from parsion import Parsion, ParsionInternalError


def test_static_table():
    class StaticLang(Parsion):
        LEXER_RULES = [
            (None,       r'(\s+)', lambda x: None),
            ('INT',      r'([0-9]+|0x[0-9a-fA-F]+)', lambda x: int(x, base=0))
        ]
        # GRAMMAR_RULES = [
        #    ('entry',         'entry',        'expr'),
        #    ('expr_int',      'expr',         'INT'),
        #    ('expr_int_expr', 'expr',         'INT expr')
        # ]
        STATIC_GRAMMAR = [
            ('$ENTRY', None, [True, False]),
            ('entry', 'entry', [True]),
            ('expr', 'expr_int', [True]),
            ('expr', 'expr_int_expr', [True, True])
        ]
        STATIC_TABLE = [
            {'INT': ('s', 1), 'expr': ('s', 2), 'entry': ('s', 3)},
            {'INT': ('s', 1), 'expr': ('s', 4), '$END': ('r', 2)},
            {'$END': ('r', 1)},
            {'$END': ('s', 5)},
            {'$END': ('r', 3)},
            {}
        ]
        STATIC_ERROR_HANDLERS = {}

        def expr_int(self, x):
            return [x]

        def expr_int_expr(self, x, xs):
            return [x] + xs

    static_lang = StaticLang()
    assert static_lang.parse('12 13 14 15') == [12, 13, 14, 15]


def test_static_table_error():
    class StaticLang(Parsion):
        LEXER_RULES = [
            (None,       r'(\s+)', lambda x: None),
            ('INT',      r'([0-9]+|0x[0-9a-fA-F]+)', lambda x: int(x, base=0))
        ]
        # GRAMMAR_RULES = [
        #    ('entry',         'entry',        'expr'),
        #    ('expr_int',      'expr',         'INT'),
        #    ('expr_int_expr', 'expr',         'INT expr')
        # ]
        STATIC_GRAMMAR = [
            ('$ENTRY', None, [True, False]),
            ('entry', 'entry', [True]),
            ('expr', 'expr_int', [True]),
            ('expr', 'expr_int_expr', [True, True])
        ]
        STATIC_TABLE = [
            {'INT': ('XXXX', 1), 'expr': ('s', 2), 'entry': ('s', 3)},
            {'INT': ('s', 1), 'expr': ('s', 4), '$END': ('r', 2)},
            {'$END': ('r', 1)},
            {'$END': ('s', 5)},
            {'$END': ('r', 3)},
            {}
        ]
        STATIC_ERROR_HANDLERS = {}

        def expr_int(self, x):  # pragma: no cover
            return [x]

        def expr_int_expr(self, x, xs):  # pragma: no cover
            return [x] + xs

    static_lang = StaticLang()

    with pytest.raises(ParsionInternalError):
        static_lang.parse('12 13 14 15')
