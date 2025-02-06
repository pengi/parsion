from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Set, Tuple
from .exceptions import ParsionGeneratorError


def _noset(obj: Any) -> Any:
    """
    Remove sets from obj, only for doctests

    It looses the use case of doctests, but when an object returns a set, the
    order is random and can't be tested otherwise

    >>> _noset(12)
    12

    >>> _noset({1, 4, 3})
    [1, 3, 4]

    >>> _noset((4, 3, {4, 2}))
    (4, 3, [2, 4])

    >>> _noset([1, 4, {1, 3}, 3])
    [1, 4, [1, 3], 3]
    """
    if isinstance(obj, set):
        return sorted(_noset(x) for x in obj)
    elif isinstance(obj, tuple):
        return tuple(_noset(x) for x in obj)
    elif isinstance(obj, list):
        return [_noset(x) for x in obj]
    else:
        return obj


class ParsionFSMMergeError(Exception):
    pass


class ParsionFSMGrammarRule:
    id: int
    name: Optional[str]
    gen: str
    parts: List[str]
    attrtokens: List[bool]
    _hash: int

    def __init__(self, id: int, name: Optional[str], gen: str, rulestr: str):
        self.id = id
        self.name = name
        self.gen = gen

        parts = rulestr.split(' ')
        self.attrtokens = [part[0] != '_' for part in parts]
        self.parts = [part[1:] if part[0] == '_' else part for part in parts]

        # This class will never change value. Precalculate hash
        self._hash = hash((
            type(self).__name__,
            self.gen,
            self.name,
            sum(hash(t) for t in self.attrtokens)
        ))

    def get(self, idx: int, default: Optional[str] = None) -> Optional[str]:
        if idx < len(self.parts):
            return self.parts[idx]
        else:
            return default

    def export(self) -> Tuple[str, Optional[str], List[bool]]:
        return (self.gen, self.name, self.attrtokens)

    def _tupleize(self) -> Tuple[str, str, List[str], List[bool]]:
        """
        Get a tuple of all relevant parameters, for usage in __eq__ and __lt__

        >>> ParsionFSMGrammarRule(12, 'name', 'gen', 'lhs _op rhs')._tupleize()
        ('name', 'gen', ['lhs', 'op', 'rhs'], [True, False, True])
        """
        return (self.name or '', self.gen, self.parts, self.attrtokens)

    def __hash__(self) -> int:
        return self._hash

    def __lt__(self, other: object) -> bool:
        assert isinstance(other, ParsionFSMGrammarRule)
        return self._tupleize() < other._tupleize()

    def __eq__(self, other: object) -> bool:
        assert isinstance(other, ParsionFSMGrammarRule)
        return self._tupleize() == other._tupleize()

    def __str__(self) -> str:  # pragma: no cover
        name = f'{self.name}:' if self.name is not None else ''
        return f'{name:<12} {self.gen:<10} = {" ".join(self.parts)}'


class ParsionFSMItem:
    rule: ParsionFSMGrammarRule
    pos: int
    follow: Set[str]
    _hash: int

    def __init__(self,
                 rule: ParsionFSMGrammarRule,
                 follow: Set[str],
                 pos: int = 0):
        self.rule = rule
        self.pos = pos
        self.follow = set(follow)

        # This class will never change value. Precalculate hash
        self._hash = hash((
            type(self).__name__,
            self.rule,
            self.pos,
            sum(hash(x) for x in self.follow)
        ))

    def __str__(self) -> str:  # pragma: no cover
        name = f'{self.rule.name}:' if self.rule.name is not None else ''
        fmt_parts = [
            part if i != self.pos else f'>{part}<'
            for i, part in enumerate(self.rule.parts)
        ]
        return f'{name:<12} {self.rule.gen:<10} = {" ".join(fmt_parts)}'

    def _tupleize(self) -> Tuple[ParsionFSMGrammarRule, int, Set[str]]:
        """
        Get a tuple of all relevant parameters, for usage in __eq__ and __lt__
        """
        return (self.rule, self.pos, self.follow)

    def __hash__(self) -> int:
        return self._hash

    def __lt__(self, other: object) -> bool:
        assert isinstance(other, ParsionFSMItem)
        return self._tupleize() < other._tupleize()

    def __eq__(self, other: object) -> bool:
        assert isinstance(other, ParsionFSMItem)
        return self._tupleize() == other._tupleize()

    def get_next(self) -> Tuple[str, Set[str]]:
        """
        Get next two symbols from an item

        >>> rule = ParsionFSMGrammarRule(12, 'name', 'gen', 'lhs _op rhs')

        >>> ParsionFSMItem(rule, {'fa', 'fb'}, 0).get_next()
        ('lhs', {'op'})

        >>> ParsionFSMItem(rule, {'fa', 'fb'}, 1).get_next()
        ('op', {'rhs'})

        >>> _noset(ParsionFSMItem(rule, {'fa', 'fb'}, 2).get_next())
        ('rhs', ['fa', 'fb'])

        """
        n = self.rule.get(self.pos)
        assert n is not None  # Should be checked before calling
        f = self.rule.get(self.pos + 1)
        if f is None:
            fs = self.follow
        else:
            fs = {f}
        return n, fs

    def is_complete(self) -> bool:
        return self.rule.get(self.pos) is None

    def take(self, sym: str) -> Optional['ParsionFSMItem']:
        if self.rule.get(self.pos) == sym:
            return ParsionFSMItem(self.rule, self.follow, self.pos + 1)
        else:
            return None

    def is_mergable(self, other: 'ParsionFSMItem') -> bool:
        return self.rule == other.rule and self.pos == other.pos

    def merge(self, other: 'ParsionFSMItem') -> 'ParsionFSMItem':
        """
        Merge two identical items but with different follows, and return the
        combined

        If the two items are not compatible, throw an error

        >>> rule = ParsionFSMGrammarRule(12, 'name', 'gen', 'lhs _op rhs')
        >>> a = ParsionFSMItem(rule, {'fa', 'fb'}, 0)
        >>> b = ParsionFSMItem(rule, {'fb', 'fc'}, 0)
        >>> sorted(a.merge(b).follow)
        ['fa', 'fb', 'fc']

        >>> a0 = ParsionFSMItem(rule, {'fa', 'fb'}, 0)
        >>> b1 = ParsionFSMItem(rule, {'fb', 'fc'}, 1)
        >>> a0.merge(b1)
        Traceback (most recent call last):
        ...
        parsion.parsegen.ParsionFSMMergeError

        """
        if not self.is_mergable(other):
            raise ParsionFSMMergeError()
        return ParsionFSMItem(
            self.rule,
            self.follow.union(other.follow),
            self.pos
        )


class ParsionFSMState:
    items: Set[ParsionFSMItem]
    _hash: int

    def __init__(self, items: Iterable[ParsionFSMItem]):
        self.items = set(items)
        self._hash = sum(hash(it) for it in self.items)

    def next_syms(self) -> Set[str]:
        return set(
            it.get_next()[0]
            for it
            in self.items
            if not it.is_complete()
        )

    def reductions(self) -> List[ParsionFSMItem]:
        return [it for it in self.items if it.is_complete()]

    def take(self, sym: str) -> List[ParsionFSMItem]:
        result = []
        for item in self.items:
            next_item = item.take(sym)
            if next_item is not None:
                result.append(next_item)
        return result

    def __hash__(self) -> int:
        return self._hash

    def __str__(self) -> str:  # pragma: no cover
        return "\n".join(str(it) for it in self.items)

    def __eq__(self, other: object) -> bool:
        assert isinstance(other, ParsionFSMState)
        return self.items == other.items


class ParsionFSM:
    error_rules: Dict[str, str]
    grammar: List[ParsionFSMGrammarRule]

    state_ids: Dict[ParsionFSMState, int]
    states: List[ParsionFSMState]
    table: List[Dict[str, Tuple[str, int]]]

    sym_set: Set[str]

    firsts: Dict[str, Set[str]]
    error_handlers: Dict[int, Dict[str, Tuple[str, str]]]

    def __init__(self, grammar_rules: List[Tuple[Optional[str], str, str]]):
        # TODO: verify no error hanlders has None as name
        self.error_rules = {
            gen: name
            for (name, gen, rulestr)
            in grammar_rules
            if rulestr == '$ERROR' and name is not None
        }

        no_error_rules = [
            (name, gen, rulestr)
            for (name, gen, rulestr)
            in grammar_rules
            if rulestr != '$ERROR'
        ]

        self.grammar = [
            ParsionFSMGrammarRule(
                0,
                None,
                '$ENTRY',
                'entry _$END'
            )
        ] + [
            ParsionFSMGrammarRule(id + 1, name, gen, rulestr)
            for id, (name, gen, rulestr)
            in enumerate(no_error_rules)
        ]

        self._build_sym_set()
        self._calculate_firsts()
        self._build_states()

    def _get_rules_by_gen(self, gen: str) -> List[ParsionFSMGrammarRule]:
        return [rule for rule in self.grammar if rule.gen == gen]

    def _add_state(self, state: ParsionFSMState) -> int:
        state_id = self.state_ids.get(state)
        if state_id is None:
            state_id = len(self.states)
            self.state_ids[state] = state_id
            self.states.append(state)
            self.table.append({})
        return state_id

    def _build_sym_set(self) -> None:
        self.sym_set = set()
        for rule in self.grammar:
            self.sym_set.add(rule.gen)
            self.sym_set.update(rule.parts)

    def _calculate_firsts(self) -> None:
        rule_firsts = {rule.gen: rule.parts[0] for rule in self.grammar}
        self.firsts = {}
        for sym in self.sym_set:
            first_set = set()
            cur_sym = sym
            while cur_sym not in first_set:
                first_set.add(cur_sym)
                if cur_sym in rule_firsts:
                    cur_sym = rule_firsts[cur_sym]
            self.firsts[sym] = first_set

    def _get_first(self, syms: Set[str]) -> Set[str]:
        result = set()
        for sym in syms:
            result.update(self.firsts.get(sym, set()))
        return result

    def _get_closure(self,
                     items: Iterable[ParsionFSMItem]
                     ) -> List[ParsionFSMItem]:
        """
        Get a closure from list of items

        A closure is the input items, but also populated with new items from
        grammars, which generates the next symbol of the incoming list of items
        """

        all_items: Dict[Tuple[ParsionFSMGrammarRule, int], ParsionFSMItem] = {}
        queue: List[ParsionFSMItem] = []

        for item in items:
            queue.append(item)

        # Resolve all sub items
        while len(queue) > 0:
            it = queue.pop()

            key = (it.rule, it.pos)
            if key in all_items:
                old_it = all_items[key]
                new_it = old_it.merge(it)
                if new_it == old_it:
                    continue
                all_items[key] = new_it
            else:
                all_items[key] = it

            if not it.is_complete():
                sym, follow = it.get_next()
                follow_first = self._get_first(follow)
                for rule in self._get_rules_by_gen(sym):
                    queue.append(ParsionFSMItem(rule, follow_first))

        return sorted(all_items.values())

    def _build_states(self) -> None:
        self.states = []
        self.table = []
        self.state_ids = {}
        self.error_handlers = {}

        self._add_state(
            ParsionFSMState(self._get_closure([
                ParsionFSMItem(
                    self.grammar[0],
                    set()
                )
            ]))
        )

        state_queue = [0]
        processed = set()

        while len(state_queue) > 0:
            state_id = state_queue.pop(0)
            if state_id in processed:
                continue
            state = self.states[state_id]
            processed.add(state_id)

            # Check if state can have an error handler
            error_handlers: Dict[str, Tuple[str, str]] = {}
            for it in state.items:
                if it.rule.gen in self.error_rules:
                    for sym in it.follow:
                        if sym in error_handlers:
                            raise ParsionGeneratorError(
                                f'{it.rule.gen}: {sym} handler already defined'
                            )
                        error_handlers[sym] = (
                            it.rule.gen, self.error_rules[it.rule.gen])
            if error_handlers != {}:
                self.error_handlers[state_id] = error_handlers

            # Process rules
            for sym in state.next_syms():
                next_id = self._add_state(ParsionFSMState(
                    self._get_closure(state.take(sym))))
                state_queue.append(next_id)
                self.table[state_id][sym] = ('s', next_id)

            for it in state.reductions():
                for sym in it.follow:
                    if sym in self.table[state_id]:
                        raise ParsionGeneratorError("Shift/Reduce conflict")
                    self.table[state_id][sym] = ('r', it.rule.id)

    def export(self) -> Tuple[
        List[Tuple[str, Optional[str], List[bool]]],
        List[Dict[str, Tuple[str, int]]],
        Dict[int, Dict[str, Tuple[str, str]]]
    ]:
        return (
            [g.export() for g in self.grammar],
            self.table,
            self.error_handlers
        )
