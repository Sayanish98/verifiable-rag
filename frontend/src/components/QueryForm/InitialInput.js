import React from "react";

export default function InitialInput({ question, setQuestion, loading, onAsk }) {
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !loading) {
      onAsk();
    }
  };

  return (
    <div style={styles.centeredInputContainer}>
      <div style={styles.inputWrapper}>
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Ask a question about your medical documents..."
          style={styles.input}
          disabled={loading}
        />
        <button
          onClick={onAsk}
          disabled={loading || !question.trim()}
          style={{
            ...styles.button,
            opacity: (loading || !question.trim()) ? 0.6 : 1
          }}
        >
          {loading ? "🔍 Processing..." : "🔍 Ask"}
        </button>
      </div>
    </div>
  );
}

const styles = {
  centeredInputContainer: {
    flex: 1,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  },
  inputWrapper: {
    width: "100%",
    maxWidth: "600px",
    display: "flex",
    gap: "10px",
  },
  input: {
    flex: 1,
    padding: "15px 20px",
    fontSize: "16px",
    border: "2px solid #e0e0e0",
    borderRadius: "8px",
    outline: "none",
    transition: "border-color 0.3s",
  },
  button: {
    padding: "15px 30px",
    fontSize: "16px",
    backgroundColor: "#2196F3",
    color: "white",
    border: "none",
    borderRadius: "8px",
    cursor: "pointer",
    fontWeight: "500",
    whiteSpace: "nowrap",
    transition: "background-color 0.3s",
  },
};
