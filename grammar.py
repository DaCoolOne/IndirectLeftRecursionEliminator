

import time
from typing import Callable, List

class ParserError(Exception):
    def __init__(self, tag: str) -> None:
        super().__init__(f"Parser Error! {tag}")
class SemanticError(Exception):
    def __init__(self, tag: str) -> None:
        super().__init__(f"Semantic Error! {tag}")

class InvalidRule(ParserError):
    def __init__(self, rule) -> None:
        super().__init__(f"Invalid Rule! {rule}")
class InvalidGrammar(ParserError):
    def __init__(self) -> None:
        super().__init__(f"Invalid Grammar! Some nonterminals cannot terminate!")
class ExpectedToken(ParserError):
    def __init__(self) -> None:
        super().__init__("Expected Token")

class ImpossibleRule(SemanticError):
    def __init__(self, rule) -> None:
        super().__init__(f"Rule does not construct anything, {rule}")

class Expr:
    def __init__(self, tokens: List[str]) -> None:
        self.tokens = tokens
    def newToken(self, token: str) -> None:
        self.tokens.append(token)
    def __add__(self, __o: object):
        if not isinstance(__o, Expr):
            raise TypeError(f"unsupported operand type(s) for +: 'Expr' and '{type(__o).__name__}'")
        return Expr(self.tokens + __o.tokens)
    def __repr__(self) -> str:
        if len(self.tokens) == 0:
            return 'empty'
        return ' '.join(self.tokens)
    def __eq__(self, __o: object) -> bool:
        if not isinstance(__o, Expr):
            return False
        if len(__o.tokens) != len(self.tokens):
            return False
        return all(a == b for a,b in zip(self.tokens, __o.tokens))
    def startsWith(self, token: str):
        return len(self.tokens) > 0 and self.tokens[0] == token

class Rule:
    def __init__(self, nt: str, exprs: List[Expr]) -> None:
        self.nonterminal = nt
        self.exprs = exprs
    
    def __repr__(self) -> str:
        return f"{self.nonterminal} -> {' | '.join(str(e) for e in self.exprs)}"
    
    def simplify(self) -> None:
        for i in range(len(self.exprs), 1, -1):
            if any(a == self.exprs[i-1] for a in self.exprs[:i-1]):
                self.exprs.pop(i-1)

    # Removes indirect left recursion by expanding the expression
    # Pre: Other is not directly left recursive (may be indirectly left recursive)
    def performILREliminationExpansion(self, other: "Rule"):
        nt = other.nonterminal
        i = 0
        while i < len(self.exprs):
            expr = self.exprs[i]
            if expr.startsWith(nt):
                self.exprs.pop(i)
                expr.tokens.pop(0)
                for j, expansion in enumerate(other.exprs):
                    self.exprs.insert(i + j, expansion + expr)
            else:
                i += 1
        # We might have created duplicate rules accidentally. I don't think that's possible,
        # but in case I'm proven wrong, this is where you would fix it.
        # self.simplify()

    def eliminateDirectLeftRec(self, nameIsValid: Callable[[str],bool]) -> List["Rule"]:
        terminal_e: List[Expr] = []
        nonterminal_e: List[Expr] = []

        for exp in self.exprs:
            if exp.startsWith(self.nonterminal):
                nonterminal_e.append(exp)
            else:
                terminal_e.append(exp)
        
        # Special cases
        # If this occurs, then we have a rule like S -> S, wh;ch we cannot parse.
        if len(terminal_e) == 0:
            raise ImpossibleRule(self)
            # return []
        # If this occurs, then this rule is not left recursive.
        if len(nonterminal_e) == 0:
            return [ self ]

        # Create two rules to deal with the recursion.
        newName = self.nonterminal + "'"
        while not nameIsValid(newName):
            newName = newName + "'"

        for n in terminal_e:
            n.newToken(newName)
        for n in nonterminal_e:
            n.tokens.pop(0)
            n.newToken(newName)

        term_rule = Rule(self.nonterminal, terminal_e)
        nt_rule = Rule(newName, nonterminal_e + [ Expr([]) ])

        nt_rule.simplify()

        return [ term_rule, nt_rule ]
        

class Grammar:
    def __init__(self) -> None:
        self.rules: List[Rule] = []
        self.terminals = set()
        self.nonterminals = set()
    
    def eliminateIndirectLeftRecursion(self):
        # Find first occurence of indirect left recursion
        i = 0
        while i < len(self.rules):

            for j in range(i):
                self.rules[i].performILREliminationExpansion(self.rules[j])
            
            try:
                self.updateRules([
                    rule.eliminateDirectLeftRec(
                        lambda a: a not in self.terminals and a not in self.nonterminals
                    ) if i == k else [ rule ] for k, rule in enumerate(self.rules)
                ])
            except ImpossibleRule:
                raise InvalidGrammar()

            i += 1
        return

    def updateRules(self, _rules: List[List[Rule]]):
        self.rules = []
        for r in _rules:
            self.rules += r
        # Update the list of non-terminals
        self.addNonterminals()

    def importRule(self, rule_str):
        # Parse the string
        p: List[str] = rule_str.split(' ')
        try:
            nt = p[0]
            if p[1] != '->':
                raise InvalidRule(rule_str)
            exprs: List[Expr] = [ Expr([]) ]
            emptyException = False
            for e in p[2:]:
                if emptyException and e != '|':
                    raise InvalidRule(rule_str)
                if e == '|':
                    if len(exprs[-1].tokens) == 0 and not emptyException:
                        raise InvalidRule(rule_str)
                    exprs.append(Expr([]))
                    emptyException = False
                elif e == 'empty':
                    emptyException = True
                else:
                    emptyException = False
                    exprs[-1].newToken(e)
            self.rules.append(Rule(nt, exprs))

        except IndexError:
            raise ExpectedToken()
    
    def __repr__(self) -> str:
        return '\n'.join(str(r) for r in self.rules)

    def addNonterminals(self):
        for rule in self.rules:
            self.nonterminals.add(rule.nonterminal)

    def compile(self):
        self.nonterminals = set()
        self.terminals = set()
        # Build terminal and non terminal lists
        for rule in self.rules:
            self.nonterminals.add(rule.nonterminal)
            rule.simplify()
        for rule in self.rules:
            for expr in rule.exprs:
                for token in expr.tokens:
                    if token not in self.nonterminals:
                        self.terminals.add(token)

# Read in a file, output a non-left recursive grammar.
if __name__ == "__main__":

    # Get inputs
    grammar = Grammar()
    try:
        while True:
            s = input().strip()
            if s != '': grammar.importRule(s)
    except EOFError:
        pass

    # Compute the nonterminals
    grammar.compile()

    # Elminate indirect left recursion
    grammar.eliminateIndirectLeftRecursion()

    # Output
    print(grammar)