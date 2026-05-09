import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Optional


STATE_FILE = os.path.join(os.path.dirname(__file__), "..", "state.json")


@dataclass
class QueuedNote:
    text: str
    source_post_title: str
    source_post_url: str
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    posted_at: Optional[str] = None

    @property
    def is_posted(self) -> bool:
        return self.posted_at is not None


@dataclass
class State:
    processed_post_ids: List[str] = field(default_factory=list)
    queue: List[QueuedNote] = field(default_factory=list)


def _load_raw() -> dict:
    if not os.path.exists(STATE_FILE):
        return {"processed_post_ids": [], "queue": []}
    with open(STATE_FILE) as f:
        return json.load(f)


def _save_raw(data: dict) -> None:
    with open(STATE_FILE, "w") as f:
        json.dump(data, f, indent=2)


def load_state() -> State:
    raw = _load_raw()
    queue = [QueuedNote(**n) for n in raw.get("queue", [])]
    return State(
        processed_post_ids=raw.get("processed_post_ids", []),
        queue=queue,
    )


def save_state(state: State) -> None:
    _save_raw({
        "processed_post_ids": state.processed_post_ids,
        "queue": [asdict(n) for n in state.queue],
    })


def mark_post_processed(state: State, post_id: str) -> None:
    if post_id not in state.processed_post_ids:
        state.processed_post_ids.append(post_id)


def add_notes_to_queue(state: State, notes: List[str], post_title: str, post_url: str) -> None:
    for text in notes:
        state.queue.append(QueuedNote(
            text=text,
            source_post_title=post_title,
            source_post_url=post_url,
        ))


def next_pending_note(state: State) -> Optional[QueuedNote]:
    for note in state.queue:
        if not note.is_posted:
            return note
    return None


def mark_note_posted(state: State, note: QueuedNote) -> None:
    note.posted_at = datetime.now().isoformat()


def pending_count(state: State) -> int:
    return sum(1 for n in state.queue if not n.is_posted)


def posted_count(state: State) -> int:
    return sum(1 for n in state.queue if n.is_posted)
