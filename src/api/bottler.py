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

    newPotions = 0
    greenMlUsed = 0
    for Potion in potions_delivered: 
        if(Potion.potion_type ==[0, 100, 0, 0]): 
            newPotions += Potion.quantity
            greenMlUsed -= (Potion.quantity * 100)
    with db.engine.begin() as connection:
        numGreenPotions = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory")).scalar()
        numGreenMl = connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory")).scalar()
        numGreenPotions += newPotions
        numGreenMl -= greenMlUsed
        with db.engine.begin() as connection:
            connection.execute(sqlalchemy.text(f"UPDATE global_inventory SET num_green_potions = {numGreenPotions}, num_green_ml = {numGreenMl}"))
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
    ml_to_bot = 0
    with db.engine.begin() as connection:
        numGreenMl = connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory")).scalar()
        while (numGreenMl >= 100):
            ml_to_bot += 1
            numGreenMl -= 100
            
        if ml_to_bot == 0:
            return []

    return [
            {
                "potion_type": [0, 100, 0, 0],
                "quantity": ml_to_bot,
            }
        ]

if __name__ == "__main__":
    print(get_bottle_plan())

