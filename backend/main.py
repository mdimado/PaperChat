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
groq_chat = ChatGroq(temperature=0.8, groq_api_key=groq_api_key, model_name="mixtral-8x7b-32768")

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
        system_message = "The points provided are from a pdf that I have uploaded. The query at the end or the request is what you have to answer "
        human_message = f'''Question: {request.query}\n Context uploaded from the pdf:\n{context}\n---\nAnswer:\n\nplease answer in markdown only Markdown is a lightweight markup language that you can use to add formatting elements to plaintext text documents. Here is a detailed guide on how to use Markdown with explanations for each symbol:

Headings
# Heading 1
## Heading 2
### Heading 3
#### Heading 4
##### Heading 5
###### Heading 6
The number of # symbols at the beginning of a line represents the level of the heading. More # symbols mean a lower-level heading.

Emphasis
*italic* or _italic_: Wrap the text in single asterisks or underscores to italicize it.
**bold** or __bold__: Wrap the text in double asterisks or underscores to make it bold.
***bold and italic***: Wrap the text in triple asterisks to make it both bold and italic.
Lists
Unordered lists: Use -, *, or + followed by a space to create an unordered list.
Example:
- Item 1
- Item 2
- Item 3
Ordered lists: Use numbers followed by a period.
Example:
1. First item
2. Second item
3. Third item
Links
[Link text](URL): Create a hyperlink with the text "Link text" that directs to the specified URL.
Example: [OpenAI](https://www.openai.com)
Images
![Alt text](Image URL): Embed an image with the alt text "Alt text" that displays the specified image.
Example: ![OpenAI Logo](https://www.openai.com/logo.png)
Blockquotes
> Blockquote: Use the > symbol at the beginning of a line to create a blockquote.
Example:
This is a blockquote.

Code
Inline code: Use backticks (`) to wrap inline code.
Example: `inline code`
Code blocks: Use triple backticks (```) before and after the code block.
Example:
go
Copy code
```
Code block
```
Horizontal Rules
---, ***, or ___: Use three or more hyphens, asterisks, or underscores to create a horizontal rule.
Example:
Tables
Use pipes (|) to separate columns and hyphens (-) to create the header row.
Example:
sql
Copy code
| Header 1 | Header 2 |
|----------|----------|
| Row 1    | Data 1   |
| Row 2    | Data 2   |
Task Lists
- [ ] Task 1: Create an unchecked task.
- [x] Task 2: Create a checked task.
Example:
 Unchecked task
 Checked task
Miscellaneous
Strikethrough: ~~strikethrough~~: Wrap the text in double tildes to strike it through.
Example: ~~strikethrough~~
Newlines
Newline in a paragraph: To create a newline within a paragraph, end a line with two or more spaces and then press Enter.
Example:
vbnet
Copy code
Line 1 with two spaces at the end.  
Line 2 is a new line within the same paragraph.
Paragraph break: Simply press Enter twice to create a new paragraph.
Example:
arduino
Copy code
Paragraph 1.

Paragraph 2 starts after a blank line.
By using these symbols and syntax, you can format text documents with Markdown effectively. Practice using these elements to become proficient in Markdown. You must use the following Markdown syntax to format text documents. Pay special attention to how newlines are handled. '''

        prompt = ChatPromptTemplate.from_messages([("system", system_message), ("human", human_message)])
        chain = prompt | groq_chat

        async for chunk in chain.astream({"text": human_message}):
            yield chunk.content

    return StreamingResponse(response_generator(), media_type="text/plain")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
