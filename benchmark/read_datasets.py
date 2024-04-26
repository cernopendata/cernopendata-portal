import requests
from datetime import datetime

size= 500
base_url= "http://127.0.0.1:5000"
#base_url = "http://opendata-dev.cern.ch/"
start=datetime.now()
print(start)
link = f"{base_url}/api/records/?q=&sort=-mostrecent&page=1&size={size}&type=Dataset%3A%3ASimulated"
r = requests.get(link)
data = r.json()

print("Got the request")
#print(data)
print(datetime.now())
num_files = 0
for entry in data['hits']['hits']:
    #print("Checking an entry", end=" ")
    #print(entry)
    for file in entry['metadata']['_files']:
        file_link = f"{base_url}/record/{entry['id']}/files/{file['key']}"
     #   print(".", end ="")
        #print(file_link)
        r = requests.get(file_link)
        num_files +=1
        #print(r.content)
    #print("")

print("DONE")
end=datetime.now()
print(end)
took=end-start
print(f"Took {took} for {num_files} files")