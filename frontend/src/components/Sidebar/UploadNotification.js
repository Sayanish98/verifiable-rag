import React, { useEffect } from "react";

export default function UploadNotification({ message }) {
  // Add slideUp animation to stylesheet
  useEffect(() => {
    const styleSheet = document.styleSheets[0];
    if (styleSheet) {
      try {
        styleSheet.insertRule(`
          @keyframes slideUp {
            from {
              transform: translateY(100%);
              opacity: 0;
            }
            to {
              transform: translateY(0);
              opacity: 1;
            }
          }
        `, styleSheet.cssRules.length);
      } catch (e) {
        // Animation already exists
      }
    }
  }, []);

  return (
    <div style={styles.uploadNotification}>
      ✓ {message}
    </div>
  );
}

const styles = {
  uploadNotification: {
    position: "absolute",
    bottom: "20px",
    left: "10px",
    right: "10px",
    padding: "12px",
    backgroundColor: "#4CAF50",
    color: "white",
    textAlign: "center",
    borderRadius: "6px",
    fontSize: "14px",
    fontWeight: "500",
    boxShadow: "0 2px 8px rgba(0,0,0,0.2)",
    animation: "slideUp 0.3s ease-out",
  },
};
