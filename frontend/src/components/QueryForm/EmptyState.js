import React from "react";
import Header from "./Header";

export default function EmptyState() {
  return (
    <div style={styles.container}>
      <Header hasConversation={false} onClearChat={() => {}} />
      <div style={styles.emptyState}>
        <div style={styles.emptyIcon}>📁</div>
        <h2 style={styles.emptyTitle}>No Documents Uploaded</h2>
        <p style={styles.emptyText}>
          Upload your medical files from the sidebar to get started
        </p>
      </div>
    </div>
  );
}

const styles = {
  container: {
    display: "flex",
    flexDirection: "column",
    height: "100%",
    padding: "0 40px",
  },
  emptyState: {
    flex: 1,
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    color: "#999",
  },
  emptyIcon: {
    fontSize: "80px",
    marginBottom: "20px",
    opacity: 0.5,
  },
  emptyTitle: {
    fontSize: "24px",
    fontWeight: "600",
    marginBottom: "10px",
    color: "#666",
  },
  emptyText: {
    fontSize: "16px",
    color: "#999",
  },
};
