import trio
from maltego_trx.maltego import MaltegoTransform, MaltegoMsg
from maltego_trx.transform import DiscoverableTransform
from extensions import registry,webtile_set
import requests
from bs4 import BeautifulSoup
import re
import json

# Check for keywords related to social media handles
def social_media_keyword(handle, soup):
    keywords = [
        "twitter",
        "instagram",
        "facebook",
        "tiktok",
        "threads",
        "snapchat",
        "linkedin",
        "youtube",
        "pinterest",
        "reddit",
        "twitch",
        "discord",
        "tumblr",
        "vimeo",
        "whatsapp",
        "telegram",
        "wechat",
        "flickr",
        "spotify",
        "soundcloud",
        "bandcamp",
        "mixcloud",
        "dribbble",
        "behance",
        "patreon",
        "stackoverflow",
    ]
    found_keyword = False
    element_containing_handle = soup.find(text=re.compile(re.escape(handle)))
    if element_containing_handle:
        for keyword in keywords:
            if keyword in element_containing_handle.lower() or keyword in element_containing_handle.parent.text.lower():
                found_keyword = True
                break

    return found_keyword

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

        # Append additional regexes to the list
        handle_regexes.extend([r"@([A-Za-z0-9_]+)",
                               r"\\$([A-Za-z0-9_]+)",
                                r"facebook.com/([A-Za-z0-9_.]+)",
                               ])

        # Find all matches of the handle regexes in the webpage content
        social_media_handles = set()
        for handle_regex in handle_regexes:
            handle_matches = re.findall(handle_regex, webpage_content)
            for match in handle_matches:
                # Double check for other indicators of social media handles for generic handles
                if handle_regex in [r"@([A-Za-z0-9_]+)", r"\\$([A-Za-z0-9_]+)"]:
                    if social_media_keyword(match, soup):
                        social_media_handles.add(match)
                else:
                    social_media_handles.add(match)

        return list(social_media_handles)

    except requests.exceptions.RequestException as e:
        #print("Error fetching the URL:", e)
        return []
    except Exception as e:
        #print("An error occurred:", e)
        return []

@registry.register_transform(
    display_name="URL to alias [webtile]", 
    input_entity="maltego.URL",
    description='Scrape url for alias',
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

        trio.run(main)  # running our async code in a non-async code