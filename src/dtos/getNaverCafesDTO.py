from pydantic import BaseModel

from src.types.naverCredential import NaverCredential

class GetNaverCafesDTO(BaseModel):
    credential: NaverCredential