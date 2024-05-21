from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth

import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)

class Barrel(BaseModel):
    sku: str

    ml_per_barrel: int
    potion_type: list[int]
    price: int

    quantity: int

@router.post("/deliver/{order_id}")
def post_deliver_barrels(barrels_delivered: list[Barrel], order_id: int):
    """ """
    for barrel in barrels_delivered:
        with db.engine.begin() as connection:
            connection.execute(sqlalchemy.text(
                "INSERT INTO ledger (item, quantity) VALUES (:gold, :gold_spent), (:red_ml, :new_red_ml), (:green_ml, :new_green_ml), (:blue_ml, :new_blue_ml), (:dark_ml, :new_dark_ml)"),
                        [{"gold": 'gold', "gold_spent": -1 * barrel.quantity * barrel.price, "red_ml": 'red_ml', "new_red_ml": barrel.quantity * barrel.ml_per_barrel * barrel.potion_type[0], "green_ml": 'green_ml', "new_green_ml": barrel.quantity * barrel.ml_per_barrel * barrel.potion_type[1], "blue_ml": 'blue_ml', "new_blue_ml": barrel.quantity * barrel.ml_per_barrel * barrel.potion_type[2], "dark_ml": 'dark_ml', "new_dark_ml": barrel.quantity * barrel.ml_per_barrel * barrel.potion_type[3]}])
    print(f"barrels delievered: {barrels_delivered} order_id: {order_id}")
    
    return "OK"




# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)
    
    curr_red_ml = 0
    curr_green_ml = 0
    curr_blue_ml = 0

    barrel_plan = []
    with db.engine.begin() as connection:
        curr_ml = connection.execute(sqlalchemy.text(
            "SELECT item, COALESCE(SUM(quantity), 0) AS total FROM ledger WHERE item LIKE '%ml' GROUP BY item"))
        curr_gold = connection.execute(sqlalchemy.text(
            "SELECT COALESCE(SUM(quantity), 0) FROM ledger WHERE item = 'gold' ")).scalar()
        ml_cap = connection.execute(sqlalchemy.text(
            "SELECT ml_cap FROM potions")).scalar()

        ml_cap = int(ml_cap)

        # get quantity of each ml type
        for item, total in curr_ml:
            if 'red' in item:
                curr_red_ml = total
            elif 'green' in item:
                curr_green_ml = total
            elif 'blue' in item:
                curr_blue_ml = total

        # start with small barrel size
        barrelsize = 500
        if ml_cap >= 30000:
            barrelsize = 5000

        # curr_green_ml < 1000 and barrel.ml_per_barrel >= 500
        
        for barrel in wholesale_catalog:
            barrel_qty = 0

            # red barrel
            if barrel.potion_type == [1, 0, 0, 0] and (barrel.ml_per_barrel == barrelsize ):
                cap = ml_cap // 3 - curr_red_ml
                print("red cap: ", cap)
                while (((curr_red_ml + barrel.ml_per_barrel) < cap) and 
                       (curr_gold > barrel.price) and 
                       (barrel_qty < barrel.quantity)):
                    barrel_qty += 1
                    curr_gold -= barrel.price
                    curr_red_ml += barrel.ml_per_barrel
                print("red qty: ", barrel_qty)
                barrel_plan.append({
                    "sku": barrel.sku,
                    "quantity": barrel_qty
                })

            # green barrel
            elif barrel.potion_type == [0, 1, 0, 0] and (barrel.ml_per_barrel == barrelsize ):
                cap = ml_cap // 3 - curr_green_ml
                print("green cap: ", cap)
                while (((curr_green_ml + barrel.ml_per_barrel) < cap) and 
                       (curr_gold > barrel.price) and 
                       (barrel_qty < barrel.quantity)):
                    barrel_qty += 1
                    curr_gold -= barrel.price
                    curr_green_ml += barrel.ml_per_barrel
                print("green qty: ", barrel_qty)
                barrel_plan.append({
                    "sku": barrel.sku,
                    "quantity": barrel_qty
                })

            # blue barrel
            elif barrel.potion_type == [0, 0, 1, 0] and (barrel.ml_per_barrel == barrelsize ):
                cap = ml_cap // 3 - curr_blue_ml
                print("blue cap: ", cap)
                while (((curr_blue_ml + barrel.ml_per_barrel) < cap) and 
                       (curr_gold > barrel.price) and 
                       (barrel_qty < barrel.quantity)):
                    barrel_qty += 1
                    curr_gold -= barrel.price
                    curr_blue_ml += barrel.ml_per_barrel
                print("blue qty: ", barrel_qty)
                barrel_plan.append({
                    "sku": barrel.sku,
                    "quantity": barrel_qty
                })

            # don't care about dark barrels

    print(f"barrel_plan: {barrel_plan}")
    return barrel_plan


# To quickly test barrels in debug
# [
#   {
#     "sku": "Green",
#     "ml_per_barrel": 100,
#     "potion_type": [
#       0, 1, 0, 0
#     ],
#     "price": 50,
#     "quantity": 1
#   },
# {
#     "sku": "Red",
#     "ml_per_barrel": 100,
#     "potion_type": [
#       1, 0, 0, 0
#     ],
#     "price": 50,
#     "quantity": 1
#   },
# {
#     "sku": "Blue",
#     "ml_per_barrel": 100,
#     "potion_type": [
#       0, 0, 1, 0
#     ],
#     "price": 50,
#     "quantity": 1
#   }
# ]