from astrapy import DataAPIClient
import requests
import os
import dotenv

dotenv.load_dotenv()

ASTRADB_API_KEY = os.getenv("ASTRADB_API_KEY")
ASTRADB_ENDPOINT = os.getenv("ASTRADB_ENDPOINT")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

messages = {
    "role": "system",
    "content": """
    You are ClassLogger AI, a study assistant for engineering students.

    Use the retrieved notes and question papers to answer questions.

    When discussing exam topics:
    - Explain concepts clearly.
    - Mention important points frequently asked in exams if available.
    - If the answer is not present, say: 'This topic is not present in the provided study material.'

    Do not fabricate information.
"""
}

if not ASTRADB_API_KEY or not ASTRADB_ENDPOINT:
    raise ValueError("ASTRADB_API_KEY and ASTRADB_ENDPOINT must be set in .env file")

client = DataAPIClient()
db = client.get_database(
    ASTRADB_ENDPOINT, token=ASTRADB_API_KEY
)

collection = db.get_collection("classloggertest")

def filter_exams(query):
    filtered = {}
    keywords = ["exam", "question", "questions", "papers", "exams", "pyq", "pyqs"]
    
    query = query.lower()
    query.replace("\n", " ")
    query.replace("\t", " ")
    query.split(" ")
    
    for word in keywords:
        if word in query:
            filtered = {"type": "pyq"}
            return filtered, True
            
    return filtered, False
    
def process_query(query, filter, limit=5):
    cursor = collection.find(
                filter=filter,
                sort={"$vectorize": query},
                limit=limit,
                projection={"$vectorize": 1},
            )
        
    docs = cursor.to_list()
    for i, doc in enumerate(docs):
        """print(f"\nRESULT {i+1}")
        print(doc["subject"])
        print(doc["type"])
        print(doc.get("unit"))
        print(doc["$vectorize"][:300])
        print("+" * 50)"""
    context = "\n".join(
        (doc.get("$vectorize") or "") for doc in docs
    ).strip()
    
    return context

def answer_query(query):
    try:
        context = process_query(query, {"type": "notes"})
        
        filtered, success = filter_exams(query)
        if success:
            context += process_query(query, filtered, limit=10)
        
        rag_message = {
                "role": "user",
                "content": (
                    f"{context}\n---\n"
                    "Given the above context, answer the following question:\n"
                    f"{query}"
                ),
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
                    rag_message, messages
                ]
            }
        )

        try:
            resp.raise_for_status()
        except Exception:
            print(f"HTTP error {resp.status_code}: {resp.text}")
            return

        try:
            response = resp.json()
        except ValueError:
            print(f"Invalid JSON response (status {resp.status_code}): {resp.text}")
            return


        return response
    except Exception as e:
            print(str(e))
            return

if __name__ == "__main__":
    while True:
        query = input("Enter your prompt: ")
        if query == "q":
            break
        
        response = answer_query(query)
        
        if isinstance(response, dict):
            print("=" * 50)
            print(response["choices"][0]["message"]["content"])
            print("=" * 50)
            print(response["choices"][0]["message"]["reasoning"])
            
    