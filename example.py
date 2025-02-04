import parsion
import re


class ExprLang(parsion.Parsion):
    SELF_CHECK = True

    LEXER_RULES = [
        (None,       r'(\s+)', lambda x: None),

        ('STR',      r'("(?:[^"\\]|\\.)*")',
            lambda x: re.sub(r'\\(.)', r'\1', x[1:-1])),
        ('FLOAT',    r'([0-9]+\.[0-9]*)', lambda x: float(x)),
        ('INT',      r'([0-9]+|0x[0-9a-fA-F]+)', lambda x: int(x, base=0)),

        ('FOR',      r'(for)(?:[^a-z0-9_]|$)', lambda x: None),
        ('IN',       r'(in)(?:[^a-z0-9_]|$)', lambda x: None),
        ('IF',       r'(if)(?:[^a-z0-9_]|$)', lambda x: None),
        ('THEN',     r'(then)(?:[^a-z0-9_]|$)', lambda x: None),
        ('ELSE',     r'(else)(?:[^a-z0-9_]|$)', lambda x: None),

        ('NAME',     r'([a-zA-Z0-9_]+)', lambda x: x),

        ('==',       r'(==)', lambda x: None),

        ('-',        r'(-)', lambda x: None),
        ('+',        r'(\+)', lambda x: None),
        ('*',        r'(\*)', lambda x: None),
        ('/',        r'(\/)', lambda x: None),

        (',',        r'(,)', lambda x: None),
        ('.',        r'(\.)', lambda x: None),
        ('=',        r'(=)', lambda x: None),
        ('(',        r'([\(])', lambda x: None),
        (')',        r'([\)])', lambda x: None),
        ('[',        r'(\[)', lambda x: None),
        (']',        r'(\])', lambda x: None),

        # Intended to not fail during lexing phase, but push invalid inputs
        # to parsing phase, with more useful error messages
        ('CHAR',        r'(.)', lambda x: x)
    ]

    GRAMMAR_RULES = [
        ('entry',       'entry',        'expr'),

        ('expr_eq',     'expr',         'expr1 _== expr1'),

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
        ('expr_float',  'expr4',        'FLOAT'),
        ('expr_var',    'expr4',        'NAME'),
        ('expr_str',    'expr4',        'STR'),

        (None,          'expr4',        '_( expr _)'),
    ]

    def expr_eq(self, lhs, rhs):
        return lhs == rhs

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

    def expr_float(self, v):
        return v

    def expr_var(self, v):
        return v

    def expr_str(self, v):
        return v


if __name__ == '__main__':
    # Generate the parser
    parser = ExprLang()

    # Print the parsing tables
    # This line uses "tabulate" library
    # parser.print()

    # Parse a string
    print(parser.parse('(12 + 32 * 4) / 7 + 13'))
