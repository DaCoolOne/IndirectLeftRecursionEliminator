# 3500 Honors Project

### Prompt: Write a program to perform left recursion elimination ( both direct and indirect ) on a given context free grammar.

# Grammar formatting

A Grammar is a list of rules in the following form:

`Head` -> `Node1` | `Node2` | `...` | `NodeK`

Where `Head` is a non-terminal string and where `Node` is a non-terminal if it is the head of any grammar rule.
`Node` is a terminal if it is not the head of any rule in the language.
`Node` can also be set to the string `empty` to represent an empty string.
Consecutive `Node`s are separated by spaces around a pipe "|" character.

By convention, terminals are strings built from lowercase letters and non-terminals start with an uppercase letter.
However, the program uses the `Head`s of rules to determine terminal or nonterminal status, so this convention may be ignored.

The input to this program is a Grammar.
The output of this program will be an equivalent grammar without any left recursion, or an error in the event the input is
messed up, or describes an invalid grammar (e.g, a grammar with no terminals).

### Example

Input:
```
S -> a A | S c
A -> A B b | A d | empty
B -> A d | S c
```

Output:
```
S -> a A S'
S' -> c S' | empty
A -> A'
A' -> B b A' | d A' | empty
B -> d A' d B' | d B' | a A S' c B'
B' -> b A' d B' | empty
```
