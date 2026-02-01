import React from "react";

export default function FileItem({ fileName, isDeleting, onDelete }) {
  return (
    <li style={styles.fileItem}>
      <div style={styles.fileInfo}>
        <span style={styles.fileIcon}>📄</span>
        <span style={styles.fileName}>{fileName}</span>
      </div>
      <button
        onClick={onDelete}
        disabled={isDeleting}
        style={styles.deleteButton}
        title="Delete this document"
      >
        {isDeleting ? "..." : "🗑️"}
      </button>
    </li>
  );
}

const styles = {
  fileItem: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    padding: "10px",
    backgroundColor: "#f9f9f9",
    borderRadius: "6px",
    marginBottom: "8px",
    transition: "background-color 0.2s",
  },
  fileInfo: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    flex: 1,
    minWidth: 0,
  },
  fileIcon: {
    fontSize: "18px",
    flexShrink: 0,
  },
  fileName: {
    fontSize: "14px",
    color: "#333",
    overflow: "hidden",
    textOverflow: "ellipsis",
    whiteSpace: "nowrap",
  },
  deleteButton: {
    backgroundColor: "transparent",
    border: "none",
    cursor: "pointer",
    fontSize: "18px",
    padding: "4px 8px",
    borderRadius: "4px",
    transition: "background-color 0.2s",
    flexShrink: 0,
    marginLeft: "8px",
  },
};
