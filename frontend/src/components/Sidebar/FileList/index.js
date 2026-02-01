import React from "react";
import FileItem from "./FileItem";

export default function FileList({ files, deleting, onDelete }) {
  return (
    <div style={styles.filesSection}>
      <h3 style={styles.sectionTitle}>Uploaded Files</h3>
      {files.length === 0 ? (
        <p style={styles.emptyMessage}>No files uploaded yet</p>
      ) : (
        <ul style={styles.fileList}>
          {files.map((file, idx) => (
            <FileItem
              key={idx}
              fileName={file}
              isDeleting={deleting === file}
              onDelete={() => onDelete(file)}
            />
          ))}
        </ul>
      )}
    </div>
  );
}

const styles = {
  filesSection: {
    flex: 1,
    overflowY: "auto",
    padding: "10px 0",
  },
  sectionTitle: {
    fontSize: "16px",
    fontWeight: "600",
    color: "#333",
    marginBottom: "10px",
  },
  emptyMessage: {
    fontSize: "14px",
    color: "#999",
    fontStyle: "italic",
    textAlign: "center",
    padding: "20px 0",
  },
  fileList: {
    listStyle: "none",
    padding: 0,
    margin: 0,
  },
};
