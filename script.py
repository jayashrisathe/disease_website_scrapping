import requests
from bs4 import BeautifulSoup
import xlsxwriter
import logging

URL = ("https://www.agriculture.gov.au/pests-diseases-weeds/plant#identify-pests-diseases")
WEB_DOMAIN = "https://www.agriculture.gov.au"


logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(message)s",
    handlers=[logging.StreamHandler()],
)


workbook = xlsxwriter.Workbook("disease_data.xlsx")
TITLES = ["Disease Name", "Disease Origin", "Image Link", "Pest"]
worksheet = workbook.add_worksheet()
for i, el in enumerate(TITLES):
    worksheet.write(0, i, el)


def get_image_src(soup):
    image_div = soup.find("div", class_="pest-header-image")
    try:
        img = [f"{WEB_DOMAIN}{img.get('src')}" for img in image_div.findAll("img")][0]
    except Exception:
        return ""
    return img


def get_origin(soup):
    origin = ""
    disease_content = soup.find_all("div", class_="pest-header-content")
    for content in disease_content:
        for strong_tag in content.find_all("strong"):
            if strong_tag.text.find("Where") != -1:
                for sib in strong_tag.next_siblings:
                    if "<strong>" in str(sib):
                        break
                    sub_str = str(sib).strip().replace("<br/>", "")
                    if sub_str:
                        origin += sub_str
    return origin


def get_pest(soup):
    pest_div = soup.find_all("div", class_="fact-sheet-label")
    try:
        pest = [p.find("p").text for p in pest_div][0]
    except IndexError:
        return ""
    return pest


def write_in_exel(index, disease_name, origin, image_src, pest):
    worksheet.write(index + 1, 0, disease_name)
    worksheet.write(index + 1, 1, origin)
    worksheet.write(index + 1, 2, image_src)
    worksheet.write(index + 1, 3, pest)


if __name__ == "__main__":
    page = requests.get(URL)
    soup = BeautifulSoup(page.content, "html.parser")
    results = soup.find(id="collapsefaq")
    job_elements = results.find_all("li", class_="flex-item")
    for index, job_element in enumerate(job_elements):
        disease_name = (
            job_element.contents[1].text
            if len(job_element.contents) == 2
            else job_element.contents[0].text
        )
        logging.debug(f"\nFetching the data for disease: {disease_name}")
        sub_url = [a["href"] for a in job_element.select("a[href]")][0]
        if sub_url[-4:-1] == "pdf":
            continue
        disease_response = requests.get(f"{WEB_DOMAIN}{sub_url}")
        disease_response_soup = BeautifulSoup(disease_response.content, "html.parser")
        pest = get_pest(disease_response_soup)
        origin = get_origin(disease_response_soup)
        image_src = get_image_src(disease_response_soup)
        write_in_exel(index, disease_name, origin, image_src, pest)
    workbook.close()
