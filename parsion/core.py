from parsion.lex import ParsionLexer
from parsion.parser import ParsionFSM
from .exceptions import ParsionInternalError

class ParsionParseError(Exception):
    pass

class Parsion:
    LEXER_RULES=[]
    GRAMMAR_RULES=[]
    SELF_CHECK=True
    
    def __init__(self, lex_rules=None, grammar_rules=None, self_check=True):
        self.lex = ParsionLexer(self.LEXER_RULES)
        self.parse_grammar, self.parse_table, self.error_handlers = ParsionFSM(self.GRAMMAR_RULES).export()
        if self.SELF_CHECK:
            self._self_check()

    def _self_check(self):
        from .self_check import run_self_check
        run_self_check(self)

    def _call_reduce(self, goal, accepts, parts):
        args = [p[0] for a, p in zip(accepts, parts) if a]

        if goal is None:
            assert len(args) == 1
            return args[0]
        else:
            return getattr(self, goal)(*args)
    
    def _call_error_handler(self, handler, error_stack, error_tokens):
        return getattr(self, handler)(error_stack, error_tokens)
    
    def parse(self, input):
        tokens = [(tok.name, tok.value) for tok in self.lex.tokenize(input)]
        stack = [('START', 0)]
        
        while len(tokens) > 0:
            tok_name, tok_value = tokens[0]
            cur_state = stack[-1][1]
            if tok_name not in self.parse_table[cur_state]:
                # Unexpected token, do error recovery
                
                # First, pop stack until error handler
                error_stack = []
                while len(stack) > 0 and stack[-1][1] not in self.error_handlers:
                    error_stack.append(stack.pop())
                
                # Second, fetch tokens until error is isolated
                if len(stack) == 0:
                    expect_toks = ",".join(self.parse_table[cur_state].keys())
                    raise ParsionParseError(f'Unexpected {tok_name}, expected {expect_toks}')
                
                state_error_handlers = self.error_handlers[stack[-1][1]]

                error_tokens = []
                while len(tokens) > 0 and tokens[0][0] not in state_error_handlers:
                    error_tokens.append(tokens.pop(0))
                
                if len(tokens) == 0:
                    expect_toks = ",".join(self.parse_table[cur_state].keys())
                    raise ParsionParseError(f'Unexpected {tok_name}, expected {expect_toks}')
                
                # Call error handler, mimic a reduce operation
                error_gen, error_handler = state_error_handlers[tokens[0][0]]
                value = self._call_error_handler(
                    error_handler,
                    error_stack,
                    error_tokens
                )
                tokens.insert(0, (error_gen, value))
                continue
                
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
                raise ParsionInternalError('Internal error: neigher shift nor reduce')
        
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
        return v#
