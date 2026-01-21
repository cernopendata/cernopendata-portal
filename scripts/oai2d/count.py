import requests
import xml.etree.ElementTree as ET

BASE_URL = "https://opendata-dev.cern.ch/oai2d"
BASE_URL = "https://opendata.cern.ch/oai2d"
METADATA_PREFIX = "oai_dc"

def fetch_records(url, params=None):
    """Fetch XML data from the OAI-PMH endpoint."""
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.text

def count_records(xml_text):
    """Count the number of <record> elements in the XML."""
    root = ET.fromstring(xml_text)
    ns = {'oai': 'http://www.openarchives.org/OAI/2.0/'}
    records = root.findall('.//oai:record', ns)
    return len(records)

def get_resumption_token(xml_text):
    """Extract the resumptionToken if it exists."""
    root = ET.fromstring(xml_text)
    ns = {'oai': 'http://www.openarchives.org/OAI/2.0/'}
    token_el = root.find('.//oai:resumptionToken', ns)
    if token_el is not None and token_el.text:
        return token_el.text.strip()
    return None

def main():
    params = {'verb': 'ListRecords', 'metadataPrefix': METADATA_PREFIX, 'set':'openaire_data', 'metadataPrefix':'oai_openaire'}
    total_records = 0

    while True:
        xml_text = fetch_records(BASE_URL, params)
        batch_count = count_records(xml_text)
        total_records += batch_count

        print(f"Records in this batch: {batch_count}")
        print(f"Cumulative total: {total_records}")

        token = get_resumption_token(xml_text)
        if not token:
            print("No more resumption token. Finished fetching all records.")
            break

        # Use resumptionToken for the next request
        params = {'verb': 'ListRecords', 'resumptionToken': token}

if __name__ == "__main__":
    main()
