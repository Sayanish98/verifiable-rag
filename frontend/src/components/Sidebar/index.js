import React, { useState } from "react";
import UploadButton from "./UploadButton";
import FileList from "./FileList";
import UploadNotification from "./UploadNotification";
import ConfirmModal from "../common/ConfirmModal";

export default function Sidebar({ uploadedFiles, onUploadSuccess, onDeleteFile }) {
  // State management
  const [loading, setLoading] = useState(false);
  const [deleting, setDeleting] = useState(null);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [fileToDelete, setFileToDelete] = useState(null);
  const [uploadMessage, setUploadMessage] = useState("");

  // Upload handling
  const handleUploadComplete = (message, files) => {
    setUploadMessage(message);
    onUploadSuccess(files);
    setTimeout(() => setUploadMessage(""), 3000);
  };

  // Delete handling
  const handleDelete = (fileName) => {
    setFileToDelete(fileName);
    setShowDeleteModal(true);
  };

  const confirmDelete = async () => {
    if (!fileToDelete) return;
    setDeleting(fileToDelete);
    
    try {
      const res = await fetch("http://localhost:8000/delete-document", {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ doc_name: fileToDelete }),
      });

      if (!res.ok) {
        throw new Error(`Delete failed: ${res.status}`);
      }

      const data = await res.json();
      onDeleteFile(fileToDelete);
    } catch (err) {
      console.error(err);
      alert("Delete failed: " + err.message);
    } finally {
      setDeleting(null);
      setShowDeleteModal(false);
      setFileToDelete(null);
    }
  };

  const cancelDelete = () => {
    setShowDeleteModal(false);
    setFileToDelete(null);
  };

  return (
    <>
      <div style={styles.sidebar}>
        <h2 style={styles.title}>Document Manager</h2>
        
        <UploadButton 
          loading={loading}
          setLoading={setLoading}
          onUploadComplete={handleUploadComplete}
        />
        
        <hr style={styles.divider} />
        
        <FileList
          files={uploadedFiles}
          deleting={deleting}
          onDelete={handleDelete}
        />

        {uploadMessage && (
          <UploadNotification message={uploadMessage} />
        )}
      </div>

      {showDeleteModal && (
        <ConfirmModal
          title="Delete File?"
          message={
            <>
              Are you sure you want to delete <strong>{fileToDelete}</strong>?
              <br />This will remove all associated data from the vector database.
            </>
          }
          confirmText="Delete"
          confirmStyle="delete"
          onConfirm={confirmDelete}
          onCancel={cancelDelete}
        />
      )}
    </>
  );
}

const styles = {
  sidebar: {
    width: "300px",
    height: "100vh",
    backgroundColor: "#f5f5f5",
    borderRight: "1px solid #e0e0e0",
    padding: "20px",
    display: "flex",
    flexDirection: "column",
    position: "fixed",
    left: 0,
    top: 0,
  },
  title: {
    fontSize: "20px",
    fontWeight: "600",
    color: "#333",
    marginBottom: "20px",
    textAlign: "center",
  },
  divider: {
    border: "none",
    borderTop: "1px solid #e0e0e0",
    margin: "15px 0",
  },
};
