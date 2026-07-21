import argparse
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from core.app_state import load_app_state, save_app_state


def seed_co_play_history(self_puuid, other_puuid, count=3, match_id="manual-co-play-test", base_path=None):
    self_puuid = str(self_puuid or "").strip()
    other_puuid = str(other_puuid or "").strip()
    match_id = str(match_id or "").strip()
    count = int(count)

    if not self_puuid:
        raise ValueError("self_puuid is required")
    if not other_puuid:
        raise ValueError("other_puuid is required")
    if not match_id:
        raise ValueError("match_id is required")
    if count < 1:
        raise ValueError("count must be at least 1")

    state = load_app_state(base_path=base_path)
    history = state.setdefault("co_play_history", {"by_user": {}})
    by_user = history.setdefault("by_user", {})
    user_history = by_user.setdefault(self_puuid, {"matches": {}, "counts": {}})
    matches = user_history.setdefault("matches", {})
    counts = user_history.setdefault("counts", {})

    matches[match_id] = [self_puuid, other_puuid]
    counts[other_puuid] = count

    return save_app_state(state, base_path=base_path)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Seed ValScanner app_state.json with a fake previous co-play count."
    )
    parser.add_argument("--self-puuid", required=True, help="Your local Valorant account PUUID.")
    parser.add_argument("--other-puuid", required=True, help="A visible player's PUUID to show the swords badge for.")
    parser.add_argument("--count", type=int, default=3, help="Badge count to display. Defaults to 3.")
    parser.add_argument(
        "--match-id",
        default="manual-co-play-test",
        help="Fake match id to write into co_play_history.matches.",
    )
    parser.add_argument(
        "--base-path",
        default=None,
        help="Optional repo/app base path. Defaults to the current ValScanner repo.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    normalized = seed_co_play_history(
        args.self_puuid,
        args.other_puuid,
        count=args.count,
        match_id=args.match_id,
        base_path=args.base_path,
    )
    saved_count = normalized["co_play_history"]["by_user"][args.self_puuid]["counts"][args.other_puuid]
    print(f"Seeded co-play count {saved_count} for {args.other_puuid}.")


if __name__ == "__main__":
    main()
