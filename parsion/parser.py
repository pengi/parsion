from typing import Any, List, Optional, Tuple, Dict, Iterable
from .exceptions import ParsionParseError, ParsionInternalError
from .lex import ParsionToken


class ParsionParser:
    parse_grammar: List[Tuple[str, Optional[str], List[bool]]]
    parse_table: List[Dict[str, Tuple[str, int]]]
    error_handlers: Dict[int, Dict[str, Tuple[str, str]]]

    def __init__(self,
                 parse_grammar: List[Tuple[str, Optional[str], List[bool]]],
                 parse_table: List[Dict[str, Tuple[str, int]]],
                 error_handlers: Dict[int, Dict[str, Tuple[str, str]]]
                 ):
        self.parse_grammar = parse_grammar
        self.parse_table = parse_table
        self.error_handlers = error_handlers

    def _call_reduce(self,
                     obj: object,
                     goal: Optional[str],
                     accepts: List[bool],
                     parts: List[Any]) -> Any:
        args = [p[0] for a, p in zip(accepts, parts) if a]

        if goal is None:
            assert len(args) == 1
            return args[0]
        else:
            return getattr(obj, goal)(*args)

    def _call_error_handler(self,
                            obj: object,
                            handler: str,
                            error_stack: List[Tuple[str, Any]],
                            error_tokens: List[Tuple[str, Any]]) -> Any:
        return getattr(obj, handler)(error_stack, error_tokens)

    def parse(self,
              input: Iterable[ParsionToken],
              handlerobj: object) -> Any:
        tokens: List[Tuple[str, Any]] = [
            (tok.name, tok.value)
            for tok
            in input
        ]
        stack: List[Tuple[str, Any]] = [('START', 0)]

        while len(tokens) > 0:
            tok_name, tok_value = tokens[0]
            cur_state = stack[-1][1]
            if tok_name not in self.parse_table[cur_state]:
                # Unexpected token, do error recovery
                try:
                    # First, pop stack until error handler
                    error_stack = []
                    while stack[-1][1] not in self.error_handlers:
                        error_stack.append(stack.pop())

                    error_handlers = self.error_handlers[stack[-1][1]]

                    error_tokens = []
                    while tokens[0][0] not in error_handlers:
                        error_tokens.append(tokens.pop(0))

                    # Call error handler, mimic a reduce operation
                    error_gen, error_handler = error_handlers[tokens[0][0]]
                    value = self._call_error_handler(
                        handlerobj,
                        error_handler,
                        error_stack,
                        error_tokens
                    )
                    tokens.insert(0, (error_gen, value))
                except IndexError:
                    expect_toks = ",".join(self.parse_table[cur_state].keys())
                    raise ParsionParseError(
                        f'Unexpected {tok_name}, expected {expect_toks}')
            else:
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
                        self._call_reduce(
                            handlerobj,
                            goal,
                            accepts,
                            stack[-len(accepts):]
                        )
                    ))
                    stack = stack[:-len(accepts)]
                else:
                    raise ParsionInternalError(
                        'Internal error: neigher shift nor reduce')

        # Stack contains three elements:
        #  0. ('START', ...) - bootstrap
        #  1. ('entry', ...) - excpeted result
        #  2. ('END', ...)   - terminination
        # Therefore, pick out entry value and return
        return stack[1][0]
