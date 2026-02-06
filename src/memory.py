import os
from dotenv import load_dotenv, find_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

# Load keys
load_dotenv(find_dotenv())

# Configuration
RESUME_PATH = "./data/Abhiram_Radha_Krishna_Resume.pdf"
DB_PATH = "./chroma_db"

def build_memory():
    """
    Ingests the resume, chunks it intelligently, and creates the Vector Brain.
    """
    if not os.path.exists(RESUME_PATH):
        print(f"❌ Error: Resume not found at {RESUME_PATH}")
        return

    print("🧠 Mikasa is analyzing your resume...")

    loader = PyPDFLoader(RESUME_PATH)
    docs = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", "•", " "]
    )
    splits = text_splitter.split_documents(docs)
    print(f"📄 Split resume into {len(splits)} memory fragments.")

    embedding_fn = OpenAIEmbeddings(model="text-embedding-3-small")
    
    vectorstore = Chroma.from_documents(
        documents=splits,
        embedding=embedding_fn,
        persist_directory=DB_PATH
    )

    print(f"💾 Memory successfully built at {DB_PATH}")
    print("✅ Mikasa now knows your profile.")

def get_retriever():
    """
    Returns the search engine for the agent to use.
    """
    embedding_fn = OpenAIEmbeddings(model="text-embedding-3-small")
    
    # Connect to the existing database
    vectorstore = Chroma(
        persist_directory=DB_PATH, 
        embedding_function=embedding_fn
    )
    
    # Return as a retriever tool (Top 4 results)
    return vectorstore.as_retriever(search_kwargs={"k": 4})

if __name__ == "__main__":
    build_memory()