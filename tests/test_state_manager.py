import unittest

from src.state_manager import (
    State,
    add_notes_to_queue,
    current_pending_source_post_url,
    mark_note_posted,
    next_pending_note,
)


class QueuePriorityTests(unittest.TestCase):
    def test_newer_notes_are_drained_before_older_leftovers(self):
        state = State()

        add_notes_to_queue(state, ["old 1", "old 2"], "Old post", "old-url")
        add_notes_to_queue(state, ["new 1", "new 2"], "New post", "new-url")

        self.assertEqual(current_pending_source_post_url(state), "new-url")
        self.assertEqual(next_pending_note(state, "new-url").text, "new 1")

        mark_note_posted(state, next_pending_note(state, "new-url"))
        self.assertEqual(current_pending_source_post_url(state), "new-url")
        self.assertEqual(next_pending_note(state, "new-url").text, "new 2")

        mark_note_posted(state, next_pending_note(state, "new-url"))
        self.assertEqual(current_pending_source_post_url(state), "old-url")
        self.assertEqual(next_pending_note(state, "old-url").text, "old 1")


if __name__ == "__main__":
    unittest.main()
