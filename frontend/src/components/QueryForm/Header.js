import React from "react";

export default function Header({ hasConversation, onClearChat }) {
  return (
    <div style={styles.header}>
      <h1 style={styles.mainTitle}>Medical RAG Assistant</h1>
      <p style={styles.mainDescription}>
        Ask questions about your medical documents and get answers with verifiable evidence
      </p>
      {hasConversation && (
        <button onClick={onClearChat} style={styles.clearButton}>
          🗑️ Clear Chat
        </button>
      )}
    </div>
  );
}

const styles = {
  header: {
    textAlign: "center",
    padding: "20px 20px 30px",
    borderBottom: "1px solid #e0e0e0",
    position: "relative",
  },
  mainTitle: {
    fontSize: "28px",
    fontWeight: "700",
    color: "#1976D2",
    marginBottom: "8px",
  },
  mainDescription: {
    fontSize: "14px",
    color: "#666",
    margin: 0,
  },
  clearButton: {
    position: "absolute",
    top: "20px",
    right: "20px",
    padding: "8px 16px",
    fontSize: "14px",
    backgroundColor: "#f44336",
    color: "white",
    border: "none",
    borderRadius: "6px",
    cursor: "pointer",
    fontWeight: "500",
    transition: "background-color 0.2s",
  },
};
