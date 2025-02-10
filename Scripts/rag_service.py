import json
import base64
import sys
import re
import os
from typing import Dict, Generator, List, Union
from langchain_core.messages import AIMessage, HumanMessage
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from pinecone import Pinecone
from langchain_pinecone import PineconeVectorStore

def initialize_services():
    """Initialize all required services and return them."""
    pc = Pinecone(api_key=os.environ.get("PINECONE_API_KEY"))
    llm = ChatOpenAI(model="gpt-4", streaming=True)
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-large", 
        api_key=os.getenv('OPENAI_API_KEY')
    )
    
    index_name = "leaps"
    index = pc.Index(index_name)
    vector_store = PineconeVectorStore(index=index, embedding=embeddings)
    
    return llm, embeddings, vector_store, index_name

def clean_text(text: str) -> str:
    """Clean and normalize text content."""
    if not text:
        return ""
        
    # Join text if it's a list
    if isinstance(text, list):
        text = ' '.join(text)
        
    # Convert to string if not already
    text = str(text)
    
    # Replace multiple spaces with single space
    text = ' '.join(text.split())
    
    # Fix common spacing issues around punctuation
    text = re.sub(r'\s+([.,!?:;])', r'\1', text)
    
    # Fix spacing after punctuation
    text = re.sub(r'([.,!?:;])(\S)', r'\1 \2', text)
    
    # Remove repeated periods
    text = re.sub(r'\.+', '.', text)
    
    # Fix spacing around hyphens in compound words
    text = re.sub(r'\s*-\s*', '-', text)
    
    return text.strip()

def parse_retriever_input(params: Dict) -> str:
    """Parse and clean the retriever input."""
    last_message_content = params["messages"][-1].content
    
    # Handle list content
    if isinstance(last_message_content, list):
        text_content = " ".join([
            str(item.get("text", "")) 
            for item in last_message_content 
            if item.get("type") == "text" and item.get("text")
        ])
    else:
        text_content = str(last_message_content)
    
    # Clean and normalize the text
    cleaned_text = clean_text(text_content)
    
    # Ensure proper sentence spacing
    sentences = cleaned_text.split('. ')
    cleaned_sentences = [s.strip() for s in sentences if s.strip()]
    
    return '. '.join(cleaned_sentences)

def create_qa_chain(llm: ChatOpenAI, retriever) -> RunnablePassthrough:
    """Create the question-answering chain."""
    system_template = """
    **Instruction**:  
    You are an SEO analysis assistant. Use the provided HTML content to answer the user's question.  
    If the user provides a URL, do NOT attempt to fetch the page. Instead, rely only on the given context.  
    
    ---
    **Context**:  
    {context}
    
    **Response**:  
    """
    
    question_answering_prompt = ChatPromptTemplate.from_messages([
        ("system", system_template),
        MessagesPlaceholder(variable_name="messages"),
    ])
    
    document_chain = create_stuff_documents_chain(llm, question_answering_prompt)
    
    return (
        RunnablePassthrough.assign(
            context=parse_retriever_input | retriever,
        ).assign(answer=document_chain)
    )

def process_transcription(
    text_chunk: str, 
    vectordb: PineconeVectorStore,
    llm: ChatOpenAI
) -> Generator[str, None, None]:
    """Process text and generate responses."""
    try:
        image_message = HumanMessage(content=clean_text(text_chunk))
        retriever = vectordb.as_retriever(search_kwargs={"k": 5})
        qa_chain = create_qa_chain(llm, retriever)
        
        response_stream = qa_chain.stream({"messages": [image_message]})
        
        for chunk in response_stream:
            if 'answer' in chunk:
                yield clean_text(chunk['answer'])
                
    except Exception as e:
        print(f"Error in process_transcription: {str(e)}")
        yield "Error: Could not process transcription."

def generate_insight_prompt(
    message: str,
    vectordb: PineconeVectorStore,
    llm: ChatOpenAI
) -> Generator[str, None, None]:
    """Generate insights from the input message."""
    try:
        for result_chunk in process_transcription(message, vectordb, llm):
            yield clean_text(result_chunk)
    except Exception as e:
        print(f"Error in generate_insight_prompt: {str(e)}")
        yield "Error: Could not generate insight."

def main():
    """Main execution function."""
    # Initialize services
    llm, embeddings, vectordb, index_name = initialize_services()
    
    while True:
        try:
            user_input = input("\nEnter your prompt (or type 'exit' to quit): ")
            if user_input.lower() in ["exit", "quit"]:
                print("\nExiting...\n")
                break
            
            print("\nProcessing...\n")
            result = generate_insight_prompt(user_input, vectordb, llm)
            insights = []
            
            for insight in result:
                cleaned_insight = clean_text(insight)
                if cleaned_insight:  # Only append non-empty insights
                    insights.append(cleaned_insight)
            
            # Join insights and ensure proper sentence spacing
            output = " ".join(insights)
            # Clean the final output one more time
            output = clean_text(output)
            print(f"\nOutput:\n{output}\n")
            
        except KeyboardInterrupt:
            print("\nOperation cancelled by user. Exiting...\n")
            break
        except Exception as e:
            print(f"\nError: {str(e)}\n")

if __name__ == "__main__":
    main()