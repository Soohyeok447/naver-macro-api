import random
import pyperclip
import subprocess
import re


from fastapi import FastAPI
from dotenv import load_dotenv

from pydantic import BaseModel
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys


from webdriver_manager.chrome import ChromeDriverManager

import time

from src.dtos import GetNaverCafesDTO
from src.dtos import PostBlogDTO

from src.customTypes import NaverCredential

app = FastAPI()
load_dotenv()

# 네이버 카페id와 게시판메뉴id 배열을 반환합니다.
@app.post("/api/cafes")
async def getNaverCafes(data: GetNaverCafesDTO):
    try:
        # 입력데이터 저장
        id = data.credential.id
        pw = data.credential.pw
            
        if(id and pw):
            print("아이디와 비밀번호를 잘 전달받았습니다...")
            
        # 셀레니움을 크롬 디버깅 모드로 실행시키기 위한 설정
        chrome_debugging_command = "/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222 --user-data-dir='/tmp/chrome_dev_sess'"

        subprocess.Popen(chrome_debugging_command, shell=True)
            
        # Chrome 옵션 설정
        chromeOptions = Options()
        chromeOptions.add_experimental_option("debuggerAddress", "localhost:9222")
        
        # ChromeDriverManager를 사용하여 ChromeService 객체 생성
        service = Service(ChromeDriverManager().install())

        # 생성된 service 객체를 사용하여 Chrome WebDriver 인스턴스 생성
        driver = webdriver.Chrome(service=service, options=chromeOptions)
        
        # 셀레니움을 사용하여 로그인 자동화
        driver.get("https://www.naver.com/")
        time.sleep(3)
        # driver.implicitly_wait(10)
        
        # 성공여부 확인용
        naverButtonExists = False
        
        try:
            # 네이버 로그인 버튼 찾기
            # (로그인이 안되어 있을 때)
            naverLoginButton = driver.find_element(By.CLASS_NAME,"MyView-module__link_login___HpHMW")
            naverButtonExists = True
            print("네이버 로그인 버튼을 찾았습니다... 로그인을 해야 합니다...")
            
        except NoSuchElementException:
            # (로그인이 되어 있을 때)
            naverButtonExists = False
            print("네이버 로그인 버튼을 찾지 못했습니다... 로그인 상태란 뜻입니다...")
            

        # 네이버 로그인 버튼이 존재할 경우 (로그인 안 되어있음)
        if naverButtonExists:            
            # 로그인버튼 눌러서 로그인페이지로 이동
            naverLoginButton.click()
            
            # 로그인 과정 자동화
            try:
                # 요소 가져오기
                idInput = driver.find_element(By.ID, "id")
                pwInput = driver.find_element(By.ID, "pw")
                loginButton = driver.find_element(By.ID, "log.login")
                autoLoginButton = driver.find_element(By.CLASS_NAME,'keep_text')
                
                # 키 흉내를 위한 actionchain 인스턴스 생성
                actions = ActionChains(driver)
                            
                # 자동로그인 버튼 활성화
                autoLoginButton.click()

                # 로그인 input 태그에 입력
                idInput.click()
                pyperclip.copy(id)

                actions.key_down(Keys.COMMAND).send_keys('v').key_up(Keys.CONTROL).perform()
                time.sleep(2)
                
                # 비밀번호 input 태그에 입력
                pwInput.click()
                pyperclip.copy(pw)

                actions.key_down(Keys.COMMAND).send_keys('v').key_up(Keys.CONTROL).perform()     
                time.sleep(2)

                # 로그인 버튼 클릭
                actions.move_to_element(loginButton).perform()
                loginButton.click()
            finally:
                # 로그인 성공 여부 판단
                try:
                    time.sleep(2)  # 실제 작업에 적절한 대기 시간 설정
                    
                    driver.find_element(By.ID, "query")  # 로그인 성공 시 보이는 요소
                except NoSuchElementException:
                    print("검색창 요소를 찾을 수 없습니다... id,pw가 잘못됐거나... 자동입력방지 시스템이 동작해버렸습니다...")
                    return { "result": "실패", "reason": "id,pw가 잘못됐거나 자동입력방지 시스템 동작."}
        
        # 로그인이 됐으니 카페 관리 페이지로 이동
        driver.get("https://section.cafe.naver.com/ca-fe/home/manage-my-cafe/join")

        time.sleep(1)  # 실제 작업에 적절한 대기 시간 설정

        # 수집한 카페 데이터들을 저장할 리스트
        cafeDatas = []
        
        # 카페 관리 페이지 페이지네이션 인덱스
        currentPageIndex = 1 # 현재 탐색중인 페이지 인덱스
        
        # 접근 금지 카페인지 여부
        inAccessible = False

        # 카페 데이터 추출 시작
        while True:
            time.sleep(3)
            
            # 현재 페이지의 카페 목록 요소 수집
            cafeNames = driver.find_elements(By.CLASS_NAME, 'cafe_name')
            
            time.sleep(2)
            
            # 한 페이지의 카페들의 링크 리스트
            cafeUrls = [cafeName.get_attribute('href') for cafeName in cafeNames]

            for cafeUrl in cafeUrls:
            # for cafe in cafes:
                driver.get(cafeUrl)
                
                time.sleep(2)  # 페이지 로드 대기
                
                # 접근 금지된 카페인지 확인
                try:
                    driver.find_element(By.XPATH, '//img[@alt="이 카페는 접근하실 수 없습니다."]')                
                    inAccessible = True
                    print("접근 제한된 카페입니다...")
                except NoSuchElementException:
                    inAccessible = False

                if inAccessible:
                    continue
                
                # cafeData 딕셔너리 초기화
                cafeData = {
                    "id": "",
                    "url": "",
                    "name": "",
                    "menus": []
                }
                
                ### 카페 이름 추출            
                cafeName = driver.find_element(By.CSS_SELECTOR, "h1.d-none")
                cafeData["name"] = cafeName.text
                print(cafeData["name"])

                ### 카페 URL 추출
                cafeData["url"] = cafeUrl
                print(cafeData["url"])
                
                    
                ### g_sClubId 값 추출
                # 특정 요소를 찾음 (여기서는 innerText가 "전체글보기"인 a 태그)
                viewAllPostsElement = driver.find_element(By.XPATH, "//a[contains(text(),'전체글보기')]")

                # 요소에서 href 속성 값을 가져옴
                viewAllPostsElementHref = viewAllPostsElement.get_attribute("href")

                # href 속성에서 'clubid' 값을 추출하기 위한 정규 표현식 패턴
                clubIdRegExp = "clubid=(\d+)"

                # href 속성에서 패턴 매칭
                match = re.search(clubIdRegExp, viewAllPostsElementHref)
                
                if match:
                    cafeData["id"] = match.group(1)
                else:
                    print("clubId를 찾을 수 없습니다..")
                    
                print(cafeData["id"])
                
                ### 접혀있는 메뉴 리스트들 전부 열기
                try:
                    downBtns = driver.find_elements(By.CLASS_NAME, 'down-btn')
                    
                    print('downBtn의 갯수 -> '+str(len(downBtns)))
                    
                    # 요소가 1개인 경우, 아무것도 하지 않음
                    if len(downBtns) <= 1:
                        print("접힌 메뉴가 없습니다...")
                        pass
                    
                    # 요소가 2개 이상인 경우, 두 번째 요소부터 클릭
                    else:
                        for btn in downBtns[1:]:
                            btn.click()
                            time.sleep(0.3)
                except NoSuchElementException:
                    print("downBtns 못찾았습니다... 결단내립니다...")
                    return { "result": "실패", "reason": "downBtns못찾는 버그가 발생했기에 빨리 재시작을 하기위한 결단"}
                
                ### 메뉴id - 이름 수집
                # 'cafe-menu-list' 클래스를 가진 ul 태그 찾기 및 순환
                menu_lists = driver.find_elements(By.CLASS_NAME, 'cafe-menu-list')
                for menu_list in menu_lists:
                    menu_items = menu_list.find_elements(By.TAG_NAME, 'li')
                    for menu_item in menu_items:
                        cafeMenu = {
                            "id": "",
                            "name": ""
                        }
                        
                        link = menu_item.find_element(By.TAG_NAME, 'a')
                                            
                        # 메뉴 링크의 href 속성
                        menuHref = link.get_attribute('href')
                        
                        
                        # href 속성 search.menuid 값을 추출하기 위한 정규표현식
                        menuIdRegExp = "menuid=(\d+)"
                        
                        # 정규표현식 매칭
                        match = re.search(menuIdRegExp, menuHref)
                        
                        if match:
                            cafeMenu["id"] = match.group(1) # 카페 메뉴 id
                            cafeMenu["name"] = link.text # 카페 메뉴 이름
                            
                            # print(cafeMenu)
                            
                            if(cafeMenu["name"] != ''):
                                cafeData["menus"].append(cafeMenu) # cafeData에 메뉴 추가
                        else:
                            # print("menuId를 찾을 수 없습니다..")
                            pass
                

                
                cafeDatas.append(cafeData)
                print("카페 하나 검색 완료했습니다...") 
                # print(cafeData)
                
            # 페이지네이션을 위한 pageIndex + 1
            currentPageIndex += 1
            
            # 다음 페이지로 이동
            driver.get("https://section.cafe.naver.com/ca-fe/home/manage-my-cafe/join")

            time.sleep(3)

            # 페이지네이션 요소들 검색
            pageItems = driver.find_elements(By.CLASS_NAME, "page_item")
            
            # 1, 2와 같이 정수 innerText가 있는 요소들만 선택
            pageItemsWithDigitText = [int(item.text) for item in pageItems if item.text.strip().isdigit()]
            
            time.sleep(3)
            
            print('현재 페이지 인덱스입니다... -> ' + str(currentPageIndex))
            
            # 마지막 페이지 인덱스
            lastPageIndex = max(pageItemsWithDigitText) if pageItemsWithDigitText else None

            print('lastPageIndex -> ' + str(lastPageIndex))
            
            print("마지막 인덱스인지 확인합니다...")
            if currentPageIndex > lastPageIndex:  # 현재 인덱스가 마지막 인덱스보다 크다면 반복문 탈출
                print("마지막 인덱스였습니다... 다음 페이지들이 더 있나 확인합니다...")

                # 페이지네이션의 다음버튼이 활성화 되어있는지 여부
                nextButton = driver.find_element(By.CLASS_NAME, "page_item.next")
                nextButtonDisplayStyle = nextButton.value_of_css_property("display")

                # nextButton의 style이 none이 아니면 클릭합니다.
                if nextButtonDisplayStyle != "none":
                    print("다음 페이지가 더 있습니다... 계속 진행합니다...")
                    nextButton.click()
                    
                    time.sleep(2) # 페이지 로딩 대기
                else:
                    # 다음 페이지로 넘기는 요소가 없으면 반복 종료
                    print("전부 검색 했습니다... ")
                    break
            
            print("마지막 인덱스가 아닙니다...")
            for item in pageItems:
                if item.text == str(currentPageIndex):
                    print("현재 페이지와 같은 버튼을 찾았습니다. -> " + item.text)
                    item.click()
                    break            
            
            
        return { "result" : "성공", "data": cafeDatas }
    except Exception as e:
        return { "result" : "실패", "reason": "예상치 못한 에러...", "error": e}
        


#TODO 네이버 블로그에 게시물을 게시합니다.
@app.post("/api/blog/article")
async def postBlog(data: PostBlogDTO):
    id = data.credential.id
    pw = data.credential.pw
    title = data.title
    content = data.content
    
    return {"result": "성공"}


@app.post("/test")
async def test():
    chrome_debugging_command = "/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222 --user-data-dir='/tmp/chrome_dev_sess'"

    subprocess.Popen(chrome_debugging_command, shell=True)
    
    # Chrome 옵션 설정
    chromeOptions = Options()
    chromeOptions.add_experimental_option("debuggerAddress", "localhost:9222")
    
    # ChromeDriverManager를 사용하여 ChromeService 객체 생성
    service = Service(ChromeDriverManager().install())

    # 생성된 service 객체를 사용하여 Chrome WebDriver 인스턴스 생성
    driver = webdriver.Chrome(service=service, options=chromeOptions)
    
    driver.get("https://www.afreecatv.com/")
    
    inputTag = driver.find_element(By.ID, "szKeyword")

    inputTag.click()
    inputTag.send_keys(Keys.COMMAND, 'v')
    
    inputTag.send_keys('pyperclip 테스트용이에용')
    
    inputTag.send_keys(Keys.ENTER)        
    
    time.sleep(5)
    
    return {"result": '안녕하세용'}
