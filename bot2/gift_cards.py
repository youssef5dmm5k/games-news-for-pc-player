import json
import logging
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"
DB_PATH = DATA_DIR / "gift_cards.json"

logger = logging.getLogger("bot2.gift_cards")


def load_database() -> dict:
    """Load the full gift-card / game-price database."""
    if not DB_PATH.is_file():
        logger.error("Database file not found: %s", DB_PATH)
        return {"gift_cards": [], "games": []}

    with open(DB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def search_items(query: str) -> list[dict]:
    """Return every gift card or game whose name contains *query* (case-insensitive)."""
    db = load_database()
    results: list[dict] = []
    q = query.lower()

    for item in db.get("gift_cards", []):
        if q in item.get("name", "").lower():
            results.append({**item, "_type": "gift_card"})

    for item in db.get("games", []):
        if q in item.get("name", "").lower():
            results.append({**item, "_type": "game"})

    return results


def get_cheapest_store(item: dict) -> dict | None:
    """Return the store entry with the lowest price."""
    stores = item.get("stores", [])
    if not stores:
        return None
    return min(stores, key=lambda s: s["price"])
