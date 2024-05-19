from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import math
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/inventory",
    tags=["inventory"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.get("/audit")
def get_inventory():
    """ """
    with db.engine.begin() as connection:
        curr_gold = connection.execute(sqlalchemy.text(
            "SELECT COALESCE(SUM(quantity), 0) FROM ledger WHERE item = 'gold'")).scalar()
        total_pots = connection.execute(sqlalchemy.text(
            "SELECT COALESCE(SUM(quantity), 0) FROM ledger WHERE item LIKE '%Potion'")).scalar()
        total_ml = connection.execute(sqlalchemy.text(
            "SELECT COALESCE(SUM(quantity), 0) FROM ledger WHERE item LIKE '%ml'")).scalar()
        
    return {"number_of_potions": total_pots, "ml_in_barrels": total_ml, "gold": curr_gold}


# Gets called once a day
@router.post("/plan")
def get_capacity_plan():
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """
    pot_cap = 0
    ml_cap = 0

    with db.engine.begin() as connection:
        curr_gold = connection.execute(sqlalchemy.text(
            "SELECT COALESCE(SUM(quantity), 0) FROM ledger WHERE item = 'gold'")).scalar()
        tot_pots = connection.execute(sqlalchemy.text(
            "SELECT COALESCE(SUM(quantity), 0) FROM ledger WHERE item LIKE '%Potion'")).scalar()
        tot_ml = connection.execute(sqlalchemy.text(
            "SELECT COALESCE(SUM(quantity), 0) FROM ledger WHERE item LIKE '%ml'")).scalar()
        curr_pot_cap = connection.execute(sqlalchemy.text(
            "SELECT potion_cap FROM potions")).scalar()
        curr_ml_cap = connection.execute(sqlalchemy.text(
            "SELECT ml_cap FROM potions")).scalar()
        
        
        # check if we almost reach potion capacity limit
        if (tot_pots >= (curr_pot_cap * 0.9) and curr_gold >= 1000):
            pot_cap += 1
            curr_gold -= 1000
        # check if we almost reach ml capacity limit
        if (tot_ml >= (curr_ml_cap * 0.9) and curr_gold >= 1000):
            ml_cap += 1
            curr_gold -= 1000


    return {
        "potion_capacity": pot_cap,
        "ml_capacity": ml_cap
        }

class CapacityPurchase(BaseModel):
    potion_capacity: int
    ml_capacity: int

# Gets called once a day
@router.post("/deliver/{order_id}")
def deliver_capacity_plan(capacity_purchase : CapacityPurchase, order_id: int):
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(
            "UPDATE potions SET potion_cap = potions.potion_cap + :new_pot_cap, ml_cap = potions.ml_cap + :new_ml_cap"),
                           [{"new_pot_cap": capacity_purchase.potion_capacity * 50, "new_ml_cap": capacity_purchase.ml_capacity * 10000}])
        connection.execute(sqlalchemy.text(
            "INSERT INTO ledger (item, quantity) VALUES (:gold, :gold_spent)"),
                [{"gold": 'gold', "gold_spent": (-1 * capacity_purchase.potion_capacity * 1000) + (capacity_purchase.ml_capacity * 1000 * -1)}])
        
    return "OK"
