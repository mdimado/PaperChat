PaperChat - AI-Driven PDF Interaction Platform
===================================================

### Overview

This repository contains code for an AI-powered chat application that allows users to upload PDF documents, perform queries, and receive responses based on the content of the uploaded documents.

https://github.com/mdimado/PaperChat/assets/123477562/c75a11db-8ae7-4ce6-9edf-b181cf36bbae

### File Structure

- **`backend/`**: Contains the FastAPI backend code.
  - **`main.py`**: Main backend Python script.
  - **`requirements.txt`**: File listing the Python dependencies.
- **`frontend/`**: Contains the React frontend code.
  - **`public/`**: Contains static assets and the main `index.html` file.
  - **`src/`**: Contains the JavaScript code for the React components.
    - **`components/`**: Contains React components used in the application.
    - **`assets/`**: Static assets like images, fonts, etc.
- **`readme.md`**: Documentation file providing information about the project setup and structure.

### Setup Instructions

Follow these steps to set up and run the project:

1. Clone the Repository:
   ```
   git clone https://github.com/mdimado/PaperChat.git
   cd PaperChat
   ```

2. Install Backend Dependencies:
   ```
   cd backend
   pip install -r requirements.txt
   ```
   
3. Pull the Qdrant Docker Image
   ```
   docker pull qdrant/qdrant
   ```
   
4. Run the Qdrant Docker Container:
   ```
   docker run -d --name qdrant -p 6333:6333 qdrant/qdrant
   ```

5. Set Environment Variables:
   Create a .env file in the backend directory and add the following variables:
   ```
   COHERE_API_KEY=your-cohere-api-key
   GROQ_API_KEY=your-groq-api-key
   ```

6. Run the Backend Server:
   ```
   uvicorn main:app --reload
   ```

7. Install Frontend Dependencies:
   ```
   cd ../frontend
   npm install
   ```

8. Run the Frontend Development Server:
   ```
   npm start
   ```


