import pandas
import os
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from pypdf import PdfReader

embeddings = OllamaEmbeddings(model="mxbai-embed-large")


vector_db = r"./vectordb"
db_exists = not os.path.exists(vector_db)

if db_exists:
    loader = PyPDFLoader(r"SEA_UNIT-1 NOTES (1).pdf")
    documents = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )

    chunks = splitter.split_documents(documents)

    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=vector_db
    )
else:
    vectorstore = Chroma(
        embedding_function=embeddings,
        persist_directory=vector_db
    )

retriever = vectorstore.as_retriever(search_kwargs={"k":6})