from .exceptions import ParsionSelfCheckError

def _self_check_handlers(par):
    """
    Startup check for handlers
    
    Check that all handlers are implemented with correct amount of arguments
    """
    # Keep inspect in this functions, so it can easily be disabled
    import inspect
    
    # Check all reduce handlers are accessable
    for i, (gen, goal, accepts) in enumerate(par.parse_grammar):
        arg_count = sum(1 for a in accepts if a)
        if goal is None:
            if arg_count != 1:
                raise ParsionSelfCheckError(f'No handler for rule #{i} (gen: {gen}), but {arg_count} arguments (expects 1)')
        else:
            try:
                handler = inspect.signature(getattr(par, goal))
                
                # Count minimum and maximum number of arguments
                param_count_min = 0
                param_count_max = 0
                for p in handler.parameters.values():
                    if p.kind in {p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD}:
                        # Positional attribute, with or without default value
                        param_count_max += 1
                        if p.default == p.empty:
                            param_count_min += 1
                    if p.kind in {p.VAR_POSITIONAL}:
                        # Variable attribute: *args
                        param_count_max = None
                        # No more paramters can come afterwards
                        break

                if arg_count < param_count_min or (param_count_max is not None and param_count_max < arg_count):
                    if param_count_min == param_count_max:
                        count_str = f'{param_count_min}'
                    elif param_count_max is None:
                        count_str = f'>={param_count_min}'
                    else:
                        count_str = f'between {param_count_min} and {param_count_max}'
                    raise ParsionSelfCheckError(f"Invalid paramter count for {goal}, expected {arg_count}, has {count_str}")
            except AttributeError:
                raise ParsionSelfCheckError(f"No handler defined for {goal}")


def run_self_check(par):
    _self_check_handlers(par)
