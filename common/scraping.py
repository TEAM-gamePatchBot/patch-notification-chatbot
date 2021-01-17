from selenium import webdriver
import urllib.request


def kartScraping():
    driver = webdriver.Chrome("./chromedriver")
    driver.get("https://kart.nexon.com/Kart/News/Patch/List.aspx?n4pageno=1")

    patchListElements = driver.find_elements_by_xpath('//*[@id="kart_main_sections"]//tbody//a')
    patchList = []

    for i in patchListElements:
        href = i.get_attribute("href")
        text = i.get_attribute("text")
        patchList.append([text, href])

    print(patchList)

    subjectLists = []
    for i in patchList:
        link = i[1]
        driver.get(link)

        stringElement = driver.find_element_by_xpath('//*[@class="board_imgarea"]')
        noticeString = stringElement.text
        print(noticeString)
        patchTime = noticeString.split("일정]\n")[1].split("\n")[0].split("-")[1]

        subjectElements = driver.find_elements_by_xpath('//*[@class="board_imgarea"]//table')
        subjectList = []

        subjectList.append(patchTime)

        for j in subjectElements:
            subject = j.text
            subjectList.append(subject)

        subjectLists.append(subjectList)
    print(subjectLists)
    driver.quit()
    return subjectLists

