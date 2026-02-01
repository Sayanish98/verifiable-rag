import React from "react";
import ReactMarkdown from 'react-markdown';
import EvidenceButton from "./EvidenceButton";

export default function MessageBubble({ message, onShowEvidence }) {
  const { type, text, evidence } = message;

  if (type === "question") {
    return (
      <div style={styles.questionMessage}>
        <div style={styles.messageLabel}>You asked:</div>
        <div style={styles.messageText}>{text}</div>
      </div>
    );
  }

  if (type === "answer") {
    return (
      <div style={styles.answerMessage} className="answerMessage">
        <div style={styles.messageLabel}>Answer:</div>
        <div style={styles.messageText}>
          <ReactMarkdown>{text}</ReactMarkdown>
        </div>
        {evidence && evidence.length > 0 && (
          <EvidenceButton 
            evidence={evidence} 
            onShow={onShowEvidence} 
          />
        )}
      </div>
    );
  }

  if (type === "error") {
    return (
      <div style={styles.errorMessage}>
        <div style={styles.messageLabel}>Error:</div>
        <div style={styles.messageText}>{text}</div>
      </div>
    );
  }

  return null;
}

const styles = {
  questionMessage: {
    maxWidth: "70%",
    alignSelf: "flex-end",
    backgroundColor: "#E3F2FD",
    padding: "12px 16px",
    borderRadius: "12px 12px 0 12px",
    marginBottom: "16px",
  },
  answerMessage: {
    maxWidth: "85%",
    alignSelf: "flex-start",
    backgroundColor: "#f5f5f5",
    padding: "12px 16px",
    borderRadius: "12px 12px 12px 0",
    marginBottom: "16px",
  },
  errorMessage: {
    maxWidth: "70%",
    alignSelf: "center",
    backgroundColor: "#ffebee",
    color: "#c62828",
    padding: "12px 16px",
    borderRadius: "8px",
    marginBottom: "8px",
  },
  messageLabel: {
    fontSize: "11px",
    fontWeight: "600",
    opacity: 0.7,
    marginBottom: "6px",
    textTransform: "uppercase",
  },
  messageText: {
    fontSize: "15px",
    lineHeight: "1.6",
    margin: 0,
  },
};
