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
        potions = connection.execute(sqlalchemy.text("""
                                                     SELECT potions.name, potions.red, potions.green, potions.blue, potions.dark, potions.cost, COALESCE(SUM(ledger.quantity), 0) AS quantity
                                                     FROM potions
                                                     LEFT JOIN ledger ON potions.name = ledger.item
                                                     WHERE potions.name LIKE '%Potion'
                                                     GROUP BY potions.name
                                                     ORDER BY quantity DESC LIMIT 6"""))
        for name, red, green, blue, dark, cost, quantity in potions:
            if (quantity != 0):
                catalog.append({
                    "sku": name,
                    "name": name,
                    "quantity": quantity,
                    "price": cost,
                    "potion_type": [red, green, blue, dark],
                })

    return catalog

"""     
    with db.engine.begin() as connection:
        numGreenPotions = connection.execute(sqlalchemy.text("SELECT quantity FROM potions WHERE name = 'Green'")).scalar()
        if numGreenPotions > 0:
            catalog.append({
                "sku": "Green_Potion",
                "name": "green potion",
                "quantity": 1,
                "price": 50,
                "potion_type": [0, 100, 0, 0],
            })
        
        numRedPotions = connection.execute(sqlalchemy.text("SELECT quantity FROM potions WHERE name = 'Red'")).scalar()
        if numRedPotions > 0:
            catalog.append({
                "sku": "Red_Potion",
                "name": "red potion",
                "quantity": 1,
                "price": 50,
                "potion_type": [100, 0, 0, 0],
            })
        
        numBluePotions = connection.execute(sqlalchemy.text("SELECT quantity FROM potions WHERE name = 'Blue'")).scalar()
        if numBluePotions > 0:
            catalog.append({
                "sku": "Blue_Potion",
                "name": "blue potion",
                "quantity": 1,
                "price": 50,
                "potion_type": [0, 0, 100, 0],
            }) 
"""
