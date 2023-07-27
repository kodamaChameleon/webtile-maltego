import subprocess
import json
import re
import requests
import io

# Install required python dependencies
def install_requirements():
    subprocess.check_call(['pip', 'install', '-r', 'requirements.txt'])

# Build config file for easy importation
def build_config():
    subprocess.check_call(['python3', 'project.py', 'list'])

def create_regex_file(url, output_file):
    try:
        # Download JSON data from the URL
        response = requests.get(url)
        if response.status_code == 200:
            # Load JSON data from the response content
            data = json.load(io.StringIO(response.content.decode('utf-8')))

            if 'sites' in data:
                sites = data['sites']
                regex_list = []

                for site in sites:
                    if 'uri_check' in site:
                        uri_check = site['uri_check']
                        # Remove 'https://' or 'http://' from the URL
                        uri_check = re.sub(r'^https?://', '', uri_check)
                        account_regex = re.sub(r'{account}', r'([A-Za-z0-9_.]+)', uri_check)
                        regex_list.append(account_regex)

                # Prepare the final JSON data
                output_data = {
                    "credit": {
                        "App": "WhatsMyName",
                        "URL": url,
                        "License": data.get("license", ""),
                        "authors": data.get("authors", ""),
                        "Edited By": "KodamaChameleon",
                    },
                    "regex": regex_list
                }

                with open(output_file, 'w') as out_file:
                    json.dump(output_data, out_file, indent=4)

                print(f"Regular expressions written to '{output_file}'.")
            else:
                print("Error: 'sites' key not found in the JSON data.")
        else:
            print(f"Error: Unable to fetch data from the URL. Status code: {response.status_code}")

    except json.JSONDecodeError:
        print(f"Error: Unable to parse the JSON data from the URL.")
    except Exception as e:
        print(f"Error: An unexpected error occurred - {e}.")

if __name__ == '__main__':
    install_requirements()
    create_regex_file("https://raw.githubusercontent.com/WebBreacher/WhatsMyName/main/wmn-data.json", "regex.json")
    build_config()

    
