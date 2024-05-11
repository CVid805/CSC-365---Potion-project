from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
from enum import Enum

import sqlalchemy
from src import database as db
from typing import Dict

router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)

class search_sort_options(str, Enum):
    customer_name = "customer_name"
    item_sku = "item_sku"
    line_item_total = "line_item_total"
    timestamp = "timestamp"

class search_sort_order(str, Enum):
    asc = "asc"
    desc = "desc"   

@router.get("/search/", tags=["search"])
def search_orders(
    customer_name: str = "",
    potion_sku: str = "",
    search_page: str = "",
    sort_col: search_sort_options = search_sort_options.timestamp,
    sort_order: search_sort_order = search_sort_order.desc,
):
    """
    Search for cart line items by customer name and/or potion sku.

    Customer name and potion sku filter to orders that contain the 
    string (case insensitive). If the filters aren't provided, no
    filtering occurs on the respective search term.

    Search page is a cursor for pagination. The response to this
    search endpoint will return previous or next if there is a
    previous or next page of results available. The token passed
    in that search response can be passed in the next search request
    as search page to get that page of results.

    Sort col is which column to sort by and sort order is the direction
    of the search. They default to searching by timestamp of the order
    in descending order.

    The response itself contains a previous and next page token (if
    such pages exist) and the results as an array of line items. Each
    line item contains the line item id (must be unique), item sku, 
    customer name, line item total (in gold), and timestamp of the order.
    Your results must be paginated, the max results you can return at any
    time is 5 total line items.
    """

    results = []
    with db.engine.begin() as connection:
        query = connection.execute(sqlalchemy.text("""
                                                    SELECT cart_items.line_item_id, cart_items.created_at AS timestamp, cart_items.quantity
                                                    FROM cart_items
                                                    JOIN carts on cart_items.cart_id = carts.cart_id
                                                    JOIN potions on potions.name = cart_items.items
                                                    JOIN customers on customers.cust_id = carts.cust_id
                                                    WHERE cart_items.items = :sku AND customers.name = :name
                                                    ORDER BY {} {}""".format(sort_col.value, sort_order.value)),
                                                    [{"sku": potion_sku, "name": customer_name}])
        for row in query:
            results.append(
                {
                    "line_item_id": row["line_item_id"],
                    "item_sku": row["item_sku"],
                    "customer_name": row["customer_name"],
                    "line_item_total": row["line_item_total"],
                    "timestamp": row["timestamp"],
                }
            )


    return results


class Customer(BaseModel):
    customer_name: str
    character_class: str
    level: int

@router.post("/visits/{visit_id}")
def post_visits(visit_id: int, customers: list[Customer]):
    """
    Which customers visited the shop today?
    """
    print(customers)

    return "OK"

cart_ids: Dict[int, Dict[str, int]] = {}
@router.post("/")
def create_cart(new_cart: Customer):
    """ """
    cart_id = len(cart_ids) + 1
    cart_ids[cart_id] = {}

    return {"cart_id": cart_id}


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """
    cart_ids[cart_id][item_sku] = cart_item.quantity
    return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    potionSum = 0
    goldSum = 0

    with db.engine.begin() as connection:
        numGreenPotions = connection.execute(sqlalchemy.text("SELECT quantity FROM potions WHERE name = 'Green'")).scalar()
        numRedPotions = connection.execute(sqlalchemy.text("SELECT quantity FROM potions WHERE name = 'Red'")).scalar()
        numBluePotions = connection.execute(sqlalchemy.text("SELECT quantity FROM potions WHERE name = 'Blue'")).scalar()
        currentGold = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory")).scalar()

    for Cart_id, in_dict in cart_ids.items():
        if Cart_id == cart_id:
            for sku, quantity in in_dict.items():
                if (sku == "Green_Potion"):
                    numGreenPotions -= 1
                    goldSum += 50
                    potionSum += 1
                if (sku == "Red_Potion"):
                    numRedPotions -= 1
                    goldSum += 50
                    potionSum += 1
                if (sku == "Blue_Potion"):
                    numBluePotions -= 1
                    goldSum += 50
                    potionSum += 1
    
    currentGold += goldSum
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_potions = {numGreenPotions}, gold = {currentGold}, num_red_potions = {numRedPotions}, num_blue_potions = {numBluePotions}"))

    return {"total_potions_bought": potionSum, "total_gold_paid": goldSum}

