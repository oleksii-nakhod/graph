from typing import List, Dict, Any


def get_item_details(item_id: str) -> Dict[str, Any]:
    """
    Get details of an item.

    Parameters:
    item_id (str): The ID of the item.
    """
    return {"item_id": item_id, "details": "Item details here"}


def list_items() -> Dict[str, List[str]]:
    """
    List all items.
    """
    return {"items": ["Item 1", "Item 2"]}
