import React, { useState } from "react";
import Sidebar from "./components/Sidebar";
import QueryForm from "./components/QueryForm";

function App() {
  const [uploadedFiles, setUploadedFiles] = useState([]);

  const handleUploadSuccess = (files) => {
    const fileNames = files.map(f => f.name);
    setUploadedFiles(prev => [...prev, ...fileNames]);
  };

  const handleDeleteFile = (fileName) => {
    setUploadedFiles(prev => prev.filter(f => f !== fileName));
  };

  return (
    <div style={{ display: "flex", height: "100vh", fontFamily: "Arial, sans-serif" }}>
      <Sidebar 
        uploadedFiles={uploadedFiles} 
        onUploadSuccess={handleUploadSuccess}
        onDeleteFile={handleDeleteFile}
      />
      
      <div style={{ 
        marginLeft: "330px", 
        flex: 1, 
        display: "flex", 
        flexDirection: "column",
        overflow: "hidden"
      }}>
        <QueryForm hasFiles={uploadedFiles.length > 0} />
      </div>
    </div>
  );
}

export default App;
