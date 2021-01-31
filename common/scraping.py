from selenium import webdriver
import urllib.request
import boto3, re

errCount = 0


def kartScraping(pageNo):
    dynamodb = boto3.resource(
        "dynamodb",
    )
    listLink = "https://kart.nexon.com/Kart/News/Patch/List.aspx?n4pageno=" + str(pageNo)
    driver = webdriver.Chrome("./chromedriver")
    driver.get(listLink)

    # 게시판 날짜별 패치 목록
    patchListElements = driver.find_elements_by_xpath('//*[@id="kart_main_sections"]//tbody//a')
    patchDateListElements = driver.find_elements_by_xpath('//*[@class="list_td day"]')
    patchList = []

    for index, val in enumerate(patchListElements):
        href = val.get_attribute("href")
        text = val.get_attribute("text")
        patchDate = patchDateListElements[index].text
        patchList.append([text, href, patchDate])

    # print(patchList)

    for patch in patchList:
        link = patch[1]  # 세부사항 링크.
        driver.get(link)  # 링크 진입
        try:
            stringElement = driver.find_element_by_xpath('//*[@class="board_imgarea"]')
            noticeString = stringElement.text  # 게시글 내용 전부 긁어옴

            thumbnailElements = driver.find_elements_by_xpath('//*[@class="board_imgarea"]//img')
            thumbnailSrc = ""
            if len(thumbnailElements) > 0:
                thumbnailSrc = thumbnailElements[0].get_attribute("src")
            else:
                thumbnailSrc = "no imgs"

            # subjectElements = driver.find_elements_by_xpath(
            #     '//*[@class="board_imgarea"]//table'
            # )  # 이미지보더에 있는 공지사항
            # subjectList = []
            # for subjectElement in subjectElements:
            #     subject = subjectElement.text
            #     subjectList.append(subject)

            subjectExpresion = re.compile("\d[.].*\n")
            subjectList = list(
                map(lambda subject: subject.strip("\n"), subjectExpresion.findall(noticeString))
            )

            patch_contents = []
            patch_content = []
            subject_num = 0
            patchTime = noticeString.split("일정]")[1].split("\n")[1].split("\n")[0].strip("- ")
            for idx, line in enumerate(noticeString.splitlines()):
                if subjectList[subject_num] in line:
                    if subject_num != 0:
                        patch_contents.append(patch_content)
                        patch_content = []
                    if subject_num < len(subjectList) - 1:
                        subject_num += 1
                if "▶" in line:
                    patch_content.append(line.strip())
                if idx == len(noticeString.splitlines()) - 1:
                    patch_contents.append(patch_content)

            patchData = list(
                map(
                    lambda subject: {
                        "patch_subject": subject[1],
                        "patch_content": patch_contents[subject[0]],
                    },
                    tuple(enumerate(subjectList)),
                )
            )
            data = {
                "dataType": "kart",
                "notification_id": int(patch[1].split("n4articlesn=")[-1]),
                "date": patch[2],
                "thumbnail_src": thumbnailSrc,
                "subject": patch[0],
                "content": {"patch_list": patchData},
                "patchTime": patchTime,
            }
            print(data)

            table = dynamodb.Table("gamePatchBot")
            print(table.creation_date_time)
            table.put_item(Item=data)
        except Exception as ex:
            global errCount
            print("error: ", ex, "page: ", patch[1])
            errCount += 1
            pass

    driver.quit()

    return


def kartMigration():
    global errCount
    for target in range(8, 25):
        kartScraping(target)
    print("errCount:", errCount)


