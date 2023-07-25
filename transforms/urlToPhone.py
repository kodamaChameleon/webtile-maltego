import trio
from maltego_trx.maltego import MaltegoTransform, MaltegoMsg
from maltego_trx.transform import DiscoverableTransform
from extensions import registry
import requests
from bs4 import BeautifulSoup
import re

# Check for keywords for 10 digit format without separators
def phone_keyword(number, soup):
    # Check for words "mobile," "phone," or "call" in the element or parent element of each regex match
    keywords = ["mobile", "phone", "call", "tel"]
    found_keyword = False
    element_containing_phone = soup.find(text=re.compile(re.escape(number)))
    if element_containing_phone:
        for keyword in keywords:
            if keyword in element_containing_phone.lower() or keyword in element_containing_phone.parent.text.lower():
                found_keyword = True
                break
    
    return found_keyword

def find_phone_numbers(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception if response status is not 2xx (successful)
        webpage_content = response.text

        # Use BeautifulSoup to parse the HTML content
        soup = BeautifulSoup(webpage_content, "html.parser")

        # Updated regular expressions to find phone numbers in various formats
        phone_regexes = [
            r"\+1\d{10}",                   # +1XXXXXXXXXX (E.164 format)
            r"\b\d{10}\b",                   # XXXXXXXXXX (10-digit format without any separators)
            r"\+\d{1,2}\s?\(\d{2,3}\)\s?\d{3}-\d{4}",  # +XX (XXX) XXX-XXXX
            r"\(\d{3}\)\s?\d{3}-\d{4}",      # (XXX) XXX-XXXX
            r"\b\d{3}-\d{3}-\d{4}\b",        # XXX-XXX-XXXX
            r"\b\d{3}\.\d{3}\.\d{4}\b"       # XXX.XXX.XXXX
        ]

        # Find all matches of the phone number regexes in the webpage content
        phone_numbers = set()
        for phone_regex in phone_regexes:
            phone_matches = re.findall(phone_regex, webpage_content)
            for match in phone_matches:

                # Double check for other indicators of phone number for common false positives
                if phone_regex in [r"\b\d{10}\b"]:
                    if phone_keyword(match, soup):
                        phone_numbers.add(re.sub(r'\D', '', match))
                else:
                    phone_numbers.add(re.sub(r'\D', '', match))

        return list(phone_numbers)

    except requests.exceptions.RequestException as e:
        #print("Error fetching the URL:", e)
        return []
    except Exception as e:
        #print("An error occurred:", e)
        return []

@registry.register_transform(
    display_name="URL to phone number(s) [webtile]", 
    input_entity="maltego.URL",
    description='Scrape url for phone numbers',
    settings=[],
    output_entities=["maltego.PhoneNumber"]
)
class urlToPhone(DiscoverableTransform):

    @classmethod
    def create_entities(cls, request: MaltegoMsg, response: MaltegoTransform):

        async def main():
            url = request.Value
            numbers = find_phone_numbers(url)

            for n in numbers:
                phone_number = response.addEntity("maltego.PhoneNumber", value=n)
                phone_number.addProperty("phonenumber.areacode", value = n[-10:-7])
                phone_number.addProperty("phonenumber.lastnumbers", value = n[-7:])
                if len(n) > 10:
                    phone_number.addProperty("phonenumber.countrycode", value = "+" + n[:-10])

        trio.run(main)  # running our async code in a non-async code