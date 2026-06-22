from astrapy import DataAPIClient
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pathlib import Path
import fitz
import re
import json

from docling.document_converter import DocumentConverter

ASTRA_DB_TOKEN = "AstraCS:EqEhdZdzhCAZQvNhZZBvRHUU:cbf0c1352e22d1138b9fe42cb49b91c72ccdfc909273339b3627500c43a579ba"
ASTRA_DB_ENDPOINT = "YOUR_ENDPOINT"
"""
# Connect
client = DataAPIClient()
db = client.get_database(
    "https://5c624cdd-cc62-442f-93f4-8ec4efaa2dbf-us-east-2.apps.astra.datastax.com", token=ASTRA_DB_TOKEN
)

collection = db.get_collection("classloggertest")

# Choose ONE PDF
pdf_file = Path(r"D:\projects\classloggerRAG\data\qustion papers\_23DC6PCSEA.pdf")

splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=100
)

def pdf_to_text(file):
    text = ""

    doc = fitz.open(file)

    for page in doc:
        text += page.get_text()

    doc.close()

    return text

def chucker(text):
    pattern = r'(?=\n\d+\s+[a-c]\))'

    questions = re.split(pattern, text)

    return [
        q.strip()
        for q in questions
        if len(q.strip()) > 20
    ]
"""
#converter = DocumentConverter()

#result = converter.convert(r"D:\projects\classloggerRAG\data\qustion papers\_23DC6PCSEA.pdf")

#print("=" * 100)
#data = result.document.export_to_dict()
#print("=" * 100)

#with open("paper.json", "w") as file:
#    json.dump(data, file, indent=4)
    
with open("paper.json", "r") as file:
    data = json.load(file)

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
            
        if question_no and isinstance(int(question_no), int):
            current_question_no = int(question_no)
            
        question = {
                "question_id": f"{current_question_no}",
                "question_no": current_question_no,
                "subpart": subquestion[0],
                "unit": current_unit,
                "question": question_text,
                "co": co_type,
                "po": po_type,
                "marks": int(marks)
            }
        
        print(question)
            
        
            
        
                
            
#print("=" * 100)