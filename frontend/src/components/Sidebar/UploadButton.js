import React from "react";

export default function UploadButton({ loading, setLoading, onUploadComplete }) {
  const handleFileSelect = async (e) => {
    const selectedFiles = [...e.target.files];
    if (!selectedFiles.length) return;

    setLoading(true);
    const formData = new FormData();
    for (let file of selectedFiles) {
      formData.append("files", file);
    }

    try {
      const res = await fetch("http://localhost:8000/upload", {
        method: "POST",
        body: formData,
      });
      
      if (!res.ok) {
        throw new Error(`Upload failed: ${res.status}`);
      }
      
      const data = await res.json();
      onUploadComplete(data.message, selectedFiles);
      
      // Reset file input
      e.target.value = null;
    } catch (err) {
      console.error(err);
      alert("Upload failed: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.uploadSection}>
      <label style={{...styles.uploadButton, opacity: loading ? 0.6 : 1}}>
        <input
          type="file"
          multiple
          accept=".pdf"
          onChange={handleFileSelect}
          style={{ display: "none" }}
          disabled={loading}
        />
        {loading ? "⏳ Uploading..." : "📁 Choose & Upload PDFs"}
      </label>
    </div>
  );
}

const styles = {
  uploadSection: {
    padding: "10px 0",
    display: "flex",
    justifyContent: "center",
  },
  uploadButton: {
    display: "block",
    width: "85%",
    padding: "12px",
    backgroundColor: "#2196F3",
    color: "white",
    textAlign: "center",
    borderRadius: "8px",
    cursor: "pointer",
    fontWeight: "500",
    transition: "background-color 0.3s",
    border: "none",
  },
};
