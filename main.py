#!/usr/bin/env python3
"""
Purifai → Substack Notes funnel.

Commands:
  fetch      Check Purifai RSS for new posts and generate notes into the queue
  post       Post the next pending note from the newest article with queued notes
  status     Show queue stats and recent activity
  preview    Print the next pending note without posting it
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

PURIFAI_FEED_URL = os.environ.get("PURIFAI_FEED_URL", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
SUBSTACK_SESSION_COOKIE = os.environ.get("SUBSTACK_SESSION_COOKIE", "")


def cmd_fetch():
    from src.rss_reader import fetch_new_posts
    from src.note_generator import generate_notes
    from src.state_manager import (
        load_state, save_state, mark_post_processed,
        add_notes_to_queue, pending_count,
    )

    if not PURIFAI_FEED_URL:
        print("ERROR: PURIFAI_FEED_URL not set in .env")
        sys.exit(1)
    if not ANTHROPIC_API_KEY:
        print("ERROR: ANTHROPIC_API_KEY not set in .env")
        sys.exit(1)

    state = load_state()
    seen_ids = set(state.processed_post_ids)

    print(f"Fetching {PURIFAI_FEED_URL} ...")
    new_posts = fetch_new_posts(PURIFAI_FEED_URL, seen_ids)

    if not new_posts:
        print("No new posts found.")
        return

    print(f"Found {len(new_posts)} new post(s).")

    for post in new_posts:
        print(f"\n  Generating notes for: {post.title}")
        notes = generate_notes(post.title, post.content, post.url)
        add_notes_to_queue(state, notes, post.title, post.url)
        mark_post_processed(state, post.id)
        print(f"  → {len(notes)} notes added to queue")

    save_state(state)
    print(f"\nDone. Queue now has {pending_count(state)} pending note(s).")


def cmd_post():
    from src.substack_client import SubstackClient
    from src.state_manager import (
        load_state, save_state, current_pending_source_post_url, next_pending_note,
        mark_note_posted, pending_notes,
    )

    if not SUBSTACK_SESSION_COOKIE:
        print("ERROR: SUBSTACK_SESSION_COOKIE must be set in .env")
        sys.exit(1)

    state = load_state()
    source_post_url = current_pending_source_post_url(state)
    note = next_pending_note(state, source_post_url)

    if note is None:
        print("No pending notes.")
        return

    print(f"Posting note from: {note.source_post_title}")
    print(f"\n{note.text}\n")

    client = SubstackClient(SUBSTACK_SESSION_COOKIE)
    client.post_note(note.text)
    mark_note_posted(state, note)
    save_state(state)

    remaining = len(pending_notes(state, source_post_url))
    print(f"Posted. {remaining} note(s) remaining for this article.")


def cmd_status():
    from src.state_manager import (
        load_state, current_pending_source_post_url, pending_count,
        pending_notes, posted_count,
    )

    state = load_state()
    print(f"Processed posts : {len(state.processed_post_ids)}")
    print(f"Notes pending   : {pending_count(state)}")
    print(f"Notes posted    : {posted_count(state)}")

    source_post_url = current_pending_source_post_url(state)
    pending = pending_notes(state, source_post_url)
    if pending:
        print("\nNext notes from current article:")
        for i, n in enumerate(pending[:5], 1):
            preview = n.text[:80].replace("\n", " ")
            print(f"  {i}. {preview}...")
    else:
        print("\nNo pending notes.")


def cmd_preview():
    from src.state_manager import load_state, current_pending_source_post_url, pending_notes

    state = load_state()
    source_post_url = current_pending_source_post_url(state)
    pending = pending_notes(state, source_post_url)

    if not pending:
        print("No pending notes.")
        return

    print(f"Source: {pending[0].source_post_title}")
    print(f"URL:    {pending[0].source_post_url}")
    print(f"{len(pending)} notes queued\n")

    for i, note in enumerate(pending, 1):
        print(f"{'═' * 40}")
        print(f"  NOTE {i} of {len(pending)}")
        print(f"{'═' * 40}")
        print()
        print(note.text)
        print()


COMMANDS = {
    "fetch": cmd_fetch,
    "post": cmd_post,
    "status": cmd_status,
    "preview": cmd_preview,
}


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(__doc__)
        print("Available commands:", ", ".join(COMMANDS))
        sys.exit(1)
    COMMANDS[sys.argv[1]]()


if __name__ == "__main__":
    main()
