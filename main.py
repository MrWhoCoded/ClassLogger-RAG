from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
import vector

model = OllamaLLM(model="qwen2.5:3b")

template = """
YOU ARE A HELPFUL ASSISTANT. ANSWER THE USER'S QUESTION IN A CONCISE MANNER. YOU ARE GIVEN WITH SOME SYLLABUS FROM A COURSE OF
SOFTWARE ENGINEERING. THE USER WILL ASK YOU QUESTIONS RELATED TO THE SYLLABUS AND YOU HAVE TO ANSWER THEM BASED ON THE SYLLABUS.
HERE IS THE SYLLABUS: {syllabus}
HERE IS THE ANSWER TO THE USER'S QUESTION: {query}
"""

prompt = ChatPromptTemplate.from_template(template)
chain = prompt | model

while True:
    query = input("Enter your prompt: ")
    if query == "q":
        break
    syllabus = vector.retriever.invoke(query)
    result = chain.invoke({"syllabus": syllabus, "query": query})
    print(result)