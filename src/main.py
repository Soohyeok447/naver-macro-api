from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
from src.dtos.getNaverCafesDTO import GetNaverCafesDTO
from src.dtos.postBlogDTO import PostBlogDTO

from src.types.naverCredential import NaverCredential

app = FastAPI()

# 네이버 카페id와 게시판메뉴id 배열을 반환합니다.
@app.post("/cafes")
async def getNaverCafes(data: GetNaverCafesDTO):
    id = data.credential.id
    pw = data.credential.pw
    


#TODO 네이버 블로그에 게시물을 게시합니다.
@app.post("/blog")
async def postBlog(data: PostBlogDTO):
    id = data.credential.id
    pw = data.credential.pw
    title = data.title
    content = data.content
    
    return {"result": "Success"}


@app.get("/test")
async def test():
    return {"result": '안녕하세용'}
