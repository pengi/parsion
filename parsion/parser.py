from pprint import pprint

class ParsionFSMMergeError(Exception):
    pass

class ParsionFSMGrammarRule:
    def __init__(self, id, name, gen, rulestr):
        self.id = id
        self.name = name
        self.gen = gen
        
        parts = rulestr.split(' ')
        self.attrtokens = [part[0] != '_' for part in parts]
        self.parts = [part[1:] if part[0] == '_' else part for part in parts]
    
    def get(self, idx, default=None):
        if idx < len(self.parts):
            return self.parts[idx]
        else:
            return default
    
    def export(self):
        return (self.gen, self.name, self.attrtokens)
    
    def _tupleize(self):
        """
        Get a tuple of all relevant parameters, for usage in __eq__ and __lt__
        """
        return (self.name or '', self.gen, self.parts, self.attrtokens)

    def __lt__(self, other):
        return self._tupleize() < other._tupleize()
    
    def __eq__(self, other):
        return self._tupleize() == other._tupleize()

    def __str__(self):
        name = f'{self.name}:' if self.name is not None else ''
        return f'{name:<12} {self.gen:<10} = {" ".join(self.parts)}'

class ParsionFSMItem:
    def __init__(self, rule, follow, pos=0):
        self.rule = rule
        self.pos = pos
        self.follow = follow

    def __str__(self):
        name = f'{self.rule.name}:' if self.rule.name is not None else ''
        fmt_parts = [
            part if i != self.pos else f'>{part}<'
            for i, part in enumerate(self.rule.parts)
        ]
        return f'{name:<12} {self.rule.gen:<10} = {" ".join(fmt_parts)}'

    def _tupleize(self):
        """
        Get a tuple of all relevant parameters, for usage in __eq__ and __lt__
        """
        return (self.rule, self.pos, self.follow)

    def __lt__(self, other):
        return self._tupleize() < other._tupleize()

    def __eq__(self, other):
        return self._tupleize() == other._tupleize()

    def get_next(self):
        n = self.rule.get(self.pos)
        if n is None:
            return None
        f = self.rule.get(self.pos+1)
        if f is None:
            f = self.follow
        else:
            f = {f}
        return n, f
    
    def is_complete(self):
        return self.rule.get(self.pos) is None
    
    def take(self, sym):
        if self.rule.get(self.pos) == sym:
            return ParsionFSMItem( self.rule, self.follow, self.pos+1 )
        else:
            return None

    def is_mergable(self, other):
        return self.rule == other.rule and self.pos == other.pos

    def merge(self, other):
        if not self.is_mergable(other):
            raise ParsionFSMMergeError()
        return ParsionFSMItem(self.rule, self.follow.union(other.follow), self.pos)

class ParsionFSMState:
    def __init__(self, items):
        self.items = sorted(items)
    
    def next_syms(self):
        return set(it.get_next()[0] for it in self.items if not it.is_complete())
    
    def reductions(self):
        return [it for it in self.items if it.is_complete()]
    
    def take(self, sym):
        result = []
        for item in self.items:
            next_item = item.take(sym)
            if next_item is not None:
                result.append(next_item)
        return result
    
    def __str__(self):
        return "\n".join(str(it) for it in self.items)
    
    def __eq__(self, other):
        return self.items == other.items

class ParsionFSM:
    def __init__(self, grammar_rules):
        self.grammar = [
            ParsionFSMGrammarRule(
                0,
                'ENTRY',
                'ENTRY',
                'entry END'
            )
        ] + [
            ParsionFSMGrammarRule(id+1, name, gen, rulestr)
            for id, (name, gen, rulestr)
            in enumerate(grammar_rules)
        ]
        
        self._build_states()

    def _get_items_by_gen(self, gen, follow):
        return [
            ParsionFSMItem(rule, follow)
            for rule
            in self.grammar
            if rule.gen == gen
        ]
    
    def _add_state(self, state):
        for i, state_i in enumerate(self.states):
            if state == state_i:
                return i
        self.states.append(state)
        self.table.append({})
        return len(self.states)-1
    
    def _get_first(self, syms):
        checked = set()
        while True:
            for cur_sym in syms-checked:
                for rule in self.grammar:
                    if rule.gen == cur_sym:
                        syms.add(rule.parts[0])
                checked.add(cur_sym)
            if syms == checked:
                return syms
    
    def _get_closure(self, items):
        """
        Get a closure from list of items
        
        A closure is the input items, but also populated with new items from
        grammars, which generates the next symbol of the incoming list of items
        """
        running = True
        syms_added = set()

        all_items = []
        queue = []

        for item in items:
            queue.append(item)

        # Resolve all sub items
        while len(queue) > 0:
            it = queue.pop()
            if any(cur == it for cur in all_items):
                continue
            all_items.append(it)
            
            if not it.is_complete():
                sym, follow = it.get_next()
                for item in self._get_items_by_gen(sym, self._get_first(follow)):
                    queue.append(item)

        # Merge items with same rule and pos
        result = []
        for it in all_items:
            is_merged = False
            for i, res_it in enumerate(result):
                if it.is_mergable(res_it):
                    is_merged = True
                    result[i] = res_it.merge(it)
                    break
            if not is_merged:
                result.append(it)

        result.sort()
        return result


    def _build_states(self):
        self.states = [
            ParsionFSMState(self._get_closure([
                ParsionFSMItem(
                    self.grammar[0],
                    set()
                )
            ]))
        ]
        self.table = [{}]
        state_queue = [0]
        processed = set()

        while len(state_queue) > 0:
            state_id = state_queue.pop(0)
            if state_id in processed:
                continue
            state = self.states[state_id]
            processed.add(state_id)

            for sym in state.next_syms():
                next_id = self._add_state(ParsionFSMState(self._get_closure(state.take(sym))))
                state_queue.append(next_id)
                self.table[state_id][sym] = ('s', next_id)
            
            for it in state.reductions():
                for sym in it.follow:
                    assert sym not in self.table[state_id], "Shift/Reduce conflict"
                    self.table[state_id][sym] = ('r', it.rule.id)
                

    def export(self):
        return [g.export() for g in self.grammar], self.table
