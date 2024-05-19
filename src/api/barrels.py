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
    
    barrel_plan = []
    with db.engine.begin() as connection:
        curr_ml = connection.execute(sqlalchemy.text(
            "SELECT item, COALESCE(SUM(quantity), 0) AS total FROM ledger WHERE item LIKE '%ml' GROUP BY item"))
        curr_gold = connection.execute(sqlalchemy.text(
            "SELECT COALESCE(SUM(quantity), 0) FROM ledger WHERE item = 'gold' ")).scalar()
        ml_cap = connection.execute(sqlalchemy.text(
            "SELECT ml_cap FROM potions")).scalar()

        # get quantity of each ml type
        for item, total in curr_ml:
            if 'red' in item:
                curr_red_ml = total
            elif 'green' in item:
                curr_green_ml = total
            elif 'blue' in item:
                curr_blue_ml = total

        barrelsize = 500
        if ml_cap >= 30000:
            barrelsize = 5000

        wholesale_catalog = sorted(wholesale_catalog, key=lambda barrel: (barrel.price / barrel.ml_per_barrel))
        
        for barrel in wholesale_catalog:
            if barrel.potion_type == [0, 1, 0, 0] and (barrel.ml_per_barrel >= barrelsize or (curr_green_ml < 1000 and barrel.ml_per_barrel >= 500)):
                cap = ml_cap/3 - curr_green_ml
                qty = int(cap // barrel.ml_per_barrel)
                while barrel.price*qty > curr_gold and qty > 0:
                    qty -= 1
                if qty > 0:
                    curr_gold -= barrel.price*qty
                    barrel_plan.append({
                        "sku": barrel.sku,
                        "quantity": qty,
                    })
                    curr_green_ml += barrel.ml_per_barrel * qty

            elif barrel.potion_type == [1, 0, 0, 0] and (barrel.ml_per_barrel >= barrelsize or (curr_red_ml < 1000 and barrel.ml_per_barrel >= 500)):
                cap = ml_cap/3 - curr_red_ml
                qty = int(cap // barrel.ml_per_barrel)
                while barrel.price*qty > curr_gold and qty > 0:
                    qty -= 1
                if qty > 0:
                    curr_gold -= barrel.price*qty
                    barrel_plan.append({
                        "sku": barrel.sku,
                        "quantity": qty,
                    })
                    curr_gold += barrel.ml_per_barrel * qty
        
            elif barrel.potion_type == [0, 0, 1, 0] and (barrel.ml_per_barrel >= barrelsize or (curr_blue_ml < 1000 and barrel.ml_per_barrel >= 500)):
                cap = ml_cap/3 - curr_blue_ml
                qty = int(cap // barrel.ml_per_barrel)
                while barrel.price*qty > curr_gold and qty > 0:
                    qty -= 1
                if qty > 0:
                    curr_gold -= barrel.price*qty
                    barrel_plan.append({
                        "sku": barrel.sku,
                        "quantity": qty,
                    })
                    curr_blue_ml += barrel.ml_per_barrel * qty
                    

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