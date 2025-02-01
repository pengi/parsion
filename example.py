from parsion import Parsion

parser = Parsion(
    [
        (None,          r'(\s+)',                     lambda x: None),

        ('STR',         r'("(?:[^"\\]|\\.)*")',       lambda x: x[1:-1]), # TODO: remove inner escapes
        ('FLOAT',       r'([0-9]+\.[0-9]*)',          lambda x: float(x)),
        ('INT',         r'([0-9]+|0x[0-9a-fA-F]+)',   lambda x: int(x,base=0)),

        ('FOR',         r'(for)(?:[^a-z0-9_]|$)',     lambda x: None),
        ('IN',          r'(in)(?:[^a-z0-9_]|$)',      lambda x: None),
        ('IF',          r'(if)(?:[^a-z0-9_]|$)',      lambda x: None),
        ('THEN',        r'(then)(?:[^a-z0-9_]|$)',    lambda x: None),
        ('ELSE',        r'(else)(?:[^a-z0-9_]|$)',    lambda x: None),

        ('NAME',        r'([a-zA-Z0-9_]+)',           lambda x: x),
        
        ('==',          r'(==)',                      lambda x: None),

        ('-',           r'(-)',                       lambda x: None),
        ('+',           r'(\+)',                      lambda x: None),
        ('*',           r'(\*)',                      lambda x: None),
        ('/',           r'(\/)',                      lambda x: None),

        (',',           r'(,)',                       lambda x: None),
        ('.',           r'(\.)',                      lambda x: None),
        ('=',           r'(=)',                       lambda x: None),
        ('(',           r'([\(])',                    lambda x: None),
        (')',           r'([\)])',                    lambda x: None),
        ('[',           r'(\[)',                      lambda x: None),
        (']',           r'(\])',                      lambda x: None),

        # Intended to not fail during lexing phase, but push invalid inputs
        # to parsing phase, with more useful error messages
        ('CHAR',        r'(.)',                       lambda x: x)
    ],
    [
        ('entry',       'entry',        'expr'),

        ('expr_eq',     'expr',         'expr1 _== expr1'),

        (None,          'expr',         'expr1'),
        
        ('expr_add',    'expr1',        'expr1 _+ expr2'),
        ('expr_sub',    'expr1',        'expr1 _- expr2'),
        
        (None,          'expr1',        'expr2'),
        
        ('expr_add',    'expr2',        'expr2 _* expr3'),
        ('expr_sub',    'expr2',        'expr2 _/ expr3'),
        
        (None,          'expr2',        'expr3'),
        
        ('expr_neg',    'expr3',        '_- expr4'),
        
        (None,          'expr3',        'expr4'),
        
        ('expr_int',    'expr4',        'INT'),
        ('expr_float',  'expr4',        'FLOAT'),
        ('expr_var',    'expr4',        'NAME'),
        ('expr_var',    'expr4',        'STRING'),
        
        (None,          'expr4',        '_( expr _)'),
    ]
)

parser.parse('(pelle + 32 * 4) / 7')
