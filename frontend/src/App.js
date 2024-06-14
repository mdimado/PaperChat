import React, { useState, useRef, useEffect } from "react";
import axios from "axios";
import "./App.css";
import Markdown from 'react-markdown';

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
      const response = await axios.post("https://paperchat-api.onrender.com/upload/", formData, {
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
    if (!query) return;

    const newChatHistory = [...chatHistory, { type: "user", text: query }];
    setChatHistory(newChatHistory); 
    setQuery(""); 
    setResponse(""); 

    try {
      const response = await fetch('https://paperchat-api.onrender.com/query/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: query,
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

  return (
    <div className="main">
      <div className="header">
        <img src="https://proxmaq.com/wp-content/uploads/2023/03/AI_Planet-logo.jpg" alt="AI Planet Logo"/>
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
          {chatHistory.map((entry, index) => (
            <div key={index} className={entry.type === "user" ? "user-query" : "bot-response"}>
              <div className="profile">
                <img className="icon" src={entry.type === "user" ? "https://static.vecteezy.com/system/resources/thumbnails/007/461/014/small/profile-gradient-logo-design-template-icon-vector.jpg" : "https://yt3.googleusercontent.com/9RnnCIf9OpQ2vpNowrYw_QAcG3tPSI2iaElvIM7-B13hHwynyZzgnXAm9h8AwwG-gfOnKOT4224=s900-c-k-c0x00ffffff-no-rj"}/>
              </div>
              <div className="texts"><div><Markdown>{entry.text}</Markdown></div></div>
            </div>
          ))}
          <div ref={chatEndRef} /> 
        </div>
        <div className="inputbox">
          <div className="boxx">
            <input placeholder="Send a message..." type="text" value={query} onChange={handleQueryChange} />
            <button className="sendbutton" onClick={handleQuery} disabled={!pdfUploaded || !query}><i className="ri-send-plane-2-line"></i></button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FileUpload;
