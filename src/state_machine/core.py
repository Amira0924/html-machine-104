"""Core finite state machine.

The machine is defined by an explicit table of allowed transitions. Any
transition not in the table raises InvalidTransitionError. This is the central
design decision: the machine cannot reach a state for which no transition was
declared, which makes the set of reachable states statically inspectable.

States and events are plain hashable values (strings are typical). We do not
model entry/exit actions, guards, or hierarchical states. Those concerns belong
to a richer library; adding them here would multiply the edge cases without a
clear payoff for the problem this library solves.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Hashable, Iterable, Mapping, Tuple


class TransitionError(Exception):
    """Base class for state machine transition errors."""


class InvalidTransitionError(TransitionError):
    """Raised when an event is fired for which no transition is defined.

    Distinct from a programming error (such as registering an unknown state
    in the transition table) so that callers can catch transition failures
    without also catching bugs in machine construction.
    """


class StateMachine:
    """A finite state machine that rejects transitions not in its table.

    Parameters
    ----------
    transitions:
        A mapping of (current_state, event) -> next_state. Every state and
        event must be hashable. The initial state is taken from the first
        transition's current_state, unless ``initial_state`` is given.
    initial_state:
        The state the machine starts in. Must appear as a current_state or
        next_state somewhere in ``transitions``. Required when
        ``transitions`` is empty only if you intend to call ``fire`` before
        adding transitions; otherwise it is still required so the machine has
        a defined starting point.

    Notes
    -----
    The machine is immutable after construction: transitions cannot be added
    or removed at runtime. This keeps the reachable-state set fixed, which is
    the whole point of declaring transitions up front. If you need a dynamic
    machine, build a new one.
    """

    def __init__(
        self,
        transitions: Mapping[Tuple[Hashable, Hashable], Hashable],
        *,
        initial_state: Hashable,
    ) -> None:
        if initial_state is None:
            raise ValueError("initial_state must not be None")
        # Normalize into a plain dict so callers can't mutate our internal
        # table by holding a reference to the mapping they passed in.
        self._transitions: Dict[Tuple[Hashable, Hashable], Hashable] = {}
        known_states: set = set()
        for (state, event), target in transitions.items():
            if not isinstance(state, Hashable) or not isinstance(event, Hashable):
                raise TypeError(f"transition key ({state!r}, {event!r}) must be hashable")
            if not isinstance(target, Hashable):
                raise TypeError(f"transition target {target!r} must be hashable")
            self._transitions[(state, event)] = target
            known_states.add(state)
            known_states.add(target)
        if initial_state not in known_states and not self._transitions:
            # Empty machine with an initial state is allowed: the machine sits
            # in that state and every fire raises. This supports the case of
            # constructing a machine whose transitions are added by rebuilding.
            known_states.add(initial_state)
        elif initial_state not in known_states:
            raise ValueError(
                f"initial_state {initial_state!r} does not appear in any transition"
            )
        self._initial_state = initial_state
        self._state = initial_state

    @property
    def state(self) -> Hashable:
        """The current state."""
        return self._state

    @property
    def initial_state(self) -> Hashable:
        """The state the machine was constructed with."""
        return self._initial_state

    @property
    def states(self) -> Tuple[Hashable, ...]:
        """All states known to the machine, in insertion order."""
        # Rebuild on each call; the set is small and this avoids staleness if
        # we ever relax immutability. Tuple so callers can't mutate.
        seen: Dict[Hashable, None] = {}
        for (s, _), t in self._transitions.items():
            seen.setdefault(s, None)
            seen.setdefault(t, None)
        seen.setdefault(self._initial_state, None)
        return tuple(seen.keys())

    @property
    def events(self) -> Tuple[Hashable, ...]:
        """All events known to the machine, in first-seen order."""
        seen: Dict[Hashable, None] = {}
        for (_, e) in self._transitions.keys():
            seen.setdefault(e, None)
        return tuple(seen.keys())

    def can_fire(self, event: Hashable) -> bool:
        """Return True if ``event`` is a valid transition from the current state."""
        return (self._state, event) in self._transitions

    def fire(self, event: Hashable) -> Hashable:
        """Apply ``event`` and return the new state.

        Raises
        ------
        InvalidTransitionError
            If no transition is defined for (current_state, event).
        """
        try:
            target = self._transitions[(self._state, event)]
        except KeyError:
            raise InvalidTransitionError(
                f"no transition from state {self._state!r} on event {event!r}"
            ) from None
        self._state = target
        return target

    def reset(self) -> Hashable:
        """Return the machine to its initial state and return that state."""
        self._state = self._initial_state
        return self._state

    def is_valid_state(self, state: Hashable) -> bool:
        """True if ``state`` is one of the machine's known states."""
        return state in self.states

    def transitions_from(self, state: Hashable) -> Tuple[Tuple[Hashable, Hashable], ...]:
        """Return all (event, next_state) pairs reachable from ``state``."""
        if state not in self.states:
            raise KeyError(f"unknown state {state!r}")
        return tuple(
            (event, target)
            for (s, event), target in self._transitions.items()
            if s == state
        )
