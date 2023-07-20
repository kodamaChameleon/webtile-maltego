import trio
from maltego_trx.maltego import MaltegoTransform, MaltegoMsg
from maltego_trx.transform import DiscoverableTransform
from extensions import registry
import requests
import os
from bs4 import BeautifulSoup
from hashlib import sha256

def get_image_data_from_url(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching the URL: {e}")
        return

    soup = BeautifulSoup(response.content, "html.parser")
    images = soup.find_all("img")

    image_data_list = []
    for img in images:
        src = img.get("src", "")
        alt = img.get("alt", "")
        file_name = os.path.basename(src)
        image_type = os.path.splitext(file_name)[1].strip(".")
        image_hash = sha256(src.encode()).hexdigest()

        image_data = {
            "hash": image_hash,
            "alt_text": alt,
            "src": src,
            "file_name": file_name,
            "type": image_type
        }
        image_data_list.append(image_data)

    return image_data_list


@registry.register_transform(
    display_name="Scrape images [webtile]", 
    input_entity="maltego.URL",
    description='Returns images from a website using webtile scraper',
    settings=[],
    output_entities=["maltego.Image"]
    )
class imgFromURL(DiscoverableTransform):
    
    @classmethod
    def create_entities(cls, request: MaltegoMsg, response: MaltegoTransform):

        async def main():
            url = request.Value

            images = get_image_data_from_url(url)
            for i in images:
                img = response.addEntity("maltego.Image", value = i["hash"])
                img.addProperty("url", value = i["src"])
                img.addProperty("alt", value = i["alt_text"])
                img.addProperty("name", value = i["file_name"])
                img.addProperty("type", value = i["type"])

        trio.run(main) # running our async code in a non-async code