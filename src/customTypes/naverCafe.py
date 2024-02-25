from pydantic import BaseModel
from typing import List

from .cafeMenu import CafeMenu

class NaverCafe(BaseModel):
    id: str
    name: str
    url: str
    menus: List[CafeMenu]
    
    
