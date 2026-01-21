import requests
import xml.etree.ElementTree as ET

BASE_URL = "https://opendata.cern.ch/oai2d"
NAME_SPACE = {"oai": "http://www.openarchives.org/OAI/2.0/"}


def fetch_records(url, params=None):
    """Fetch XML data from the OAI-PMH endpoint."""
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.text


def count_records(base_element):
    """Count the number of <record> elements in the XML."""
    records = base_element.findall(".//oai:record", NAME_SPACE)
    return len(records)


def get_resumption_token(base_element):
    """Extract the resumptionToken if it exists."""
    token_el = base_element.find(".//oai:resumptionToken", NAME_SPACE)
    if token_el is not None and token_el.text:
        return token_el.text.strip()
    return None


def main():
    params = {
        "verb": "ListRecords",
        "set": "openaire_data",
        "metadataPrefix": "oai_openaire",
    }
    total_records = 0

    while True:
        xml_text = fetch_records(BASE_URL, params)
        base_element = ET.fromstring(xml_text)
        batch_count = count_records(base_element)
        total_records += batch_count

        print(f"Records in this batch: {batch_count}")
        print(f"Cumulative total: {total_records}")

        token = get_resumption_token(base_element)
        if not token:
            print("No more resumption token. Finished fetching all records.")
            break

        # Use resumptionToken for the next request
        params = {"verb": "ListRecords", "resumptionToken": token}


if __name__ == "__main__":
    main()
