from fastapi import APIRouter

import sqlalchemy
from src import database as db

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """

    catalog = []
    with db.engine.begin() as connection:
        numGreenPotions = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory")).scalar()
        if numGreenPotions > 0:
            catalog.append({
                "sku": "Green_Potion",
                "name": "green potion",
                "quantity": 1,
                "price": 50,
                "potion_type": [0, 100, 0, 0],
            })
        
        numRedPotions = connection.execute(sqlalchemy.text("SELECT num_red_potions FROM global_inventory")).scalar()
        if numRedPotions > 0:
            catalog.append({
                "sku": "Red_Potion",
                "name": "red potion",
                "quantity": 1,
                "price": 50,
                "potion_type": [100, 0, 0, 0],
            })
        
        numBluePotions = connection.execute(sqlalchemy.text("SELECT num_blue_potions FROM global_inventory")).scalar()
        if numBluePotions > 0:
            catalog.append({
                "sku": "Blue_Potion",
                "name": "blue potion",
                "quantity": 1,
                "price": 50,
                "potion_type": [0, 0, 100, 0],
            })


    return catalog


