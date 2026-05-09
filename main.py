#!/usr/bin/env python3
"""
Purifai → Substack Notes funnel.

Commands:
  fetch      Check Purifai RSS for new posts and generate notes into the queue
  post       Post the next pending note from the queue (run via cron)
  status     Show queue stats and recent activity
  preview    Print the next pending note without posting it
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

PURIFAI_FEED_URL = os.environ.get("PURIFAI_FEED_URL", "")
SUBSTACK_SESSION_COOKIE = os.environ.get("SUBSTACK_SESSION_COOKIE", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")


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
        load_state, save_state, next_pending_note,
        mark_note_posted, pending_count,
    )

    if not SUBSTACK_SESSION_COOKIE:
        print("ERROR: SUBSTACK_SESSION_COOKIE must be set in .env")
        sys.exit(1)

    state = load_state()
    note = next_pending_note(state)

    if note is None:
        print("Queue is empty — nothing to post.")
        return

    print(f"Posting note from: {note.source_post_title}")
    print(f"\n{note.text}\n")

    client = SubstackClient(SUBSTACK_SESSION_COOKIE)
    client.post_note(note.text)
    mark_note_posted(state, note)
    save_state(state)

    remaining = pending_count(state)
    print(f"Posted. {remaining} note(s) remaining in queue.")


def cmd_status():
    from src.state_manager import load_state, pending_count, posted_count

    state = load_state()
    print(f"Processed posts : {len(state.processed_post_ids)}")
    print(f"Notes pending   : {pending_count(state)}")
    print(f"Notes posted    : {posted_count(state)}")

    pending = [n for n in state.queue if not n.is_posted]
    if pending:
        print("\nNext notes in queue:")
        for i, n in enumerate(pending[:5], 1):
            preview = n.text[:80].replace("\n", " ")
            print(f"  {i}. {preview}...")


def cmd_preview():
    from src.state_manager import load_state, next_pending_note

    state = load_state()
    note = next_pending_note(state)

    if note is None:
        print("Queue is empty.")
        return

    print(f"Source: {note.source_post_title}")
    print(f"URL:    {note.source_post_url}")
    print(f"Added:  {note.created_at}")
    print("\n--- NOTE PREVIEW ---\n")
    print(note.text)
    print("\n--------------------")


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
