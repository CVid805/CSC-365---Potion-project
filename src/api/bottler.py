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

    for potion in potions_delivered:
        with db.engine.begin() as connection:
            connection.execute(sqlalchemy.text(
                "UPDATE potions SET quantity = potions.quantity + :quantity WHERE potions.Red = :redPots AND potions.Green = :greenPots AND potions.Blue = :bluePots"),
                    [{"quantity":potion.quantity, "redPots":potion.potion_type[0], "greenPots":potion.potion_type[1], "bluePots":potion.potion_type[2]}])
            connection.execute(sqlalchemy.text(
                "UPDATE global_inventory SET num_red_ml = global_inventory.num_red_ml - :redMl, num_green_ml = global_inventory.num_green_ml - :greenMl, num_blue_ml = global_inventory.num_blue_ml - :blueMl"), 
                    [{"redMl":(potion.quantity * potion.potion_type[0]), "greenMl":(potion.quantity * potion.potion_type[1]), "blueMl":(potion.quantity * potion.potion_type[2])}])

    return "OK"

    """
    newGreenPotions = 0
    newRedPotions = 0
    newBluePotions = 0
    greenMlUsed = 0
    redMlUsed = 0
    blueMlUsed = 0
    
    for Potion in potions_delivered: 
        if(Potion.potion_type == [100, 0, 0, 0]): 
            newRedPotions += Potion.quantity
            redMlUsed += (Potion.quantity * 100)
        
        elif(Potion.potion_type == [0, 100, 0, 0]): 
            newGreenPotions += Potion.quantity
            greenMlUsed += (Potion.quantity * 100)
        
        elif(Potion.potion_type == [0, 0, 100, 0]): 
            newBluePotions += Potion.quantity
            blueMlUsed += (Potion.quantity * 100)

    with db.engine.begin() as connection:
        numGreenPotions = connection.execute(sqlalchemy.text("SELECT quantity FROM potions WHERE name = 'Green'")).scalar()
        numGreenMl = connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory")).scalar()
        numRedPotions = connection.execute(sqlalchemy.text("SELECT quantity FROM potions WHERE name = 'Red'")).scalar()
        numRedMl = connection.execute(sqlalchemy.text("SELECT num_red_ml FROM global_inventory")).scalar()
        numBluePotions = connection.execute(sqlalchemy.text("SELECT quantity FROM potions WHERE name = 'Blue'")).scalar()
        numBlueMl = connection.execute(sqlalchemy.text("SELECT num_blue_ml FROM global_inventory")).scalar()

        numGreenPotions += newGreenPotions
        numGreenMl -= greenMlUsed
        numRedPotions += newRedPotions
        numRedMl -= redMlUsed
        numBluePotions += newBluePotions
        numBlueMl -= blueMlUsed

        with db.engine.begin() as connection:
            connection.execute(sqlalchemy.text(f"UPDATE global_`inventory SET num_green_ml = {numGreenMl}, num_red_ml = {numRedMl}, num_blue_ml = {numBlueMl}"))
            connection.execute(sqlalchemy.text(f"UPDATE potions SET quantity WHERE name"))
        """
    

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

    with db.engine.begin() as connection:
        numGreenMl = connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory")).scalar()
        while (numGreenMl >= 100):
            makeGreenBot += 1
            numGreenMl -= 100
        
        numRedMl = connection.execute(sqlalchemy.text("SELECT num_red_ml FROM global_inventory")).scalar()
        while (numRedMl >= 100):
            makeRedBot += 1
            numRedMl -= 100
        
        numBlueMl = connection.execute(sqlalchemy.text("SELECT num_blue_ml FROM global_inventory")).scalar()
        while (numBlueMl >= 100):
            makeBlueBot += 1
            numBlueMl -= 100

        if(makeGreenBot >= 1):
            bottlePlan.append({
                "potion_type" : [0, 100, 0, 0],
                "quantity" : makeGreenBot
            })
        
        if(makeRedBot >= 1):
            bottlePlan.append({
                "potion_type" : [100, 0, 0, 0],
                "quantity" : makeRedBot
            })
        
        if(makeBlueBot >= 1):
            bottlePlan.append({
                "potion_type" : [0, 0, 100, 0],
                "quantity" : makeBlueBot
            })

    return bottlePlan

if __name__ == "__main__":
    print(get_bottle_plan())

