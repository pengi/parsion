import pytest
from parsion import Parsion, ParsionLexerError


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
    GRAMMAR_RULES = []


def test_simple_lex():
    lang = ExprLang()
    raw_tokens = list(lang.lex.tokenize("(12+3)*4"))
    str_tokens = [tok.name for tok in raw_tokens]
    assert str_tokens == ['(', 'INT', '+', 'INT', ')', '*', 'INT', '$END']
    assert raw_tokens[1].value == 12
    assert raw_tokens[3].value == 3
    assert raw_tokens[6].value == 4


def test_lex_token_set():
    lang = ExprLang()
    assert lang.lex.get_token_set() == {
        'INT', '+', '-', '*', '/', '(', ')', '$END'
    }


def test_invalid_token():
    lang = ExprLang()
    with pytest.raises(ParsionLexerError):
        list(lang.lex.tokenize('( 1+3 ) invalid'))
