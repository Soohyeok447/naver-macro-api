from pydantic import BaseModel

class NaverCredential(BaseModel):
    id: str
    pw: str