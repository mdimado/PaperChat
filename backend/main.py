#used for testing

import os
import shutil

import cohere
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from pydantic import BaseModel
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, PointStruct, VectorParams

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

load_dotenv()

UPLOAD_DIR = os.getcwd()

cohere_api_key = os.getenv("COHERE_API_KEY")
cohere_client = cohere.Client(cohere_api_key)

qdrant_api_url = os.getenv("QDRANT_API_URL")
qdrant_api_key = os.getenv("QDRANT_API_KEY")
qdrant_client = QdrantClient(
    url=qdrant_api_url, 
    api_key=qdrant_api_key,
)

groq_api_key = os.getenv("GROQ_API_KEY")
groq_chat = ChatGroq(temperature=0.7, groq_api_key=groq_api_key, model_name="mixtral-8x7b-32768")


@app.post("/upload/")
async def upload_pdf(pdf_file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, pdf_file.filename)

    with open(file_path, "wb") as f:
        shutil.copyfileobj(pdf_file.file, f)

    collection_name = os.path.splitext(pdf_file.filename)[0]

    loader = PyPDFLoader(file_path)
    splitter = CharacterTextSplitter(separator=".\n")

    pages = loader.load_and_split(splitter)
    texts = splitter.split_documents(pages)

    text_chunks = [chunk.page_content for chunk in texts]

    embeddings = embed_text_chunks(text_chunks)

    store_embeddings_in_qdrant(collection_name, text_chunks, embeddings)

    return {"embeddings": embeddings}


def embed_text_chunks(chunks):
    response = cohere_client.embed(texts=chunks)
    embeddings = response.embeddings
    return embeddings


def store_embeddings_in_qdrant(collection_name, text_chunks, embeddings):
    vectors_config = VectorParams(size=4096, distance=Distance.COSINE)

    points = []
    for i, embedding in enumerate(embeddings, start=1):
        points.append(PointStruct(id=i, vector=embedding, payload={"text": text_chunks[i - 1]}))

    qdrant_client.recreate_collection(
        collection_name=collection_name,
        vectors_config=vectors_config,
    )

    qdrant_client.upsert(collection_name=collection_name, wait=True, points=points)


class QueryRequest(BaseModel):
    collection_name: str
    query: str

# Endpoint for querying the database and generating responses
@app.post("/query/")
async def query_database(request: QueryRequest):
    query_embedding = cohere_client.embed(texts=[request.query]).embeddings[0]

    search_result = qdrant_client.search(collection_name=request.collection_name, query_vector=query_embedding, limit=3)

    context = ""
    for result in search_result:
        context += result.payload["text"] + "\n"

    async def response_generator():
        system_message = "You are a question-answering assistant. You are given relevant context. Answer only in Markdown format. Use newlines, Use backticks for code. Do not mention markdown or code anywhere. Only answer what is asked and keep it concise."
        human_message = f"""### Question: {request.query}
        ### Context: {context}
        !!! Remember to answer in markdown format
        ### Answer:"""

        prompt = ChatPromptTemplate.from_messages([("system", system_message), ("human", human_message)])
        chain = prompt | groq_chat

        async for chunk in chain.astream({"text": human_message}):
            yield chunk.content

    return StreamingResponse(response_generator(), media_type="text/plain")


if __name__ == "__main__":
    port = int(os.getenv('PORT', 8000)) 
    uvicorn.run(app, host="0.0.0.0", port=port)