from pathlib import Path
from docling.document_converter import DocumentConverter
from langchain_text_splitters import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=100
)

def extract_text(file):
    converter = DocumentConverter()

    result = converter.convert(file)

    return result.document.export_to_text()

def process_ppt_doc_notes(file, subject):
    documents = []

    text = extract_text(file)

    print("=" * 50)
    print("EXTRACTED TEXT")
    print("=" * 50)
    print(text[:2000])

    chunks = splitter.split_text(text)

    print("\n")
    print(f"Chunks created: {len(chunks)}")

    for i, chunk in enumerate(chunks[:5]):
        print("\n")
        print("=" * 50)
        print(f"CHUNK {i+1}")
        print("=" * 50)
        print(chunk[:500])

    for chunk in chunks:
        documents.append(
            {
                "$vectorize": chunk,
                "subject": subject,
                "unit": None,
                "source": file.name,
                "type": "notes"
            }
        )

    return documents


file = Path(r"data/NGD/unit 1 - updated (1).pptx")
# file = Path(r"data\SE\your_file.docx")

docs = process_ppt_doc_notes(
    file=file,
    subject="NGD"
)

print("\n")
print(f"Documents generated: {len(docs)}")