import trio
from maltego_trx.maltego import MaltegoTransform, MaltegoMsg
from maltego_trx.transform import DiscoverableTransform
from extensions import registry,webtile_set
import requests
import re
from datetime import datetime

def standardize_datetime(dt_str):
    try:
        # List of possible datetime formats to parse the input string
        datetime_formats = [
            "%m/%d/%Y %I:%M %p",      # MM/DD/YYYY [HH:MM AM/PM]
            "%m/%d/%Y %I:%M%p",       # MM/DD/YYYY [HH:MMAM/PM]
            "%m/%d/%Y",               # MM/DD/YYYY
            "%m-%d-%Y %I:%M %p",      # MM-DD-YYYY [HH:MM AM/PM]
            "%m-%d-%Y %I:%M%p",       # MM-DD-YYYY [HH:MMAM/PM]
            "%m-%d-%Y",               # MM-DD-YYYY
            "%m.%d.%Y %I:%M %p",      # MM.DD.YYYY [HH:MM AM/PM]
            "%m.%d.%Y %I:%M%p",       # MM.DD.YYYY [HH:MMAM/PM]
            "%m.%d.%Y",               # MM.DD.YYYY
            "%d %b %Y %I:%M %p",      # DD MMM YYYY [HH:MM AM/PM]
            "%d %b %Y %I:%M%p",       # DD MMM YYYY [HH:MMAM/PM]
            "%d %b %Y",               # DD MMM YYYY
            "%b %d, %Y %I:%M %p",     # MMM DD, YYYY [HH:MM AM/PM]
            "%b %d, %Y %I:%M%p",      # MMM DD, YYYY [HH:MMAM/PM]
            "%b %d, %Y",              # MMM DD, YYYY
            "%Y-%m-%d %I:%M %p",      # YYYY-MM-DD [HH:MM AM/PM]
            "%Y-%m-%d %I:%M%p",       # YYYY-MM-DD [HH:MMAM/PM]
            "%Y-%m-%d",               # YYYY-MM-DD
            "%d %b, %Y %I:%M %p",     # D MMM, YYYY [HH:MM AM/PM]
            "%d %b, %Y %I:%M%p",      # D MMM, YYYY [HH:MMAM/PM]
            "%d %b, %Y",              # D MMM, YYYY
            "%b %d %Y %I:%M %p",      # MMM D YYYY [HH:MM AM/PM]
            "%b %d %Y %I:%M%p",       # MMM D YYYY [HH:MMAM/PM]
            "%b %d %Y",               # MMM D YYYY
            "%B %d, %Y %I:%M %p",     # Month DD, YYYY [HH:MM AM/PM]
            "%B %d, %Y %I:%M%p",      # Month DD, YYYY [HH:MMAM/PM]
            "%B %d, %Y",              # Month DD, YYYY
        ]

        # Attempt to parse the input datetime string using the available formats
        for dt_format in datetime_formats:
            try:
                dt_obj = datetime.strptime(dt_str, dt_format)
                # If the parsing succeeds, return the datetime object
                standardized_format = "%Y-%m-%d"
                if re.search(r"\d{1,2}:\d{2}", dt_str):
                    standardized_format += " %H:%M"
                return dt_obj.strftime(standardized_format)
            except ValueError:
                pass

        # If none of the formats match, return dt_str
        return dt_str

    except Exception as e:
        print("An error occurred during datetime standardization:", e)
        return dt_str

def find_datetime(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception if response status is not 2xx (successful)
        webpage_content = response.text

        # Regular expression to find dates with optional timestamps (with or without time and AM/PM)
        datetime_regexes = [
            r"\d{1,2}/\d{1,2}/\d{4}(?:\s\d{1,2}:\d{2}(?:\s?[apAP][mM])?)?",      # MM/DD/YYYY [HH:MM AM/PM]
            r"\d{1,2}-\d{1,2}-\d{4}(?:\s\d{1,2}:\d{2}(?:\s?[apAP][mM])?)?",      # MM-DD-YYYY [HH:MM AM/PM]
            r"\d{1,2}\.\d{1,2}\.\d{4}(?:\s\d{1,2}:\d{2}(?:\s?[apAP][mM])?)?",    # MM.DD.YYYY [HH:MM AM/PM]
            r"\d{1,2}\s[a-zA-Z]{3}\s\d{4}(?:\s\d{1,2}:\d{2}(?:\s?[apAP][mM])?)?", # DD MMM YYYY [HH:MM AM/PM]
            r"[a-zA-Z]{3,9}\s\d{1,2},\s\d{4}(?:\s\d{1,2}:\d{2}(?:\s?[apAP][mM])?)?",  # MMM DD, YYYY [HH:MM AM/PM]
            r"\d{4}-\d{1,2}-\d{1,2}(?:\s\d{1,2}:\d{2}(?:\s?[apAP][mM])?)?",        # YYYY-MM-DD [HH:MM AM/PM]
            r"\d{1,2}\s[a-zA-Z]{3},\s\d{4}(?:\s\d{1,2}:\d{2}(?:\s?[apAP][mM])?)?",  # D MMM, YYYY [HH:MM AM/PM]
            r"[a-zA-Z]{3}\s\d{1,2}\s\d{4}(?:\s\d{1,2}:\d{2}(?:\s?[apAP][mM])?)?"   # MMM D YYYY [HH:MM AM/PM]
        ]

        # Find all matches of the datetime regexes in the webpage content
        datetimes = set()
        for dt_regex in datetime_regexes:
            dt_matches = re.findall(dt_regex, webpage_content)
            for match in dt_matches:
                standardized_datetime = standardize_datetime(match)
                if standardized_datetime:
                    datetimes.add(standardized_datetime)

        return list(datetimes)

    except requests.exceptions.RequestException as e:
        # print("Error fetching the URL:", e)
        return []
    except Exception as e:
        # print("An error occurred:", e)
        return []

@registry.register_transform(
    display_name="URL to datetime(s) [webtile]", 
    input_entity="maltego.URL",
    description='Scrape url for dates',
    settings=[],
    output_entities=["maltego.DateTime"],
    transform_set=webtile_set
)
class urlToDate(DiscoverableTransform):

    @classmethod
    def create_entities(cls, request: MaltegoMsg, response: MaltegoTransform):

        async def main():
            url = request.Value
            dates = find_datetime(url)

            for d in dates:
                datetime = response.addEntity("maltego.DateTime", value=d)
                datetime.addProperty("date", value = d[:10])
                datetime.addProperty("year", value = d[:4])
                datetime.addProperty("month", value = d[5:7])
                datetime.addProperty("day", value = d[8:10])
                if len(d) > 10:
                    datetime.addProperty("hour", value = d[11:13])
                    datetime.addProperty("minute", value = d[14:16])

        trio.run(main)  # running our async code in a non-async code