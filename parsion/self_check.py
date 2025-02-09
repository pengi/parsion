from inspect import Signature
from typing import Optional
from .exceptions import ParsionSelfCheckError
from .core import ParsionBase


def _self_check_handlers(par: ParsionBase) -> None:
    """
    Startup check for handlers

    Check that all handlers are implemented with correct amount of arguments
    """
    # Keep inspect in this functions, so it can easily be disabled
    import inspect

    expected_funcs = {}

    # Check all reduce handlers are accessable
    for i, (gen, goal, accepts) in enumerate(par.parser.parse_grammar):
        argc = sum(1 for a in accepts if a)
        if goal is None:
            if argc != 1:
                raise ParsionSelfCheckError(
                    f'No handler for rule #{i} (gen: {gen}), but {argc} args'
                )
        else:
            expected_funcs[goal] = argc

    # Check all error handlers are implemented
    for error_handlers in par.parser.error_handlers.values():
        for gen, handler_name in error_handlers.values():
            expected_funcs[handler_name] = 5  # gen, start, pos, end, expect

    # Check all reduce handlers are accessable
    for goal, arg_count in expected_funcs.items():
        try:
            handler: Signature = inspect.signature(getattr(par, goal))

            # Count minimum and maximum number of arguments
            param_count_min: int = 0
            param_count_max: Optional[int] = 0
            for p in handler.parameters.values():
                if p.kind in {p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD}:
                    # Positional attribute, with or without default value
                    if param_count_max is not None:
                        param_count_max += 1
                    if p.default == p.empty:
                        param_count_min += 1
                if p.kind in {p.VAR_POSITIONAL}:
                    # Variable attribute: *args
                    param_count_max = None

            if arg_count < param_count_min or (
                param_count_max is not None and param_count_max < arg_count
            ):
                if param_count_min == param_count_max:
                    count_str = f'{param_count_min}'
                elif param_count_max is None:
                    count_str = f'>={param_count_min}'
                else:
                    count_str = \
                        f'between {param_count_min} and {param_count_max}'
                raise ParsionSelfCheckError(
                    f"{goal}: expected {arg_count} args, has {count_str}")
        except AttributeError:
            raise ParsionSelfCheckError(f"No handler defined for {goal}")


def run_self_check(par: ParsionBase) -> None:
    _self_check_handlers(par)
