from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import os
import fitz 

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploaded_pdfs"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/upload/")
async def upload_pdf(pdf_file: UploadFile = File(...)):
    contents = await pdf_file.read()
    file_path = os.path.join(UPLOAD_DIR, pdf_file.filename)
    
    with open(file_path, "wb") as f:
        f.write(contents)
    
    text = extract_text_from_pdf(file_path)
    chunks = split_text_into_chunks(text)
    
    return chunks

def extract_text_from_pdf(file_path):
    text = ""
    with fitz.open(file_path) as pdf_document:
        for page in pdf_document:
            text += page.get_text()
    return text

def split_text_into_chunks(text, words_per_chunk=200):
    chunks = []
    current_chunk = ""
    current_word_count = 0
    
    for paragraph in text.split('\n\n'):
        words = paragraph.split()
        for word in words:
            current_chunk += word + ' '
            current_word_count += 1
            if current_word_count >= words_per_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = ""
                current_word_count = 0
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks
