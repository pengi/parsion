from typing import Any, Callable, List, Optional, Tuple, Dict, Iterable
from .exceptions import ParsionParseError, ParsionInternalError
from .lex import ParsionToken


class ParsionASTNode:
    def __str__(self) -> str:  # pragma: no cover
        return '<ParsionASTNode>'


class ParsionASTRule(ParsionASTNode):
    goal: str
    gen: str
    parts: List[Any]

    def __init__(self,
                 goal: str,
                 gen: str,
                 parts: List[Any]):
        self.goal = goal
        self.gen = gen
        self.parts = parts

    def __str__(self) -> str:  # pragma: no cover
        result = [f'{self.gen} - {self.goal}']
        for part in self.parts:
            result.extend([
                "   " + line
                for line
                in str(part).split("\n")
            ])
        return "\n".join(result)

    def _tupleize(self) -> Tuple[str, str, List[Any]]:
        return (self.goal, self.gen, self.parts)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, ParsionASTRule):
            return self._tupleize() == other._tupleize()
        else:
            return False


# TODO: Define error handlers before making error handler tests
class ParsionASTError(ParsionASTNode):  # pragma: no cover
    handler: str
    gen: str
    error_stack: List[Tuple[str, Any]]
    error_tokens: List[Tuple[str, Any]]

    def __init__(self,
                 handler: str,
                 gen: str,
                 error_stack: List[Tuple[str, Any]],
                 error_tokens: List[Tuple[str, Any]]):
        self.handler = handler
        self.gen = gen
        self.error_stack = error_stack
        self.error_tokens = error_tokens

    def __str__(self) -> str:
        result = [f'{self.gen} - {self.handler}', 'stack:']
        for st in self.error_stack:
            result.extend([
                "   " + line
                for line
                in str(st[0]).split("\n")
            ])
        return "\n".join(result)

    def _tupleize(self) -> Tuple[
        str,
        str,
        List[Tuple[str, Any]],
        List[Tuple[str, Any]]
    ]:
        return (self.handler, self.gen, self.error_stack, self.error_tokens)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, ParsionASTError):
            return self._tupleize() == other._tupleize()
        else:
            return False


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
                   str,
                   str,
                   List[Tuple[str, Any]],
                   List[Tuple[str, Any]]
               ], Any]
               ) -> Any:
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

                    state_error_handlers = self.error_handlers[stack[-1][1]]

                    error_tokens = []
                    while tokens[0][0] not in state_error_handlers:
                        error_tokens.append(tokens.pop(0))

                    # Call error handler, mimic a reduce operation
                    error_gen, handler_func = \
                        state_error_handlers[tokens[0][0]]

                    value = error_handler(
                        handler_func,
                        error_gen,
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
                        reduce_handler(
                            goal,
                            gen,
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

    def parse(self,
              input: Iterable[ParsionToken],
              handlerobj: object) -> Any:

        def _call_reduce(
                goal: Optional[str],
                gen: str,
                accepts: List[bool],
                parts: List[Any]) -> Any:
            args = [p[0] for a, p in zip(accepts, parts) if a]

            if goal is None:
                assert len(args) == 1
                return args[0]
            else:
                return getattr(handlerobj, goal)(*args)

        def _call_error_handler(
                handler: str,
                gen: str,
                error_stack: List[Tuple[str, Any]],
                error_tokens: List[Tuple[str, Any]]) -> Any:
            return getattr(handlerobj, handler)(error_stack, error_tokens)

        return self._parse(
            input,
            _call_reduce,
            _call_error_handler)

    def parse_ast(self, input: Iterable[ParsionToken]) -> ParsionASTNode:
        def _call_reduce(
                goal: Optional[str],
                gen: str,
                accepts: List[bool],
                parts: List[Any]) -> Any:
            args = [p[0] for a, p in zip(accepts, parts) if a]

            if goal is None:
                assert len(args) == 1
                return args[0]
            else:
                return ParsionASTRule(goal, gen.rstrip('0123456789'), args)

        result = self._parse(
            input,
            _call_reduce,
            ParsionASTError
        )
        assert isinstance(result, ParsionASTNode)
        return result
