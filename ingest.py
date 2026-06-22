from astrapy import DataAPIClient
from langchain_text_splitters import RecursiveCharacterTextSplitter
import fitz
import requests
from pathlib import Path
import json
import re
from time import sleep
from docling.document_converter import DocumentConverter
import os
import dotenv

dotenv.load_dotenv()

ASTRADB_API_KEY = os.getenv("ASTRADB_API_KEY")
ASTRADB_ENDPOINT = os.getenv("ASTRADB_ENDPOINT")

if not ASTRADB_API_KEY or not ASTRADB_ENDPOINT:
    raise ValueError("ASTRADB_API_KEY and ASTRADB_ENDPOINT must be set in .env file")

client = DataAPIClient()
db = client.get_database(ASTRADB_ENDPOINT, token=ASTRADB_API_KEY)

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

def process_syllabus(file, subject):
        documents = []
        text = pdf_to_text(file)
        
        chunks = splitter.split_text(text)
        
        subject = subject
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

        return documents

def process_question_paper(file, subject):
    documents = []
    current_unit = None
    current_question_no = None
    
    converter = DocumentConverter()
    result = converter.convert(file)
    
    data = result.document.export_to_dict()
    
    for table in data["tables"]:
        grid = table["data"]["grid"]
        
        for row in grid:
            cells = []
            
            for cell in row:
                cells.append(cell["text"].strip())
            
            question_no = cells[0]
            subquestion = cells[1]
            question_text = cells[2]
            co_type = cells[3]
            po_type = cells[4]
            marks = cells[5]
            
            if question_text.startswith("UNIT"):
                current_unit = question_text.split()[-1]
                continue
            
            if question_text == "OR":
                continue
                
            if question_no.isdigit():
                current_question_no = int(question_no)
                
            document = {
                    "$vectorize": question_text,
                    "subject": subject,
                    "question_id": f"{current_question_no}",
                    "question_no": current_question_no,
                    "subpart": subquestion.replace(")", ""),
                    "unit": current_unit,
                    "co": co_type,
                    "po": po_type,
                    "marks": int(marks)
                }
            
            documents.append(document)
            
    return documents
        
        
for s in subdirs:
    for file in [f for f in Path(s).iterdir() if f.is_file()]:
        subject = s.name
        if file.name not in data.keys() or not data[file.name]:
            parent_folder = file.parent.name.lower()
            print(f"Processing {file.name} in {parent_folder}")

            if parent_folder == "question papers":
                documents = process_syllabus(file, subject)

            else:
                documents = process_question_paper(file, subject)

            result = collection.insert_many(documents=documents)
            sleep(5)
            data[file.name] = True
            
            
            
with open(r"data\processed.json", "w") as f:
    json.dump(data, f)
            
