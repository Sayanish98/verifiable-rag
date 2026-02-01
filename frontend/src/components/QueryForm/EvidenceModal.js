import React from "react";

export default function EvidenceModal({ evidence, onClose }) {
  return (
    <div style={styles.modalOverlay} onClick={onClose}>
      <div style={styles.modalContent} onClick={(e) => e.stopPropagation()}>
        <div style={styles.modalHeader}>
          <h3 style={styles.modalTitle}>📚 Evidence Sources</h3>
          <button onClick={onClose} style={styles.closeButton}>
            ✕
          </button>
        </div>
        <div style={styles.modalBody}>
          {evidence.map((e, idx) => (
            <div key={idx} style={styles.evidenceItem}>
              <div style={styles.evidenceHeader}>
                <span style={styles.evidenceNumber}>#{idx + 1}</span>
                <strong style={styles.evidenceSource}>
                  {e.doc_name} - Page {e.page_number}
                </strong>
              </div>
              <p style={styles.evidenceText}>{e.text}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

const styles = {
  modalOverlay: {
    position: "fixed",
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: "rgba(0, 0, 0, 0.6)",
    backdropFilter: "blur(5px)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    zIndex: 9999,
  },
  modalContent: {
    backgroundColor: "white",
    borderRadius: "12px",
    maxWidth: "700px",
    maxHeight: "80vh",
    width: "90%",
    display: "flex",
    flexDirection: "column",
    boxShadow: "0 4px 20px rgba(0,0,0,0.2)",
    border: "4px solid #1976D2",
  },
  modalHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    padding: "20px",
    borderBottom: "1px solid #e0e0e0",
  },
  modalTitle: {
    margin: 0,
    fontSize: "20px",
    fontWeight: "600",
    color: "#333",
  },
  closeButton: {
    background: "none",
    border: "none",
    fontSize: "24px",
    cursor: "pointer",
    color: "#999",
    padding: "0",
    width: "30px",
    height: "30px",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  },
  modalBody: {
    padding: "20px",
    overflowY: "auto",
    flex: 1,
  },
  evidenceItem: {
    backgroundColor: "#f9f9f9",
    padding: "15px",
    borderRadius: "8px",
    marginBottom: "12px",
    border: "1px solid #e0e0e0",
  },
  evidenceHeader: {
    display: "flex",
    alignItems: "center",
    gap: "10px",
    marginBottom: "10px",
  },
  evidenceNumber: {
    backgroundColor: "#4CAF50",
    color: "white",
    padding: "3px 10px",
    borderRadius: "12px",
    fontSize: "12px",
    fontWeight: "600",
  },
  evidenceSource: {
    color: "#2196F3",
    fontSize: "14px",
  },
  evidenceText: {
    fontSize: "14px",
    lineHeight: "1.6",
    color: "#333",
    margin: 0,
  },
};
