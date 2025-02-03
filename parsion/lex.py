
import re
from .exceptions import ParsionException

class ParsionLexerError(ParsionException):
    def __init__(self, message, input, pos):
        super().__init__(message)
        self.input = input
        self.pos = pos
    
    def __str__(self):
        return f'{self.args[0]} (pos {self.pos} in {self.input!r})'

class ParsionToken:
    def __init__(self, name, value, start, end):
        self.name = name
        self.value = value
        self.start = start
        self.end = end
    
    def __str__(self):
        if self.value is None:
            return f'[@{self.start:>3} {self.name}]'
        else:
            return f'[@{self.start:>3} {self.name}: {self.value!r}]'
    
    def ignore(self):
        return self.name is None

class ParsionEndToken(ParsionToken):
    def __init__(self, pos):
        super().__init__('$END', '$END', pos, pos)

class ParsionLexer:
    def __init__(self, rules):
        self.rules = [
            (name, re.compile(regexp), handler)
            for (name, regexp, handler)
            in rules
        ]

    def next_token(self, input, pos):
        for name, regexp, handler in self.rules:
            m = regexp.match(input, pos)
            if m is not None:
                return ParsionToken(name, handler(m.group(1)), m.start(1), m.end(1))
        return None
    
    def tokenize(self, input):
        pos = 0
        while pos < len(input):
            token = self.next_token(input, pos)
            if token is None:
                raise ParsionLexerError('Invalid input', input, pos)
            pos = token.end
            if not token.ignore():
                yield token
        yield ParsionEndToken(pos)

    def get_token_set(self):
        return {rule[0] for rule in self.rules}.union({'END'})
