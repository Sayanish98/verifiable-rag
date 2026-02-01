import React, { useEffect, useRef } from "react";
import MessageBubble from "./MessageBubble";

export default function ConversationView({ 
  conversation, 
  question, 
  setQuestion, 
  loading, 
  onAsk, 
  onShowEvidence 
}) {
  const conversationEndRef = useRef(null);

  // Auto-scroll effect
  useEffect(() => {
    conversationEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [conversation]);

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !loading) {
      onAsk();
    }
  };

  return (
    <>
      {/* Inline CSS for markdown */}
      <style>
        {`
          .answerMessage table {
            border-collapse: collapse;
            width: 100%;
            margin: 15px 0;
            font-size: 14px;
          }
          .answerMessage th, .answerMessage td {
            border: 1px solid #ddd;
            padding: 10px;
            text-align: left;
          }
          .answerMessage th {
            background-color: #e8e8e8;
            font-weight: 600;
          }
          .answerMessage h3 {
            margin-top: 15px;
            margin-bottom: 10px;
            font-size: 16px;
            font-weight: 600;
            color: #333;
          }
          .answerMessage ul, .answerMessage ol {
            margin: 10px 0;
            padding-left: 25px;
          }
          .answerMessage li {
            margin: 5px 0;
          }
          .answerMessage strong {
            font-weight: 600;
          }
          .answerMessage code {
            background-color: #f0f0f0;
            padding: 2px 5px;
            border-radius: 3px;
            font-family: monospace;
          }
          .answerMessage p {
            margin: 8px 0;
          }
        `}
      </style>

      {/* Conversation Container */}
      <div style={styles.conversationContainer}>
        {conversation.map((msg, idx) => (
          <MessageBubble
            key={idx}
            message={msg}
            onShowEvidence={onShowEvidence}
          />
        ))}
        <div ref={conversationEndRef} />
      </div>

      {/* Bottom Input */}
      <div style={styles.bottomInputContainer}>
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Ask another question..."
          style={styles.bottomInput}
          disabled={loading}
        />
        <button
          onClick={onAsk}
          disabled={loading || !question.trim()}
          style={{
            ...styles.bottomButton,
            opacity: (loading || !question.trim()) ? 0.6 : 1
          }}
        >
          {loading ? "⏳" : "📤"}
        </button>
      </div>
    </>
  );
}

const styles = {
  conversationContainer: {
    flex: 1,
    overflowY: "auto",
    padding: "20px 0",
    display: "flex",
    flexDirection: "column",
  },
  bottomInputContainer: {
    padding: "20px 0",
    borderTop: "1px solid #e0e0e0",
    display: "flex",
    gap: "10px",
    backgroundColor: "white",
  },
  bottomInput: {
    flex: 1,
    padding: "12px 20px",
    fontSize: "15px",
    border: "2px solid #e0e0e0",
    borderRadius: "25px",
    outline: "none",
  },
  bottomButton: {
    width: "50px",
    height: "50px",
    backgroundColor: "#2196F3",
    color: "white",
    border: "none",
    borderRadius: "50%",
    fontSize: "20px",
    cursor: "pointer",
    transition: "background-color 0.3s",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  },
};
