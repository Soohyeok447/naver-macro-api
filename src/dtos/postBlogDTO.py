from pydantic import BaseModel

from src.customTypes import NaverCredential

class PostBlogDTO(BaseModel):
    credential: NaverCredential
    title: str
    content: object