import trio
from maltego_trx.maltego import MaltegoTransform, MaltegoMsg
from maltego_trx.transform import DiscoverableTransform
from extensions import registry
import requests
from PIL import Image
import imagehash
from io import BytesIO

@registry.register_transform(
    display_name="Hash image [webtile]", 
    input_entity="maltego.Image",
    description='Returns perceptual hash of an image',
    settings=[],
    output_entities=["maltego.hashtag"]
)
class imgToHash(DiscoverableTransform):

    @classmethod
    def create_entities(cls, request: MaltegoMsg, response: MaltegoTransform):

        async def main():
            src = request.Value

            # Download the image
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
            }
            image_response = requests.get(src, headers=headers)
            image_response.raise_for_status()
            image = Image.open(BytesIO(image_response.content))

            # Resize the image to a fixed size
            target_size = (128, 128)  # Adjust the target size as needed
            image = image.resize(target_size, Image.ANTIALIAS)

            # Calculate the Average Hash
            image_hash = str(imagehash.average_hash(image))

            hash_entity = response.addEntity("maltego.hashtag", value=image_hash)

        trio.run(main)  # running our async code in a non-async code