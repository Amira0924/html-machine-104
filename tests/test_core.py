import unittest

from state_machine import StateMachine, TransitionError, InvalidTransitionError


class TestStateMachine(unittest.TestCase):
    def _turnstile(self):
        # classic push-to-lock, coin-to-unlock turnstile
        return StateMachine(
            transitions={
                ("locked", "coin"): "unlocked",
                ("unlocked", "push"): "locked",
            },
            initial_state="locked",
        )

    def test_initial_state(self):
        m = self._turnstile()
        self.assertEqual(m.state, "locked")
        self.assertEqual(m.initial_state, "locked")

    def test_valid_transition_returns_new_state(self):
        m = self._turnstile()
        self.assertEqual(m.fire("coin"), "unlocked")
        self.assertEqual(m.state, "unlocked")
        self.assertEqual(m.fire("push"), "locked")
        self.assertEqual(m.state, "locked")

    def test_invalid_transition_raises(self):
        m = self._turnstile()
        with self.assertRaises(InvalidTransitionError):
            m.fire("push")  # locked + push is not defined

    def test_invalid_transition_does_not_change_state(self):
        m = self._turnstile()
        with self.assertRaises(InvalidTransitionError):
            m.fire("push")
        self.assertEqual(m.state, "locked")

    def test_invalid_transition_error_is_transition_error(self):
        m = self._turnstile()
        with self.assertRaises(TransitionError):
            m.fire("push")

    def test_can_fire(self):
        m = self._turnstile()
        self.assertTrue(m.can_fire("coin"))
        self.assertFalse(m.can_fire("push"))
        m.fire("coin")
        self.assertFalse(m.can_fire("coin"))
        self.assertTrue(m.can_fire("push"))

    def test_reset(self):
        m = self._turnstile()
        m.fire("coin")
        self.assertEqual(m.reset(), "locked")
        self.assertEqual(m.state, "locked")

    def test_states_collection(self):
        m = self._turnstile()
        self.assertEqual(set(m.states), {"locked", "unlocked"})

    def test_events_collection(self):
        m = self._turnstile()
        self.assertEqual(set(m.events), {"coin", "push"})

    def test_is_valid_state(self):
        m = self._turnstile()
        self.assertTrue(m.is_valid_state("locked"))
        self.assertTrue(m.is_valid_state("unlocked"))
        self.assertFalse(m.is_valid_state("jammed"))

    def test_transitions_from(self):
        m = self._turnstile()
        self.assertEqual(m.transitions_from("locked"), (("coin", "unlocked"),))
        self.assertEqual(m.transitions_from("unlocked"), (("push", "locked"),))

    def test_transitions_from_unknown_state_raises(self):
        m = self._turnstile()
        with self.assertRaises(KeyError):
            m.transitions_from("jammed")

    def test_initial_state_not_in_transitions_raises(self):
        with self.assertRaises(ValueError):
            StateMachine(
                transitions={("locked", "coin"): "unlocked"},
                initial_state="broken",
            )

    def test_none_initial_state_raises(self):
        with self.assertRaises(ValueError):
            StateMachine(transitions={}, initial_state=None)

    def test_empty_machine_with_initial_state(self):
        m = StateMachine(transitions={}, initial_state="idle")
        self.assertEqual(m.state, "idle")
        with self.assertRaises(InvalidTransitionError):
            m.fire("anything")

    def test_non_hashable_event_raises(self):
        with self.assertRaises(TypeError):
            StateMachine(
                transitions={("a", ["list"]): "b"},
                initial_state="a",
            )

    def test_non_hashable_target_raises(self):
        with self.assertRaises(TypeError):
            StateMachine(
                transitions={("a", "go"): {"set"}},
                initial_state="a",
            )

    def test_internal_table_not_aliased(self):
        table = {("locked", "coin"): "unlocked"}
        m = StateMachine(transitions=table, initial_state="locked")
        table[("locked", "coin")] = "tampered"
        # The machine must not see the external mutation.
        self.assertEqual(m.fire("coin"), "unlocked")

    def test_self_transition_allowed(self):
        m = StateMachine(
            transitions={("idle", "tick"): "idle"},
            initial_state="idle",
        )
        self.assertEqual(m.fire("tick"), "idle")
        self.assertEqual(m.state, "idle")

    def test_multiple_events_from_same_state(self):
        m = StateMachine(
            transitions={
                ("idle", "run"): "running",
                ("idle", "sleep"): "sleeping",
            },
            initial_state="idle",
        )
        self.assertTrue(m.can_fire("run"))
        self.assertTrue(m.can_fire("sleep"))
        m.fire("sleep")
        self.assertEqual(m.state, "sleeping")
        self.assertFalse(m.can_fire("run"))


if __name__ == "__main__":
    unittest.main()
