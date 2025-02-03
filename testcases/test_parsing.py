import pytest
from parsion import *

class ExprLang(Parsion):
    LEXER_RULES = [
        (None,       r'(\s+)',                     lambda x: None),
        ('INT',      r'([0-9]+|0x[0-9a-fA-F]+)',   lambda x: int(x,base=0)),

        ('+',        r'(\+)',                      lambda x: None),
        ('-',        r'(-)',                       lambda x: None),
        ('*',        r'(\*)',                      lambda x: None),
        ('/',        r'(\/)',                      lambda x: None),

        ('(',        r'([\(])',                    lambda x: None),
        (')',        r'([\)])',                    lambda x: None)
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
    
    def expr_add(self, lhs, rhs):
        return lhs + rhs
    
    def expr_sub(self, lhs, rhs):
        return lhs - rhs
    
    def expr_mult(self, lhs, rhs):
        return lhs * rhs
    
    def expr_div(self, lhs, rhs):
        return lhs // rhs
    
    def expr_neg(self, v):
        return -v
    
    def expr_int(self, v):
        return v

class ExprLangAST(ExprLang):
    """
    Same language as ExprLang, but track syntax tree
    """
    def expr_add(self, lhs, rhs):
        return ('expr_add', lhs, rhs)
    
    def expr_sub(self, lhs, rhs):
        return ('expr_sub', lhs, rhs)
    
    def expr_mult(self, lhs, rhs):
        return ('expr_mult', lhs, rhs)
    
    def expr_div(self, lhs, rhs):
        return ('expr_div', lhs, rhs)
    
    def expr_neg(self, v):
        return ('expr_neg', v)
    
    def expr_int(self, v):
        return ('expr_int', v)

def test_simple_parse():
    lang = ExprLang()
    assert lang.parse("(12+3)*4") == (12+3)*4
    assert lang.parse("(12+3-1)*4") == (12+3-1)*4
    assert lang.parse("(12+3-1)*(32*-2)") == (12+3-1)*(32*-2)
    assert lang.parse("(12+3-1+55*23*45)/(3*-2)") == (12+3-1+55*23*45)//(3*-2)

def test_simple_parse_ast():
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

def test_parse_errors():
    lang = ExprLang()
    
    # Missing token
    with pytest.raises(ParsionParseError):
        lang.parse("(12+3")
    
    # Extra token
    with pytest.raises(ParsionParseError):
        lang.parse("(12+3))")


def test_lexing_errors():
    lang = ExprLang()
    
    # Missing token
    with pytest.raises(ParsionLexerError):
        lang.parse("(12+3x")
