Parsion - A simple LR(1) parser
===============================

Parsion is intended to be a simple drop-in parser generator, lexer and parser
for grammars in python.

It's main intention is to make it possible to load and create a grammar for
simple expression parsers without using code generation.

## Installation

parsion is available on [pypi](https://pypi.org/project/parsion/)

To install:

```sh
pip install parsion
```

## Usage

To define a language for parsing, three components are required:

  - Lexer rules – Specify how to tokenize the input by splitting it into
    meaningful units (tokens).
  - Grammar – Defined as Python objects, similar in concept to
    [Backus-Naur Form (BNF)](https://en.wikipedia.org/wiki/Backus%E2%80%93Naur_form).
  - Reducers/Handlers – Functions that handle reductions, with one handler per
    grammar rule.

A language is defined as a Python class containing these rules.

The lexer rules are implemented as a series of regular expressions that consume
the input string from the beginning. The first regex that matches the start of
the string determines the next token, which is then extracted from the input
before the process repeats. Each lexer rule also contains a method to
postprocess the input. For example convert an integer to `int`, or unpack a
quoted string.

The parser rules is defined as a list of rules, where each rule has three parts:
 - A handler to be called when the rule is reduced
 - The symbol that will be the result of the rule
 - A sequence of symbols that is the input to the rule

The sequence of symbols is a space seperated string, for readability. If a
symbol starts with `_`, the `_` is dropped, and the value of the corresponding
token will
not be passed to the handler.

A rule specifying the handler `None` must have exactly one symbol without `_`,
and the input value will be passed directly as result. It is useful for defining
rules to set operator precedence.

Parsing begins from the grammar rule that produces the `entry` token.

To parse an input string, call the `parse(input)` method. It will apply the
defined handlers and return the result of the entry node.

If an error occurs during parsing, an exception is raised.

## Example

For a bigger example, see: [example.py](example.py)

```py
from parsion import Parsion

class ExprLang(Parsion):
    LEXER_RULES = [
        (None,       r'(\s+)',                   lambda x: None),
        ('INT',      r'([0-9]+|0x[0-9a-fA-F]+)', lambda x: int(x, base=0)),

        ('+',        r'(\+)',                    lambda x: None),
        ('-',        r'(-)',                     lambda x: None),
        ('*',        r'(\*)',                    lambda x: None),
        ('/',        r'(\/)',                    lambda x: None),

        ('(',        r'([\(])',                  lambda x: None),
        (')',        r'([\)])',                  lambda x: None)
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

if __name__ == '__main__':
    # Generate the parser, and parsing tables
    expr_lang = ExprLang()

    # Run the parser
    print( expr_lang.parse('12 * (3 + 7)' )) # prints "120"

    # Run the parser again. Same table generation is reused.
    print( expr_lang.parse('2 + -4 * -10' )) # prints "42"
```

## Error recovery

To isolate error handling, an error rule can be created.

Given the grammar:

```py
from parsion import Parsion


class ExprErrorLang(Parsion):
    LEXER_RULES = [
        (None,       r'(\s+)', lambda x: None),
        ('INT',      r'([0-9]+|0x[0-9a-fA-F]+)', lambda x: int(x, base=0)),

        ('+',        r'(\+)', lambda x: None),
        ('-',        r'(-)', lambda x: None),
        ('*',        r'(\*)', lambda x: None),
        ('/',        r'(\/)', lambda x: None),

        ('(',        r'([\(])', lambda x: None),
        (')',        r'([\)])', lambda x: None),
        (';',        r'(;)', lambda x: None)
    ]
    GRAMMAR_RULES = [
        ('entry',       'entry',        'stmts'),
        ('stmts_list',  'stmts',        'stmt _; stmts'),
        ('stmts_tail',  'stmts',        'stmt'),

        # proxy statement, to be able to isolate errors to top level
        (None,          'stmt',         'expr'),
        ('stmt_error',  'stmt',         '$ERROR'),

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

    def stmt_error(self, gen, start, pos, end, expect):
        return None

```

A valid input would then be
```
1 + 3 + 5 + 7; 12*13*14; 313-13
```

Resulting in a list:
```
[16, 2184, 300]
```

The language contains three separate statements. To isolate errors within a
single statement, the special rule generated by `$ERROR` will be used.

Upon a parse error, all tokens will be accumulated up until a possible token
following the closest `$ERROR` rule. Then the error handler will be called,
to return a placeholder for the generation, in this case `stmt`, and parsing
will continue.

If no error handler are defined, or error happens outside of defined error
handlers, an exception will be raised instead, and parsing will fail.

Given the above grammar and error handler, the following input:


An input with an error in the middle stmt:
```
1 + 3 + 5 + 7; 12+*13*14; 313-13
```

Will then result in:
```
[16, None, 300]
```

`None` is there the result of the error handler.


### Default Error isolation

Without specifying an error handler, an exception will be raised of type
`ParsionParseError`.

The exception contains the field `pos` containing the location in the input
string of the erroneous token. It also contains `start` and `end`, which
includes the scope of where the error occurs.

It is possible in the example above to instead specify the error handler
`default_error` instead of `stmt_error`. In that case, an exception will still
be raised, but the `start` and `end` fields will better contain the erroneous
parse tree.

## Precalculated tables

For bigger languages, it may be motivated to actually precalculate the parse
tables upon packaging. For that purpose, there is a class `ParsionStatic` which
doesn't invoke the parser generation, but takes the raw parse tables as input.

The interface for that method is to be defined and documented. Open an issue if
interested in that feature.
