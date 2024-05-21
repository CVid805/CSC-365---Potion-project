from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth

import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)

class PotionInventory(BaseModel):
    potion_type: list[int]
    quantity: int

@router.post("/deliver/{order_id}")
def post_deliver_bottles(potions_delivered: list[PotionInventory], order_id: int):
    """ """
    print(f"potions delievered: {potions_delivered} order_id: {order_id}")

    with db.engine.begin() as connection:
        for Potion in potions_delivered:
            item = connection.execute(sqlalchemy.text(
                "SELECT name FROM potions WHERE potions.red = :red AND potions.green = :green AND potions.blue = :blue AND potions.dark = :dark"),
                               [{"red": Potion.potion_type[0], "green": Potion.potion_type[1], "blue": Potion.potion_type[2], "dark": Potion.potion_type[3]}]).scalar()
            connection.execute(sqlalchemy.text(
                "INSERT INTO ledger (item, quantity) VALUES (:item, :quantity)"),
                               [{"item": item, "quantity": Potion.quantity}])
            connection.execute(sqlalchemy.text(
                "INSERT INTO ledger (item, quantity) VALUES (:red_ml, :red_used), (:green_ml, :green_used), (:blue_ml, :blue_used), (:dark_ml, :dark_used)"),
                               [{"red_ml": 'red_ml', "red_used": -1 * Potion.quantity * Potion.potion_type[0], "green_ml": 'green_ml', "green_used": -1 * Potion.quantity * Potion.potion_type[1], "blue_ml": 'blue_ml', "blue_used": -1 * Potion.quantity * Potion.potion_type[2], "dark_ml": 'dark_ml', "dark_used": -1 * Potion.quantity * Potion.potion_type[3]}])
    return "OK"



@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """

    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    # Initial logic: bottle all barrels into red potions.
    
    makeGreenBot = 0
    makeRedBot = 0
    makeBlueBot = 0
    bottlePlan = []
    bottlerPlan = []

    with db.engine.begin() as connection:
        ml = connection.execute(sqlalchemy.text(
            "SELECT item, COALESCE(SUM(quantity), 0) AS total FROM ledger WHERE item LIKE '%ml' GROUP BY item"))
        for item, total in ml:
            if 'red' in item:
                curr_red_ml = total
            elif 'green' in item:
                curr_green_ml = total
            elif 'blue' in item:
                curr_blue_ml = total
            elif 'dark' in item:
                curr_dark_ml = total

        
        total_potions = connection.execute(sqlalchemy.text(
            "SELECT COALESCE(SUM(quantity), 0) FROM ledger WHERE item LIKE '%Potion'")).scalar()
        potion_cap = connection.execute(sqlalchemy.text(
            "SELECT potion_cap FROM potions")).scalar()
        
        counter = 0
        while((total_potions < potion_cap) and (counter < (potion_cap + 10))):
            potions = connection.execute(sqlalchemy.text("""
                                                        SELECT potions.red, potions.green, potions.blue, potions.dark
                                                        FROM potions
                                                        LEFT JOIN (
                                                            SELECT item, COALESCE(SUM(quantity), 0) AS total_quantity
                                                            FROM ledger
                                                            GROUP BY item
                                                        ) AS ledger_quantity ON potions.name = ledger_quantity.item
                                                        WHERE potions.name LIKE '%Potion' AND ledger_quantity.total_quantity < (0.165 * :potion_cap)
                                                        GROUP BY potions.name
                                                        ORDER BY COALESCE(SUM(ledger_quantity.total_quantity), 0) ASC"""),
                                         [{"potion_cap": potion_cap}])
            
            for red, green, blue, dark in potions:
                if (curr_red_ml >= red) and (curr_green_ml >= green) and (curr_blue_ml >= blue) and (curr_dark_ml >= dark) and (total_potions + 1 < potion_cap):
                    bottlePlan.append({
                        "potion_type": [red, green, blue, dark],
                        "quantity": 1,
                    })
                    curr_red_ml -= red
                    curr_green_ml -= green
                    curr_blue_ml -= blue
                    curr_dark_ml -= dark
                    total_potions += 1
                else:
                    counter += 1
            counter += 1
        
        potion_type_counts = {}
        for entry in bottlePlan:
            potion_type = tuple(entry["potion_type"])
            quantity = entry["quantity"]
            if potion_type in potion_type_counts:
                potion_type_counts[potion_type] += quantity
            else:
                potion_type_counts[potion_type] = quantity
        for potion_type, count in potion_type_counts.items():
            bottlerPlan.append({
                "potion_type": list(potion_type),
                "quantity": count
            })

    print(bottlerPlan)
    return bottlerPlan

if __name__ == "__main__":
    print(get_bottle_plan())

