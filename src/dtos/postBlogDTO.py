from pydantic import BaseModel

from src.types.naverCredential import NaverCredential

class PostBlogDTO(BaseModel):
    credential: NaverCredential
    title: str
    content: object