# from langchain_community.document_loaders import PyPDFDirectoryLoader
# from langchain_text_splitters import RecursiveCharacterTextSplitter
# # from langchain_openai.embeddings import OpenAIEmbeddings
# from langchain_huggingface import HuggingFaceEmbeddings
# from langchain_chroma import Chroma
# from uuid import uuid4

# # import the .env file
# from dotenv import load_dotenv
# load_dotenv()

# # configuration
# DATA_PATH = r"data"
# CHROMA_PATH = r"chroma_db"

# # initiate the embeddings model
# # embeddings_model = OpenAIEmbeddings(model="text-embedding-3-large")
# # embeddings_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
# # embeddings_model = HuggingFaceEmbeddings(model_name="paraphrase-multilingual-MiniLM-L12-v2")

# embeddings_model = HuggingFaceEmbeddings(
#     model_name="intfloat/multilingual-e5-small"
# )

# # initiate the vector store
# vector_store = Chroma(
#     collection_name="example_collection",
#     embedding_function=embeddings_model,
#     persist_directory=CHROMA_PATH,
# )

# # loading the PDF document
# loader = PyPDFDirectoryLoader(DATA_PATH)

# raw_documents = loader.load()

# # splitting the document
# text_splitter = RecursiveCharacterTextSplitter(
#     chunk_size=300,
#     chunk_overlap=100,
#     length_function=len,
#     is_separator_regex=False,
# )

# # creating the chunks
# chunks = text_splitter.split_documents(raw_documents)

# # creating unique ID's
# uuids = [str(uuid4()) for _ in range(len(chunks))]

# # adding chunks to vector store
# vector_store.add_documents(documents=chunks, ids=uuids)



import os
import fitz  # PyMuPDF
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from uuid import uuid4

from dotenv import load_dotenv
load_dotenv()

# configuration
DATA_PATH = r"data"
CHROMA_PATH = r"chroma_db"

# نموذج embeddings محسّن للعربية
embeddings_model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

# initiate the vector store
vector_store = Chroma(
    collection_name="example_collection",
    embedding_function=embeddings_model,
    persist_directory=CHROMA_PATH,
)


def load_pdfs_with_pymupdf(data_path):
    """استخراج نص PDF باستخدام PyMuPDF (يعالج RTL العربي بشكل صحيح)"""
    docs = []
    for fname in os.listdir(data_path):
        if fname.lower().endswith(".pdf"):
            path = os.path.join(data_path, fname)
            pdf = fitz.open(path)
            for i, page in enumerate(pdf):
                text = page.get_text("text")
                docs.append(
                    Document(
                        page_content=text,
                        metadata={"source": fname, "page": i + 1},
                    )
                )
            pdf.close()
    return docs


raw_documents = load_pdfs_with_pymupdf(DATA_PATH)

# splitting the document
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=150,
    length_function=len,
    is_separator_regex=False,
    separators=["\n\n", "\n", "؟", "!", ".", " ", ""],
)

# creating the chunks
chunks = text_splitter.split_documents(raw_documents)

# creating unique ID's
uuids = [str(uuid4()) for _ in range(len(chunks))]

# adding chunks to vector store
vector_store.add_documents(documents=chunks, ids=uuids)

print(f"تم إضافة {len(chunks)} مقطع إلى قاعدة البيانات.")