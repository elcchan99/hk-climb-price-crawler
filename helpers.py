"""Helper functions"""

from typing import Dict, Union


def breakdown_price_tag(price_tag: str) -> Dict[str, Union[str, int]]:
    """
    Breakdown a string price tag into currency & price amount
    """
    if not price_tag:
        return {}
    return {
        "currency_symbol": price_tag[0],
        "price": int(price_tag[1:].replace(",", "")),
    }
