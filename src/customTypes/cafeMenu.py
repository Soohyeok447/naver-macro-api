from pydantic import BaseModel
from typing import List

class CafeMenu(BaseModel):
    id: str
    name: str