"""Crypto API."""

from typing import Dict, List

import requests

# API Documentation - https://www.coingecko.com/en/api#explore-api


def get_coins(id_list=None) -> List[Dict]:
    """This function will get the top 10 coins at the current time, sorted by market cap in desc order."""
    url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd"
    if id_list:
        url += "&ids=" + ",".join(id_list)
    else:
        url += "&per_page=10&page=1"
    response = requests.get(f'{url}&order=market_cap_desc&sparkline=false')
    
    # Important keys
    # - id
    # - symbol
    # - name
    # - current_price
    return response.json()


def get_coin_price_history(coin_id: str) -> List[Dict]:
    response = requests.get(f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days=9&interval=daily")

    # Returns a list of tuples
    # Item 0 -> Unix Timestamp in UTC
    # Item 1 -> price 17/18 decimal places
    return response.json()['prices']


# utilize this function when submitting an order
def submit_order(coin_id: str, quantity: int, bid: float):
    """
    Mock function to submit an order to an exchange. 
    
    Assume order went through successfully and the return value is the price the order was filled at.
    """
    return bid