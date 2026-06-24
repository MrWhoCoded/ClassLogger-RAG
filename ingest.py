from astrapy import DataAPIClient
from langchain_text_splitters import RecursiveCharacterTextSplitter
import fitz
import requests
from pathlib import Path
import json
import re
from time import sleep
from docling.document_converter import DocumentConverter
import tiktoken

enc = tiktoken.get_encoding("cl100k_base")

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

splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
    chunk_size = 350,
    chunk_overlap = 50
)

ppt_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
    chunk_size = 150,
    chunk_overlap = 25
)

def pdf_to_text(file):
    text = ""
    
    doc = fitz.open(file)
    for page in doc:
        text = text + page.get_text()
        
    return text

def extract_text(file):
    converter = DocumentConverter()
    result = converter.convert(file)
    
    text = result.document.export_to_markdown()
    
    return text

def process_pdf_notes(file, subject):
        documents = []
        text = pdf_to_text(file)
        
        chunks = splitter.split_text(text)
        
        subject = subject
        match = re.search(
            r"UNIT[\s_-]*(\d+)",
            file.name,
            re.IGNORECASE
        )

        unit = int(match.group(1)) if match else file.name
        source = file.name
        type = "notes"
        
        for chunk in chunks:
            document = {
                "$vectorize": chunk,
                "subject": subject,
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
                
            if len(cells) < 6:
                print(f"Invalid row: {row}")
                continue
            
            question_no = cells[0]
            subquestion = cells[1]
            question_text = cells[2]
            co_type = cells[3]
            po_type = cells[4]
            marks = cells[5]
            
            if question_text.startswith("UNIT"):
                current_unit = question_text.split()[-1]
                continue
            
            if "OR" in cells:
                continue
                
            try:
                current_question_no = int(question_no)
            except ValueError:
                pass
                
            document = {
                    "$vectorize": question_text,
                    "subject": subject,
                    "question_id": f"{current_question_no}",
                    "question_no": current_question_no,
                    "subpart": subquestion.replace(")", ""),
                    "unit": current_unit,
                    "co": co_type,
                    "po": po_type,
                    "marks": int(marks),
                    "type": "pyq"
                }
            
            documents.append(document)
            
    return documents

def process_ppt_doc_notes(file, subject):
        documents = []
        text = extract_text(file)
        
        if file.name.endswith(".pptx"):
            chunks = ppt_splitter.split_text(text)
        else:
            chunks = splitter.split_text(text)
        
        subject = subject
        match = re.search(
            r"UNIT[\s_-]*(\d+)",
            file.name,
            re.IGNORECASE
        )

        unit = int(match.group(1)) if match else file.name
        source = file.name
        type = "notes"
        
        for chunk in chunks:
            document = {
                "$vectorize": chunk,
                "subject": subject,
                "unit": unit,
                "source": source,
                "type": type
            }
            
            documents.append(document)

        return documents
        
        
try:   
    for s in subdirs:
        for file in [f for f in Path(s).iterdir() if f.is_file()]:
            subject = s.name
            if file.name not in data.keys() or not data[file.name]:
                parent_folder = file.parent.name.lower()
                print(f"Processing {file.name} in {parent_folder}")

                if parent_folder == "question papers":
                    documents = process_question_paper(file, subject)
                    continue
                elif file.name.endswith(".pdf"):
                    documents = process_pdf_notes(file, subject)
                else:
                    documents = process_ppt_doc_notes(file, subject)

                for i, doc in enumerate(documents):
                    try:
                        tokens = len(enc.encode(doc["$vectorize"]))

                        print(
                            f"Inserting {i+1}/{len(documents)} "
                            f"({tokens} tokens)"
                        )

                        collection.insert_one(doc)

                    except Exception as e:
                        print("\n" + "=" * 80)
                        print(f"FAILED FILE: {file.name}")
                        print(f"FAILED DOCUMENT: {i}")
                        print(f"TOKENS: {tokens}")
                        print(e)

                        print("\nChunk Preview:")
                        print(doc["$vectorize"][:1000])

                        print("=" * 80)

                        raise
            data[file.name] = True
except Exception as e:
    print(str(e))
            
            
            
with open(r"data\processed.json", "w") as f:
    json.dump(data, f, indent=4)
            
