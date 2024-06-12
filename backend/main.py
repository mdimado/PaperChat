from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import os
import shutil
import cohere
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import CharacterTextSplitter
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from dotenv import load_dotenv


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

load_dotenv()

UPLOAD_DIR = "uploaded_pdfs"
os.makedirs(UPLOAD_DIR, exist_ok=True)

cohere_api_key = os.getenv('COHERE_API_KEY')
cohere_client = cohere.Client(cohere_api_key)

QDRANT_API_URL = 'http://localhost:6333'
qdrant_client = QdrantClient(QDRANT_API_URL)

groq_api_key = os.getenv('GROQ_API_KEY')
groq_chat = ChatGroq(temperature=0.7, groq_api_key=groq_api_key, model_name="mixtral-8x7b-32768")

@app.post("/upload/")
async def upload_pdf(pdf_file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, pdf_file.filename)
    
    with open(file_path, "wb") as f:
        shutil.copyfileobj(pdf_file.file, f)
    
    collection_name = os.path.splitext(pdf_file.filename)[0]  

    loader = PyPDFLoader(file_path)
    splitter = CharacterTextSplitter(separator='.\n')

    documents = loader.load()
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
        points.append(PointStruct(id=i, vector=embedding, payload={"text": text_chunks[i-1]}))

    qdrant_client.recreate_collection(
        collection_name=collection_name,
        vectors_config=vectors_config,
    )

    operation_info = qdrant_client.upsert(
        collection_name=collection_name,
        wait=True,
        points=points
    )

class QueryRequest(BaseModel):
    collection_name: str
    query: str

@app.post("/query/")
async def query_database(request: QueryRequest):
    query_embedding = cohere_client.embed(texts=[request.query]).embeddings[0]

    search_result = qdrant_client.search(
        collection_name=request.collection_name,
        query_vector=query_embedding,
        limit=3
    )

    context = ""
    for result in search_result:
        context += result.payload['text'] + "\n"

    async def response_generator():
        system_message = "The points provided are from a pdf that I have uploaded. The query at the end or the request is what you have to answer"
        human_message = f"Question: {request.query}\n Context uploaded from the pdf:\n{context}\n---\nAnswer:\n\nplease answer in markdown only also add new line after each paragraph use the ''' ''' to writhe the code so that we can directly copy it, also in the answer do not say or mention that you are answering in markdown format or anything like that"

        prompt = ChatPromptTemplate.from_messages([("system", system_message), ("human", human_message)])
        chain = prompt | groq_chat

        async for chunk in chain.astream({"text": human_message}):
            yield chunk.content

    return StreamingResponse(response_generator(), media_type="text/plain")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
