# Quarto

## Table of Contents

1. [Theory of games](#Theory)
2. [Example2](#example2)
3. [Third Example](#third-example)
4. [Fourth Example](#fourth-examplehttpwwwfourthexamplecom)

## Theory

https://github.com/yanntrividic/quarto-game
https://github.com/search?l=Jupyter+Notebook&q=quarto+game&type=Repositories
https://github.com/techwithtim/Python-Checkers-AI/blob/master/minimax/algorithm.py

Quarto is a board game of type:

- finite: meaning there is always at least one combination to win/lose or end in a draw
- deterministic: meaning the game states are determined solely by the players' actions
- turn-based: meaning the two players alternate turns

For a combinatorial game, it's possible to define a game tree where each node `v` represents a game state (the root is the initial state); each arc `(u,v)` represents instead a legal transition from `u` to `v`.
The levels alternate according to turns:

- even level: player A's turn
- odd level: player B's turn

The leaves are terminal states (victory/defeat of A or B or draw). A root-to-leaf path is a possible game (instance) of the game.

The objective is to reach a terminal state of the tree with utility maximization (winning decisively). We're assuming we're playing with `A`, if the opponent starts first, they become `A` and we become `B`, with the goal of minimizing utility (making A lose).
The idea is to define a utility function that has a value, given a terminal state:

- 0 if draw (leaf)
- 1 if A wins
- -1 if A loses (and B wins)

The numbers don't necessarily have to be these.

Let's assume that each turn A and B choose their most convenient move, that is, the one that leads them to better game endings. At the end of the game, it's easy to understand which are the best moves. From these, we can trace back to the current state node.

- if the level is A's, label the node with the `max` of the children's utilities
- if the level is B's, label the node with the `min` of the children's utilities.

`A(B)` moves to the child with utility `max(min)`.

![image](./image.jpg)

With minmax, each time I must maximize my move or minimize the opponent's move.

The general algorithm is a recursive algorithm

```
minMaxMove(node u) -> son v:
    return argmax_v minval(v)

# if I am a leaf I return the utility, otherwise I calculate the minimum
maxval(node u) -> real:
    if (u is leaf) return f(u)
    f(u) <- - infinite
    for each v in sons(u):
        f(u)=max{f(u),minval(v)}
    return f(u)

# The state I'm in is a leaf? If yes I return the terminal state, if instead it's not a leaf
# I must minimize the authority of my children and my f(u) is initialized with + infinite, then I go to find the minimum
# I therefore look for the smallest utility of my children, who however are opponents, so I must ask maxval for the utility
minval(node u) -> real:
        if (u is leaf) return f(u)
    f(u) <- + infinite
    for each v in sons(u):
        f(u)=min{f(u),maxval(v)}
    return f(u)
```

![image](./image2.jpg)

The algorithm is a depth-first traversal, in post-order because I first evaluate the children and then evaluate the rest. The computational complexity is equal to all nodes of the tree, same for spatial complexity. If we can understand the number of nodes, we have characterized the complexities.

We need to apply a _cutoff_ technique where the idea is that instead of expanding the game tree to the leaves, we expand it to a certain depth `d` from the current node. The deepest states are evaluated through an evaluation function `e(v)` and the result is propagated upward through the Min-Max algorithm.
For example, in tic-tac-toe `e(v)=possible tic-tac-toes for X - possible tic-tac-toes for 0`. If it's positive, then I have possibilities for X, otherwise for 0. In case of equality to zero, then I have the same probability.

Obviously in the case of minmax, how do I do it? You must satisfy some requirements:

- correctness: it must be consistent with the utility function `f(v)` if applied to the terminal states of the game, that is, it must induce the same ordering
- efficiency: it must be fast to calculate, otherwise it would be better to increase the search depth
- precision: it must reflect the real situation of the player, that is, be proportional to their probability of winning

It can depend on one or more characteristics of the game state `v`.

Implementation of the cutoff

```
minMaxMove (node u, depth d) -> son v:
    return argmax_v minval(v,d)

maxval (node u, depth d) -> real:
    if (level(u)==d) return e(u)
    e(u)= - infinite
    for each v in sons(u):
        e(u)=max{e(u),minval(v,d)}
    return e(u)

minval (node u, depth d) -> real:
    if (level(u)==d) return e(u)
    e(u)= + infinite
    for each v in sons(u):
        e(u)=min{e(u),max(v,d)}
    return e(u)
```

The difference is the choice of `d`:

- even: pessimistic, evaluates the game state with `max` that must make a move, I'm ignoring the advantage
- odd: optimistic
- the larger d is, the more accurate the estimate (but also the difficulty)

Generally, to win against a human, one chooses `d>5` which is the human limit (statistics...)
