import trio
from maltego_trx.maltego import MaltegoTransform, MaltegoMsg
from maltego_trx.transform import DiscoverableTransform
from extensions import registry,webtile_set
import requests
import re

def find_emails(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception if response status is not 2xx (successful)
        webpage_content = response.text

        # Regular expression to find email addresses
        email_regex = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"

        # Find all matches of email addresses in the webpage content
        emails = set(re.findall(email_regex, webpage_content))

        return list(emails)

    except requests.exceptions.RequestException as e:
        # print("Error fetching the URL:", e)
        return []
    except Exception as e:
        # print("An error occurred:", e)
        return []

@registry.register_transform(
    display_name="URL to email address(es) [webtile]", 
    input_entity="maltego.URL",
    description='Scrape url for email addresses',
    settings=[],
    output_entities=["maltego.EmailAddress"],
    transform_set=webtile_set
)
class urlToEmail(DiscoverableTransform):

    @classmethod
    def create_entities(cls, request: MaltegoMsg, response: MaltegoTransform):

        async def main():
            url = request.Value
            emails = find_emails(url)

            for e in emails:
                email_address = response.addEntity("maltego.EmailAddress", value=e)

        trio.run(main)  # running our async code in a non-async code