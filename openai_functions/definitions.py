tools = [
    {
        "type": "function",
        "function": {
            "name": "Item.get_item_details",
            "description": "Get details of an item.",
            "parameters": {
                "type": "object",
                "properties": {
                    "item_id": {
                        "type": "string",
                        "description": "The ID of the item.",
                    },
                },
                "required": ["item_id"],
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "Product.recommend_products",
            "description": "Recommend products to the user based on their query.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_query": {
                        "type": "string",
                        "description": "The query input by the user.",
                    },
                },
                "required": ["user_query"],
            },
        }
    },
]
