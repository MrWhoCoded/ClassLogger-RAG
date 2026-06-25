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
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not ASTRADB_API_KEY or not ASTRADB_ENDPOINT:
    raise ValueError("ASTRADB_API_KEY and ASTRADB_ENDPOINT must be set in .env file")

question_paper_messages = {
    "role": "system",
    "content": """
You are an information extraction engine.

Your task is to extract and structure examination questions from the provided text.

The input is text extracted from an engineering university question paper.

Return ONLY valid JSON.

Do not explain.
Do not summarize.
Do not add markdown.
Do not add code fences.
Do not add any text outside the JSON output.

Return a JSON object with the following schema:

{
    "questions": [
        {
            "question_no": 1,
            "subpart": "a",
            "unit": "UNIT-I",
            "question": "Question text",
            "co": "CO1",
            "po": "PO1",
            "marks": 6,
            "type": "pyq"
        }
    ]
}

Example Input:

UNIT - I

1
a)
What is Agile methodology?
CO1
PO1
06

Example Output:

{
  "questions": [
    {
      "question_no": 1,
      "subpart": "a",
      "unit": "UNIT-I",
      "question": "What is Agile methodology?",
      "co": "CO1",
      "po": "PO1",
      "marks": 6,
      "type": "pyq"
    }
  ]
}

Rules:

1. Extract every question present in the text.
2. Preserve the complete question text exactly as written.
3. Combine multiline questions into a single question string.
4. Keep the current UNIT until a new UNIT appears.
5. Ignore instructions, page numbers, headers, footers, USN fields, and decorative text.
6. Ignore standalone OR entries.
7. Marks must be integers.
8. Question numbers must be integers.
9. Subpart must be a, b, or c.
10. If a question continues across multiple lines, merge them into one question.
11. Do not omit any valid question.
12. Return only the JSON object.
13. Use only English language.
"""
}

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

def extract_text_question_paper(file):
    converter = DocumentConverter()
    result = converter.convert(file)
    
    text = result.document.export_to_text()
    
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
    text = extract_text_question_paper(file) 
    
    try: 
        rag_message = {
                "role": "user",
                "content": text
            }
        
        endpoint = "https://openrouter.ai/api/v1/chat/completions"
        if not endpoint.startswith(("http://", "https://")):
            endpoint = "https://" + endpoint

        resp = requests.post(
            endpoint,
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "qwen/qwen3-8b",
                "messages": [
                    rag_message, question_paper_messages
                ], 
            }
        )

        resp.raise_for_status()
    except Exception:
        print(f"HTTP error {resp.status_code}: {resp.text}")
    
    try:   
        response = resp.json()
    except ValueError:
        print(f"Invalid JSON response (status {resp.status_code}): {resp.text}")
        return
    
    result = response["choices"][0]["message"]["content"]
    content = json.loads(result)
    questions = content["questions"]
    
    for question in questions:     
        document = {
                "$vectorize": question["question"],
                "subject": subject,
                "question_id": f"{question["question_no"]}{question["subpart"]}",
                "question_no": int(question["question_no"]),
                "subpart": question["subpart"],
                "unit": question["unit"],
                "co": question["co"],
                "po": question["po"],
                "marks": int(question["marks"]),
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
            documents = []
            subject = s.name
            if file.name not in data.keys() or not data[file.name]:
                parent_folder = file.parent.name.lower()
                print(f"Processing {file.name} in {parent_folder}")

                if parent_folder == "question papers":
                    documents = process_question_paper(file, file.name)
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
            
