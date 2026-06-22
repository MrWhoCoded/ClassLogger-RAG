from astrapy import DataAPIClient
import requests
import google
import os
import dotenv

dotenv.load_dotenv()


ASTRADB_API_KEY = os.getenv("ASTRADB_API_KEY")
ASTRADB_ENDPOINT = os.getenv("ASTRADB_ENDPOINT")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not ASTRADB_API_KEY or not ASTRADB_ENDPOINT:
    raise ValueError("ASTRADB_API_KEY and ASTRADB_ENDPOINT must be set in .env file")

client = DataAPIClient()
db = client.get_database(
    ASTRADB_ENDPOINT, token=ASTRADB_API_KEY
)

collection = db.get_collection("classloggertest")

messages = {
    "role": "system",
    "content": "You are an AI assistant that can answer questions based on the context you are given. Don't mention the context, just use it to inform your answers."
}

while True:
    query = input("Enter your prompt: ")
    if query == "q":
        break
    
    try:
        cursor = collection.find(
                {},
                sort={"$vectorize": query},
                limit=5,
                projection={"$vectorize": 1},
            )
        
        docs = cursor.to_list()
        context = "\n".join(
            (doc.get("$vectorize") or "") for doc in docs
        ).strip()
        
        rag_message = {
                "role": "user",
                "content": (
                    f"{context}\n---\n"
                    "Given the above context, answer the following question:\n"
                    f"{query}"
                ),
            }
        
        endpoint = "https://openrouter.ai/api/v1/chat/completions"
        # Ensure endpoint has a scheme
        if not endpoint.startswith(("http://", "https://")):
            endpoint = "https://" + endpoint

        resp = requests.post(
            endpoint,
            headers={
                "Authorization": f"Bearer {}",
                "Content-Type": "application/json"
            },
            json={
                "model": "qwen/qwen3.5-9b",
                "messages": [
                    messages, rag_message
                ]
            }
        )

        try:
            resp.raise_for_status()
        except Exception:
            print(f"HTTP error {resp.status_code}: {resp.text}")
            continue

        try:
            response = resp.json()
        except ValueError:
            print(f"Invalid JSON response (status {resp.status_code}): {resp.text}")
            continue

        #print(somejson['choices'])
        print(response["choices"][0]["message"]["role"])
        print(response["choices"][0]["message"]["content"])
        print(response["choices"][0]["message"]["reasoning"])
        print(response["choices"][0]["message"]["reasoning_details"][0])
    except Exception as e:
            print(str(e))