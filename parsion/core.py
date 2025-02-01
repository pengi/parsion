from parsion.lex import ParsionLexer
from parsion.parser import ParsionFSM

from pprint import pprint

class ParsionException(Exception):
    pass

class Parsion:
    def __init__(self, lex_rules, grammar_rules):
        self.lex = ParsionLexer(lex_rules)
        self.parse_grammar, self.parse_table = ParsionFSM(grammar_rules).export()
    
    def _call_reduce(self, goal, accepts, parts):
        args = [p[0] for a, p in zip(accepts, parts) if a]
        
        if goal is None:
            assert len(args) == 1
            return args[0]
        else:
            return getattr(self, goal)(*args)
    
    def parse(self, input):
        tokens = [(tok.name, tok.value) for tok in self.lex.tokenize(input)]
        stack = [('START', 0)]
        
        while len(tokens) > 0:
            tok_name, tok_value = tokens[0]
            cur_state = stack[-1][1]
            op, id = self.parse_table[cur_state][tok_name]
            if op == 's':
                # shift
                tokens.pop(0)
                stack.append((tok_value, id))
            elif op == 'r':
                # reduce
                gen, goal, accepts = self.parse_grammar[id]
                tokens.insert(0, (
                    gen,
                    self._call_reduce(goal, accepts, stack[-len(accepts):])
                ))
                stack = stack[:-len(accepts)]
            else:
                raise ParsionException('Internal error: neigher shift nor reduce')
        
        # Stack contains three elements:
        #  0. ('START', ...) - bootstrap
        #  1. ('entry', ...) - excpeted result
        #  2. ('END', ...)   - terminination
        # Therefore, pick out entry value and return
        return stack[1][0]

    def print(self):
        from tabulate import tabulate
        
        def _print_header(header):
            print("")
            print(f"{header}")
        
        _print_header("Lexer")
        print(tabulate(
            [
                (name, regexp.pattern)
                for name, regexp, handler in self.lex.rules   
            ],
            tablefmt='simple_outline'
        ))
        
        _print_header("FSM grammar")
        print(tabulate(
            self.parse_grammar,
            headers=('generate', 'goal', 'parts'),
            tablefmt='simple_outline',
            showindex='always'
        ))
        _print_header("FSM states")

        print(tabulate(
            [
                {
                    k: " ".join(str(p) if p is not None else '-' for p in v)
                    for k,v in st.items()
                }
                for st in self.parse_table
            ],
            headers='keys',
            tablefmt='simple_outline',
            showindex='always'
        ))

    def entry(self, v):
        return v
