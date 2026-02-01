import React, { useState, useEffect } from "react";
import Header from "./Header";
import EmptyState from "./EmptyState";
import InitialInput from "./InitialInput";
import ConversationView from "./ConversationView";
import EvidenceModal from "./EvidenceModal";
import ConfirmModal from "../common/ConfirmModal";

export default function QueryForm({ hasFiles }) {
  // State management
  const [question, setQuestion] = useState("");
  const [conversation, setConversation] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showEvidenceModal, setShowEvidenceModal] = useState(false);
  const [selectedEvidence, setSelectedEvidence] = useState([]);
  const [showClearModal, setShowClearModal] = useState(false);

  // Load conversation from sessionStorage on mount
  useEffect(() => {
    const saved = sessionStorage.getItem("ragConversation");
    if (saved) {
      setConversation(JSON.parse(saved));
    }
  }, []);

  // Save conversation to sessionStorage whenever it changes
  useEffect(() => {
    if (conversation.length > 0) {
      sessionStorage.setItem("ragConversation", JSON.stringify(conversation));
    }
  }, [conversation]);

  // Business logic functions
  const askQuestion = async () => {
    if (!question.trim()) return;
    
    const userQuestion = question.trim();
    setQuestion("");
    setLoading(true);

    // Add user question to conversation
    const newMessage = {
      type: "question",
      text: userQuestion,
      timestamp: new Date().toISOString(),
    };
    setConversation(prev => [...prev, newMessage]);

    try {
      const res = await fetch("http://localhost:8000/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          question: userQuestion,
          conversation_history: conversation
        }),
      });
      
      if (!res.ok) {
        throw new Error(`Server error: ${res.status}`);
      }
      
      const data = await res.json();
      
      // Add answer to conversation
      const answerMessage = {
        type: "answer",
        text: data.answer,
        evidence: data.evidence || [],
        timestamp: new Date().toISOString(),
      };
      setConversation(prev => [...prev, answerMessage]);
    } catch (err) {
      console.error(err);
      const errorMessage = {
        type: "error",
        text: "Sorry, something went wrong. Please try again.",
        timestamp: new Date().toISOString(),
      };
      setConversation(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const showEvidence = (evidence) => {
    setSelectedEvidence(evidence);
    setShowEvidenceModal(true);
  };

  const clearConversation = () => {
    setShowClearModal(true);
  };

  const confirmClearChat = () => {
    setConversation([]);
    sessionStorage.removeItem("ragConversation");
    setShowClearModal(false);
  };

  const cancelClearChat = () => {
    setShowClearModal(false);
  };

  // Show placeholder when no files are uploaded
  if (!hasFiles) {
    return <EmptyState />;
  }

  const hasConversation = conversation.length > 0;

  return (
    <div style={styles.container}>
      <Header 
        hasConversation={hasConversation}
        onClearChat={clearConversation}
      />
      
      {!hasConversation ? (
        <InitialInput
          question={question}
          setQuestion={setQuestion}
          loading={loading}
          onAsk={askQuestion}
        />
      ) : (
        <ConversationView
          conversation={conversation}
          question={question}
          setQuestion={setQuestion}
          loading={loading}
          onAsk={askQuestion}
          onShowEvidence={showEvidence}
        />
      )}

      {showEvidenceModal && (
        <EvidenceModal
          evidence={selectedEvidence}
          onClose={() => setShowEvidenceModal(false)}
        />
      )}

      {showClearModal && (
        <ConfirmModal
          title="Clear Chat History?"
          message="This will permanently delete your entire conversation history. This action cannot be undone."
          confirmText="Clear Chat"
          onConfirm={confirmClearChat}
          onCancel={cancelClearChat}
        />
      )}
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
};
