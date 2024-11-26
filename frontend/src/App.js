import React, { useState, useRef, useEffect } from "react";
import axios from "axios";
import "./App.css";
import Markdown from 'react-markdown';
import aiplanet from "./images/download.png"
import usericon from "./images/usericon.png"
import logo from "./images/logo.png"
import logolight from "./images/logolight.png"
import logodark from "./images/logodark.png"

const FileUpload = () => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [data, setData] = useState("");
  const [query, setQuery] = useState("");
  const [response, setResponse] = useState("");
  const [collectionName, setCollectionName] = useState("");
  const [pdfUploaded, setPdfUploaded] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [chatHistory, setChatHistory] = useState([]); 
  const chatEndRef = useRef(null); 

  useEffect(() => {
    scrollToBottom();
  }, [response]);

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const handleFileChange = async (event) => {
    const file = event.target.files[0];
    setSelectedFile(file);
    await uploadFile(file);
  };

  const uploadFile = async (file) => {
    setUploading(true);
    const formData = new FormData();
    formData.append("pdf_file", file);

    try {
      const response = await axios.post("http://localhost:8000/upload/", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });
      setData(response.data);
      console.log("File uploaded successfully:", response.data);
      setCollectionName(file.name.split('.').slice(0, -1).join('.'));
      setPdfUploaded(true);
    } catch (error) {
      console.error("Error uploading file:", error);
    } finally {
      setUploading(false);
    }
  };

  const handleQueryChange = (event) => {
    setQuery(event.target.value);
  };

  const handleQuery = async () => {
    if (!query || !pdfUploaded) return;

    await sendMessage(query);
  };

  const sendMessage = async (message) => {
    const newChatHistory = [...chatHistory, { type: "user", text: message }];
    setChatHistory(newChatHistory); 
    setQuery(""); 
    setResponse(""); 

    try {
      const response = await fetch('http://localhost:8000/query/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: message,
          collection_name: collectionName,
        }),
      });

      if (!response.body) {
        console.error('ReadableStream not supported in this browser.');
        return;
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let result = '';
      let currentBotResponse = ''; 

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value);
        result += chunk;
        currentBotResponse += chunk;

        setResponse(result); 

        setChatHistory(prevChatHistory => {
          const lastEntry = prevChatHistory[prevChatHistory.length - 1];
          if (lastEntry && lastEntry.type === "bot") {
            lastEntry.text = currentBotResponse;
            return [...prevChatHistory];
          } else {
            return [...prevChatHistory, { type: "bot", text: chunk }];
          }
        });

        await new Promise(resolve => setTimeout(resolve, 20));
      }
    } catch (error) {
      console.error("Error querying database:", error);
    }
  };

  const handleKeyPress = (event) => {
    if (event.key === 'Enter') {
      event.preventDefault();
      handleQuery();
    }
  };

  return (
    <div className="main">
      <div className="header">
      <div className="logo logodark"><img src={logodark} alt="AI Planet Logo"/></div>
        <div className="logo logolight"><img  src={logolight} alt="AI Planet Logo"/></div>
        <div className="labelbutton">
          {selectedFile ? (uploading ? <div className="fileicon"><i className="loader ri-loader-4-line"></i></div> : <div className="fileicon"><i className="ri-file-3-line"></i></div>) : ""}
          <label className="pdfname" htmlFor="file-upload">
            {selectedFile && selectedFile.name.length > 12 ? (
              uploading ? "Uploading..." : `${selectedFile.name.slice(0, 8) + "..." + selectedFile.name.slice(-4)}`
            ) : selectedFile ? (
              uploading ? "Uploading..." : selectedFile.name
            ) : ""}
          </label>
          <label htmlFor="file-upload" className="custom-file-upload">
            <i className="ri-add-circle-line"></i><p>Upload PDF</p>
            <input id="file-upload" type="file" onChange={handleFileChange} accept="application/pdf" />
          </label>
        </div>
      </div>
      <div className="body">
        <div className="chat">
          {chatHistory.length > 0 ? (
            chatHistory.map((entry, index) => (
              <div key={index} className={entry.type === "user" ? "user-query" : "bot-response"}>
                <div className="profile">
                  <img className="icon" src={entry.type === "user" ? usericon : aiplanet}/>
                </div>
                <div className="texts">
                  <div className="markdown-body"><Markdown>{entry.text}</Markdown></div>
                </div>
              </div>
            ))
          ) : (
            <div className="no-chat-history"><div className="island">
                <h3>Instructions:</h3>
                <p>Upload a PDF: Click on "<i className="ri-add-circle-line"></i><span className="novisible">Upload PDF</span>" to select and upload a PDF document. Wait for the upload to complete.</p>
                <p>Enter Your Query: Once the PDF is uploaded, type your query in the input box and press the send button.</p>
            </div></div>
          )}
          <div ref={chatEndRef} /> 
        </div>
        <div className="inputbox">
          <div className="boxx">
            <input
              placeholder="Send a message..."
              type="text"
              value={query}
              onChange={handleQueryChange}
              onKeyPress={handleKeyPress}
            />
            <button
              className="sendbutton"
              onClick={handleQuery}
              disabled={!pdfUploaded || !query}
            >
              <i className="ri-send-plane-2-line"></i>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FileUpload;
