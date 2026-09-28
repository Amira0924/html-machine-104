# state-machine

A finite state machine that rejects transitions not declared in its table.

```python
from state_machine import StateMachine, InvalidTransitionError

machine = StateMachine(
    transitions={
        ("locked", "coin"): "unlocked",
        ("unlocked", "push"): "locked",
    },
    initial_state="locked",
)

machine.fire("coin")   # -> "unlocked"
machine.fire("push")    # -> "locked"

try:
    machine.fire("push")  # locked + push is not defined
except InvalidTransitionError:
    print("rejected")
```

## Why

The problem is narrow: you have a set of states, a set of events, and you want
to guarantee that the machine never reaches a state for which no transition was
written down. Libraries that let you register transitions dynamically, or that
fall back to no-ops on unknown events, make that guarantee impossible to check.

This library takes the opposite trade-off: the transition table is fixed at
construction time and copied internally, so the set of reachable states is
static. You cannot add a transition after the fact. If you need a different
machine, build a new one.

## Edge cases

- An `InvalidTransitionError` does **not** change the current state. The
  machine stays where it was.
- `initial_state` must appear in the transition table, unless the table is
  empty (in which case the machine sits in the initial state and every `fire`
  raises).
- States and events must be hashable. Passing an unhashable value (a list, a
  set) as a state, event, or target raises `TypeError` at construction.

## Exported names

- `StateMachine` — the machine class.
- `TransitionError` — base class for transition failures.
- `InvalidTransitionError` — raised by `fire` when no transition matches.

`StateMachine` methods: `fire(event)`, `can_fire(event)`, `reset()`,
`is_valid_state(state)`, `transitions_from(state)`. Properties: `state`,
`initial_state`, `states`, `events`.
