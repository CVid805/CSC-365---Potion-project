from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.post("/reset")
def reset():
    """
    Reset the game state. Gold goes to 100, all potions are removed from
    inventory, and all barrels are removed from inventory. Carts are all reset.
    """
    with db.engine.begin() as connection:
        # reset ledger
        connection.execute(sqlalchemy.text("TRUNCATE ledger"))
        # set default values
        connection.execute(sqlalchemy.text("""
                                            INSERT INTO ledger (name, quantity)
                                            VALUES ('gold', 100), ('red_ml', 0), ('green_ml', 0), ('blue_ml', 0),
                                                ('dark_ml', 0), ('Red_Potion', 0), ('Green_Potion', 0),
                                                ('Blue_Potion', 0), ('Dark_Potion', 0), ('Wocky_Slush_Potion', 0),
                                                ('Dirty_Sprite_Potion', 0)"""))
        

    return "OK"

