from pydantic import BaseModel

from src.customTypes import NaverCredential

class GetNaverCafesDTO(BaseModel):
    credential: NaverCredential