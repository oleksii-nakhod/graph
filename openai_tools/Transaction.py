from typing import List, Dict, Any


def get_transaction_details(transaction_id: str) -> Dict[str, Any]:
    """
    Get details of an transaction.

    Parameters:
    transaction_id (str): The ID of the transaction.
    """
    from db.queries import get_node
    from config import Config
    transaction = get_node(transaction_id)
    transaction['x'] = "<feature vector>"
    for field in Config.HIDDEN_FIELDS:
        if field in transaction:
            del transaction[field]
    return transaction


def predict_class(transaction_id: str) -> Dict[str, Any]:
    """
    Predict the class of a transaction. 0 for licit, 1 for illicit.

    Parameters:
    transaction_id (str): The ID of the transaction.

    Returns:
    Dict[str, Any]: A dictionary containing the predicted class.
    """
    return None