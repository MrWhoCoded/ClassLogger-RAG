from astrapy import DataAPIClient
from langchain_text_splitters import RecursiveCharacterTextSplitter
import fitz
import requests
from pathlib import Path
import json
import re
from time import sleep

ASTRADB_API_KEY = "YOUR_API_KEY"

client = DataAPIClient()
db = client.get_database(
    "https://5c624cdd-cc62-442f-93f4-8ec4efaa2dbf-us-east-2.apps.astra.datastax.com", token=ASTRADB_API_KEY
)

collection = db.get_collection("classloggertest")

with open(r"data\processed.json") as f:
    data = json.load(f)

subdirs = [p for p in Path("data").iterdir() if p.is_dir()]

splitter = RecursiveCharacterTextSplitter(
    chunk_size = 800,
    chunk_overlap = 100
)

def pdf_to_text(file):
    text = ""
    
    doc = fitz.open(file)
    for page in doc:
        text = text + page.get_text()
        
    return text

for s in subdirs:
    for file in [f for f in Path(s).iterdir() if f.is_file()]:
        documents = []
        if file.name not in data.keys() or not data[file.name]:
            text = pdf_to_text(file)
            
            chunks = splitter.split_text(text)
            
            subject = s.name
            match = re.search(
                r"UNIT[\s_-]*(\d+)",
                file.name,
                re.IGNORECASE
            )

            unit = int(match.group(1)) if match else None
            source = file.name
            type = "notes"
            
            for chunk in chunks:
                document = {
                    "$vectorize": chunk,
                    "subject": s.name,
                    "unit": unit,
                    "source": source,
                    "type": type
                }
                
                documents.append(document)

            result = collection.insert_many(documents=documents)
            sleep(5)
            print(result)
            
            data[file.name] = True
            
            
with open(r"data\processed.json", "w") as f:
    json.dump(data, f)
            
