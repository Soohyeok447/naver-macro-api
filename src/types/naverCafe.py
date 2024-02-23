from pydantic import BaseModel
from typing import List

class NaverCafe(BaseModel):
    id: str
    menuIds: List[str]