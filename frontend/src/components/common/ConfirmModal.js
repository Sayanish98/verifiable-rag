import React from "react";

export default function ConfirmModal({ 
  title, 
  message, 
  confirmText, 
  confirmStyle = "delete", // "delete" or "primary"
  onConfirm, 
  onCancel 
}) {
  return (
    <div style={styles.modalOverlay} onClick={onCancel}>
      <div style={styles.modalContent} onClick={(e) => e.stopPropagation()}>
        <h3 style={styles.modalTitle}>{title}</h3>
        <p style={styles.modalText}>{message}</p>
        <div style={styles.modalButtons}>
          <button onClick={onCancel} style={styles.cancelButton}>
            Cancel
          </button>
          <button 
            onClick={onConfirm} 
            style={confirmStyle === "delete" ? styles.confirmDeleteButton : styles.confirmButton}
          >
            {confirmText}
          </button>
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
    padding: "30px",
    maxWidth: "400px",
    width: "90%",
    boxShadow: "0 8px 32px rgba(0,0,0,0.3)",
    border: "4px solid #1976D2",
  },
  modalTitle: {
    fontSize: "20px",
    fontWeight: "600",
    marginBottom: "15px",
    color: "#333",
    margin: "0 0 15px 0",
  },
  modalText: {
    fontSize: "15px",
    color: "#666",
    marginBottom: "25px",
    lineHeight: "1.5",
  },
  modalButtons: {
    display: "flex",
    gap: "10px",
    justifyContent: "flex-end",
  },
  cancelButton: {
    padding: "10px 20px",
    fontSize: "14px",
    backgroundColor: "#e0e0e0",
    color: "#333",
    border: "none",
    borderRadius: "6px",
    cursor: "pointer",
    fontWeight: "500",
  },
  confirmDeleteButton: {
    padding: "10px 20px",
    fontSize: "14px",
    backgroundColor: "#f44336",
    color: "white",
    border: "none",
    borderRadius: "6px",
    cursor: "pointer",
    fontWeight: "500",
  },
  confirmButton: {
    padding: "10px 20px",
    fontSize: "14px",
    backgroundColor: "#2196F3",
    color: "white",
    border: "none",
    borderRadius: "6px",
    cursor: "pointer",
    fontWeight: "500",
  },
};
