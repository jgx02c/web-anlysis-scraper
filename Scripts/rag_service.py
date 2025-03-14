import json
import base64
import sys
import re
import os

from langchain_core.messages import AIMessage, HumanMessage
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from typing import Dict
from langchain_core.runnables import RunnablePassthrough

from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

from pinecone import Pinecone
from pinecone import ServerlessSpec
from langchain_pinecone import PineconeVectorStore

# Ensure the index is created only once
pc = Pinecone(api_key=os.environ.get("PINECONE_API_KEY"))
llm = ChatOpenAI(
    model="gpt-4o",
    streaming=True,
    temperature=0.8,     # Controls creativity/randomness
    presence_penalty=0.6, # Encourages diverse language
)
embeddings = OpenAIEmbeddings(model="text-embedding-ada-002", api_key=os.getenv('OPENAI_API_KEY'))
index_name = "leaps"
index = pc.Index(index_name)
PineconeVectorStore(index=index, embedding=embeddings)

def parse_retriever_input(params: Dict):
    last_message_content = params["messages"][-1].content
    if isinstance(last_message_content, list):
        return " ".join([item.get("text", "") for item in last_message_content if item["type"] == "text"])
    return last_message_content

def process_transcription(text_chunk, vectordb):
    image_message = HumanMessage(content=f"{text_chunk}")
    retriever = vectordb.as_retriever(search_kwargs={"k": 5})
    
    SYSTEM_TEMPLATE = """
**Instruction**:  

You are a helpful and knowledgeable SEO analysis assistant. Your goal is to provide clear, conversational explanations based on the HTML content provided. Think of yourself as a friendly expert having a natural conversation.

When responding:
- Synthesize the information naturally, as if explaining to a colleague
- Use conversational language while maintaining accuracy
- Feel free to add relevant examples or analogies when helpful
- Connect related concepts to provide better context
- Rephrase technical content in an accessible way

If the user provides a URL, do NOT attempt to fetch the page. Instead, rely only on the given context or metadata.

---
**Context**:  
{context}

**Response**:  
Please provide your response in a natural, conversational tone while ensuring all information is accurate and based on the context provided.
"""
    
    question_answering_prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_TEMPLATE),
        MessagesPlaceholder(variable_name="messages"),
    ])
    
    document_chain = create_stuff_documents_chain(llm, question_answering_prompt)
    retrieval_chain = RunnablePassthrough.assign(
        context=parse_retriever_input | retriever,
    ).assign(answer=document_chain)
    
    response_stream = retrieval_chain.stream({"messages": [image_message]})
    
    for chunk in response_stream:
        if 'answer' in chunk:
            yield chunk['answer']

def generate_insight_prompt(message):
    text_chunk = message
    vectordb = PineconeVectorStore.from_existing_index(index_name=index_name, embedding=embeddings)
    
    try:
        for result_chunk in process_transcription(text_chunk, vectordb):
            yield result_chunk
    except Exception as e:
        print(f"Error during transcription processing: {str(e)}")
        yield "Error: Could not generate insight."

if __name__ == "__main__":
    while True:
        user_input = input("\nEnter your prompt (or type 'exit' to quit): ")
        if user_input.lower() in ["exit", "quit"]:
            print("\nExiting...\n")
            break
        
        print("\nProcessing...\n")
        result = generate_insight_prompt(user_input)
        insights = []
        for insight in result:
            insights.append(insight)
        
        output = " ".join(insights)
        print(f"\nOutput:\n{output}\n")