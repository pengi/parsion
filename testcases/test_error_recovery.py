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
        (')',        r'([\)])',                    lambda x: None),
        (';',        r'(;)',                       lambda x: None)
    ]
    GRAMMAR_RULES = [
        ('entry',       'entry',        'stmts'),
        ('stmts_list',  'stmts',        'stmt _; stmts'),
        ('stmts_tail',  'stmts',        'stmt _;'),
        
        # proxy statement, to be able to isolate errors to top level
        (None,          'stmt',         'expr'),
        ('error_stmt',  'stmt',         '$ERROR'),
        
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
    
    def error_stmt(self, error):
        return None
    
    def stmts_list(self, expr, list):
        return [expr] + list
    
    def stmts_tail(self, expr):
        return [expr]
    
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

def test_simple_parse():
    lang = ExprLang()
    assert lang.parse("(12+3)*4; 1+3; 43*4;") == [(12+3)*4, 1+3, 43*4]

@pytest.mark.skip(reason="Error handling not yet implemented")
def test_simple_error_stmt():
    """
    Test that error in one statement is isolated to that statement
    """
    lang = ExprLang()
    assert lang.parse("(12+3)*4; 3+; 43*4;") == [(12+3)*4, None, 43*4]
