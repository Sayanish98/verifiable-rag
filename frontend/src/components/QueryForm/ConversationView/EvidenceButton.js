import React from "react";

export default function EvidenceButton({ evidence, onShow }) {
  return (
    <button
      onClick={() => onShow(evidence)}
      style={styles.evidenceButton}
    >
      📚 View Evidence ({evidence.length} sources)
    </button>
  );
}

const styles = {
  evidenceButton: {
    marginTop: "12px",
    padding: "8px 16px",
    fontSize: "13px",
    backgroundColor: "#f0f0f0",
    color: "#2196F3",
    border: "1px solid #2196F3",
    borderRadius: "6px",
    cursor: "pointer",
    fontWeight: "500",
    transition: "all 0.2s",
  },
};
