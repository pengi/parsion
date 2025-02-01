from parsion.lex import ParsionLexer

class Parsion:
    def __init__(self, lex_rules, grammar_rules):
        self.lex = ParsionLexer(lex_rules)
        
    def parse(self, input):
        tokens = self.lex.tokenize(input)
        
        for tok in tokens:
            print(tok)
