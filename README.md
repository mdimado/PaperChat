PaperChat - AI-Driven PDF Interaction Platform
===================================================

### Overview

This repository contains code for an AI-powered chat application that allows users to upload PDF documents, perform queries, and receive responses based on the content of the uploaded documents.



https://github.com/mdimado/PaperChat/assets/123477562/a5adbe2b-6595-4acd-a5e6-8136b2a7fd50





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


<img width="1440" alt="Screenshot 2024-06-21 at 11 41 12 PM" src="https://github.com/mdimado/PaperChat/assets/123477562/c04a2938-e5a6-420b-a980-fb2c7c11b22a">

<img width="723" alt="Screenshot 2024-06-21 at 11 41 39 PM" src="https://github.com/mdimado/PaperChat/assets/123477562/88f39359-6791-4645-82ca-77206af2c710">

<img width="379" alt="Screenshot 2024-06-21 at 11 42 02 PM" src="https://github.com/mdimado/PaperChat/assets/123477562/6f4f22b6-6be2-4834-b2db-f2a7e5754c9e">
