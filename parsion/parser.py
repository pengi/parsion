from dataclasses import dataclass
from typing import Any, Callable, List, Optional, Set, Tuple, Dict, Iterable
from .exceptions import ParsionParseError, ParsionInternalError
from .lex import ParsionToken


@dataclass
class ParsionStackItem:
    value: Any
    state: int
    start: int
    end: int


@dataclass
class ParsionQueueItem:
    sym: str
    value: Any
    start: int
    end: int


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

    def _parse(self,
               input: Iterable[ParsionToken],
               reduce_handler: Callable[[
                   Optional[str],
                   str,
                   List[bool],
                   List[Any]
               ], Any],
               error_handler: Callable[[
                   str, str, int, int, int, Set[str]], Any]
               ) -> Any:
        tokens: List[ParsionQueueItem] = [
            ParsionQueueItem(tok.name, tok.value, tok.start, tok.end)
            for tok
            in input
        ]
        stack: List[ParsionStackItem] = [ParsionStackItem('START', 0, 0, 0)]

        while len(tokens) > 0:
            cur_tok = tokens[0]
            cur_state = stack[-1]
            if cur_tok.sym not in self.parse_table[cur_state.state]:
                # Unexpected token, do error recovery
                expect_toks = set(self.parse_table[cur_state.state].keys())
                try:
                    # First, pop stack until error handler
                    error_stack: List[ParsionStackItem] = []
                    while stack[-1].state not in self.error_handlers:
                        error_stack.append(stack.pop())

                    state_error_handlers = self.error_handlers[stack[-1].state]

                    error_tokens = []
                    while tokens[0].sym not in state_error_handlers:
                        error_tokens.append(tokens.pop(0))

                    # Call error handler, mimic a reduce operation
                    error_gen, handler_func = \
                        state_error_handlers[tokens[0].sym]

                    error_start = error_stack[-1].start
                    error_pos = error_tokens[0].start
                    error_end = error_tokens[-1].end

                    value = error_handler(
                        handler_func,
                        error_gen,
                        error_start,
                        error_pos,
                        error_end,
                        expect_toks
                    )
                    tokens.insert(0, ParsionQueueItem(
                        error_gen,
                        value,
                        error_start,
                        error_end
                    ))
                except IndexError:
                    expect_str = ",".join(expect_toks)
                    raise ParsionParseError(
                        f'Unexpected {cur_tok.sym}, expected {expect_str}',
                        cur_state.start,
                        cur_tok.start,
                        cur_tok.end,
                        expect_toks
                    )
            else:
                op, id = self.parse_table[cur_state.state][cur_tok.sym]
                if op == 's':
                    # shift
                    tokens.pop(0)
                    stack.append(ParsionStackItem(
                        cur_tok.value,
                        id,
                        cur_tok.start,
                        cur_tok.end
                    ))
                elif op == 'r':
                    # reduce
                    gen, goal, accepts = self.parse_grammar[id]
                    reduce_start = stack[-len(accepts)].start
                    reduce_end = stack[-1].end
                    tokens.insert(0, ParsionQueueItem(
                        gen,
                        reduce_handler(
                            goal,
                            gen,
                            accepts,
                            [p.value for p in stack[-len(accepts):]]
                        ),
                        reduce_start,
                        reduce_end
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
        return stack[1].value

    def parse(self,
              input: Iterable[ParsionToken],
              handlerobj: object) -> Any:

        def _call_reduce(
                goal: Optional[str],
                gen: str,
                accepts: List[bool],
                parts: List[Any]) -> Any:
            args = [p for a, p in zip(accepts, parts) if a]

            if goal is None:
                assert len(args) == 1
                return args[0]
            else:
                return getattr(handlerobj, goal)(*args)

        def _call_error_handler(
                handler: str,
                gen: str,
                error_start: int,
                error_pos: int,
                error_end: int,
                expect: Set[str]) -> Any:
            return getattr(handlerobj, handler)(
                gen,
                error_start,
                error_pos,
                error_end,
                expect
            )

        return self._parse(
            input,
            _call_reduce,
            _call_error_handler)
