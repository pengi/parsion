import pytest
from parsion import *

class BaseLang(Parsion):
    def __init__(self, self_check=True):
        super().__init__([
            (None,       r'(\s+)',                     lambda x: None),
            ('INT',      r'([0-9]+|0x[0-9a-fA-F]+)',   lambda x: int(x,base=0))
        ],[
            ('entry',         'entry',        'expr'),
            ('expr_int',      'expr',         'INT'),
            ('expr_int_expr', 'expr',         'INT expr')
        ], self_check=self_check)

def test_working():
    """
    Self check of base language fixture
    """
    class TestLang(BaseLang):
        def expr_int(self, v):
            return v
        def expr_int_expr(self, v, e):
            return v+e
    
    lang = TestLang()
    assert lang.parse("1 3 4 5") == 1+3+4+5

def test_extra_arg():
    class TestLang(BaseLang):
        def expr_int(self, v):
            return v
        def expr_int_expr(self, v, e, extra):
            return v+e
    
    with pytest.raises(ParsionSelfCheckError):
        lang = TestLang()
        
def test_missing_arg():
    class TestLang(BaseLang):
        def expr_int(self, v):
            return v
        def expr_int_expr(self, v):
            return v
    
    with pytest.raises(ParsionSelfCheckError):
        lang = TestLang()
        
def test_default_value_expected():
    class TestLang(BaseLang):
        def expr_int(self, v):
            return v
        def expr_int_expr(self, v, e=12):
            return v+e
    
    lang = TestLang()
    assert lang.parse("1 3 4 5") == 1+3+4+5
        
def test_default_value_extra():
    class TestLang(BaseLang):
        def expr_int(self, v):
            return v
        def expr_int_expr(self, v, e, extra=12):
            return v+e
    
    lang = TestLang()
    assert lang.parse("1 3 4 5") == 1+3+4+5

def test_variable_args():
    class TestLang(BaseLang):
        def expr_int(self, v):
            return v
        def expr_int_expr(self, *args):
            return sum(args)

    lang = TestLang()
    assert lang.parse("1 3 4 5") == 1+3+4+5


def test_missing_func():
    class TestLang(BaseLang):
        def expr_int(self, v):
            return v

    with pytest.raises(ParsionSelfCheckError):
        lang = TestLang()

def test_self_check_disabled():
    class TestLang(BaseLang):
        def __init__(self):
            super().__init__(self_check=False)

        def expr_int(self, v):
            return v

    # Parser generation should work
    lang = TestLang()
    
    # Missing handler not triggered, should work
    assert lang.parse('12') == 12
    
    # Missing handler is triggered
    with pytest.raises(AttributeError):
        lang.parse('12 13')
