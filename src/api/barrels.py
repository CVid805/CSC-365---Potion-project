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
                "INSERT INTO ledger (name, quantity) VALUES (:gold, :gold_spent), (:red_ml, :new_red_ml), (:green_ml, :new_green_ml), (:blue_ml, :new_blue_ml), (:dark_ml, :new_dark_ml)"),
                        [{"gold": 'gold', "gold_spent": -1 * barrel.quantity * barrel.price, "red_ml": 'red_ml', "new_red_ml": barrel.quantity * barrel.ml_per_barrel * barrel.potion_type[0], "green_ml": 'green_ml', "new_green_ml": barrel.quantity * barrel.ml_per_barrel * barrel.potion_type[1], "blue_ml": 'blue_ml', "new_blue_ml": barrel.quantity * barrel.ml_per_barrel * barrel.potion_type[2], "dark_ml": 'dark_ml', "new_dark_ml": barrel.quantity * barrel.ml_per_barrel * barrel.potion_type[3]}])
    print(f"barrels delievered: {barrels_delivered} order_id: {order_id}")
    
    return "OK"




# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)
    
    with db.engine.begin() as connection:
        numGreenPotions = connection.execute(sqlalchemy.text("SELECT quantity FROM potions WHERE name = 'Green'")).scalar()
        numRedPotions = connection.execute(sqlalchemy.text("SELECT quantity FROM potions WHERE name = 'Red'")).scalar()
        numBluePotions = connection.execute(sqlalchemy.text("SELECT quantity FROM potions WHERE name = 'Blue'")).scalar()
        goldAmmount = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory")).scalar()
    
    barrelCatalog = []
    orderRed = 0
    orderGreen = 0
    orderBlue = 0
    if ((numGreenPotions <= numBluePotions) and (numBluePotions <= numRedPotions)):
        orderGreen += 1
    else:
        orderGreen = 0
    if ((numRedPotions <= numGreenPotions) and (numGreenPotions <= numBluePotions)):
        orderRed += 1
    else:
        orderRed = 0
    if ((numBluePotions <= numRedPotions) and (numRedPotions <= numGreenPotions)):
        orderBlue += 1
    else:
        orderBlue = 0
    

    for barrel in wholesale_catalog:
        if((orderGreen == 1) and (barrel.potion_type == [0, 1, 0, 0])):
            if(goldAmmount >= barrel.price):
                goldAmmount -= barrel.price
                barrelCatalog.append({
                    "sku" : barrel.sku,
                    "quantity" : orderGreen
                })

        if((orderRed == 1) and (barrel.potion_type == [1, 0, 0, 0])):
            if(goldAmmount >= barrel.price):
                goldAmmount -= barrel.price
                barrelCatalog.append({
                    "sku" : barrel.sku,
                    "quantity" : orderRed
                })

        if((orderBlue == 1) and (barrel.potion_type == [0, 0, 1, 0])):
            if(goldAmmount >= barrel.price):
                goldAmmount -= barrel.price
                barrelCatalog.append({
                    "sku" : barrel.sku,
                    "quantity" : orderBlue
                })
        
    return barrelCatalog

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

    """ if(numGreenPotions < 10) :
            greenInv = 1
        else:
            return []
    
    for barrel in wholesale_catalog:
        if barrel.potion_type == [0,1, 0, 0]:
            sku = barrel.sku """


