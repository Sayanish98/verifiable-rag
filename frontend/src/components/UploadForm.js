import React, { useState } from "react";

export default function UploadForm({ onUploadSuccess }) {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleUpload = async () => {
    if (!files.length) return;

    setLoading(true);
    const formData = new FormData();
    for (let file of files) formData.append("files", file);

    try {
      const res = await fetch("http://localhost:8000/upload", {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      onUploadSuccess(data);
    } catch (err) {
      console.error(err);
      alert("Upload failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <input
        type="file"
        multiple
        accept=".pdf"
        onChange={(e) => setFiles([...e.target.files])}
      />
      <button onClick={handleUpload} disabled={loading}>
        {loading ? "Uploading..." : "Upload PDFs"}
      </button>
    </div>
  );
}
