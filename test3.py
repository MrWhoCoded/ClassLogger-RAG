import json

with open(r"D:\projects\classloggerRAG\paper.json", "r") as f:
    content = json.load(f)
    
questions = content["questions"]

for question in questions:
    print(question)
    print(type(question))
    print("=" * 50)
