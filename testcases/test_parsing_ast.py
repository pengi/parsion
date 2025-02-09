from parsion import Parsion, ParsionASTRule


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
        ('errstuff',    'entry',        '$ERROR'),
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
    SELF_CHECK = False  # Just generating AST doesn't require handlers


def test_parse_ast() -> None:
    lang = ExprLang()
    actual_ast = lang.parse_ast("(12+3-1)*4")
    expect_ast = ParsionASTRule('entry', 'entry', [
        ParsionASTRule('expr_mult', 'expr', [
            ParsionASTRule('expr_sub', 'expr', [
                ParsionASTRule('expr_add', 'expr', [
                    ParsionASTRule('expr_int', 'expr', [
                        12
                    ]),
                    ParsionASTRule('expr_int', 'expr', [
                        3
                    ])
                ]),
                ParsionASTRule('expr_int', 'expr', [
                    1
                ])
            ]),
            ParsionASTRule('expr_int', 'expr', [
                4
            ])
        ])
    ])

    assert actual_ast == expect_ast


def test_parse_ast_node() -> None:
    assert ParsionASTRule('a', 'b', ['x']) != 1234
