from typing import List, Dict, Any
from flask import current_app


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


def predict_transaction_class(transaction_id: str) -> Dict[str, Any]:
    """
    Predict the class of a transaction. 0 for licit, 1 for illicit.

    Parameters:
    transaction_id (str): The ID of the transaction.

    Returns:
    Dict[str, Any]: A dictionary containing the predicted class.
    """
    from db.queries import get_node
    transaction = get_node(transaction_id)
    transaction_classifier = current_app.transaction_classifier
    transaction_data = current_app.transaction_data
    predictions, probabilities = transaction_classifier.predict(transaction_data, transaction['orig_id'])
    return {
        'class': predictions.item(),
        'probability': probabilities.tolist()
    }


def list_recent_transactions() -> List[Dict[str, Any]]:
    """
    List recent transactions.

    Returns:
    List[Dict[str, Any]]: A list of dictionaries containing the recent transactions.
    """
    from db.queries import list_nodes
    from config import Config
    transactions = list_nodes({'labels': ['Transaction']}, page_size=3)
    for transaction in transactions:
        transaction['x'] = "<feature vector>"
        for field in Config.HIDDEN_FIELDS:
            if field in transaction:
                del transaction[field]
    return transactions