import trio
from maltego_trx.maltego import MaltegoTransform, MaltegoMsg
from maltego_trx.transform import DiscoverableTransform
from extensions import registry,webtile_set
import requests
from bs4 import BeautifulSoup
import re
import json

# Function to extract domain name from a URL
def extract_domain(original_regex):
    domain_extract_regex = r"(https?://)?([A-Za-z0-9_.-]+)"
    match = re.match(domain_extract_regex, original_regex)
    if match:
        return match.group(2)
    return None

# WhatsMyName reverselookup :)
def find_alias(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception if response status is not 2xx (successful)
        webpage_content = response.text

        # Use BeautifulSoup to parse the HTML content
        soup = BeautifulSoup(webpage_content, "html.parser")

        # Load handle regexes from the JSON file
        with open("regex.json", "r") as file:
            handle_regexes = json.load(file)["regex"]

        # Append additional regexes to the list not covered by 
        handle_regexes.extend([
                               r"facebook.com/([A-Za-z0-9_.]+)",
                               r"twitter.com/([A-Za-z0-9_.]+)",
                            ])

        # Find all matches of the handle regexes in the webpage content
        social_media_handles = {}
        for handle_regex in handle_regexes:
            handle_matches = re.findall(handle_regex, webpage_content)
            for match in handle_matches:
                if match in social_media_handles:
                    if handle_regex not in social_media_handles[match]:
                        social_media_handles[match].append(extract_domain(handle_regex))
                else:
                    social_media_handles[match] = [extract_domain(handle_regex)]

        return social_media_handles

    except requests.exceptions.RequestException as e:
        #print("Error fetching the URL:", e)
        return {}
    except Exception as e:
        #print("An error occurred:", e)
        return {}

@registry.register_transform(
    display_name="URL to alias [webtile]", 
    input_entity="maltego.URL",
    description='Scrape url for alias (aka. reverse WhatsMyName lookup)',
    settings=[],
    output_entities=["maltego.Alias"],
    transform_set=webtile_set
)
class urlToAlias(DiscoverableTransform):

    @classmethod
    def create_entities(cls, request: MaltegoMsg, response: MaltegoTransform):

        async def main():
            url = request.Value
            alias = find_alias(url)

            for a in alias:
                alias_name = response.addEntity("maltego.Alias", value=a)
                for d in alias[a]:
                    alias_name.addProperty(d, value = a)

        trio.run(main)  # running our async code in a non-async code