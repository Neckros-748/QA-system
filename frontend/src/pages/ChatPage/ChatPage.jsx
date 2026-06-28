import React, { useState, useRef, useEffect } from "react";
import { documentsApi } from "../../api/documents";
import "./ChatPage.css";

export default function ChatPage() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [mode, setMode] = useState("llm"); // "llm" или "dialog-tree"
  const messagesEndRef = useRef(null);

  // Автоматическая прокрутка вниз при новых сообщениях
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async () => {
    const question = input.trim();
    if (!question || loading) return;

    // Добавляем сообщение пользователя
    const userMessage = { role: "user", content: question };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      let response;

      if (mode === "dialog-tree") {
        // Дерево диалога
        response = await documentsApi.askWithDialogTree(question, messages);
      } else {
        // LLM
        response = await documentsApi.ask(question);
      }

      if (response.success) {
        const assistantMessage = {
          role: "assistant",
          content: response.answer,
          context: response.context,
          //dialogTree: response.dialog_tree || null,
        };
        setMessages((prev) => [...prev, assistantMessage]);
      } else {
        throw new Error(response.error || "Неизвестная ошибка");
      }
    } catch (error) {
      console.error("Ошибка чата:", error);
      const errorMessage = {
        role: "assistant",
        content: `Ошибка: ${error.message || "Не удалось получить ответ"}`,
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const toggleMode = () => {
    setMode((prev) => (prev === "llm" ? "dialog-tree" : "llm"));
  };

  const formatMessage = (msg) => {
    if (msg.role === "user") return msg.content;

    if (mode === "dialog-tree" && msg.dialogTree) {
      return `${msg.content}\n\n🌳 Структура диалога:\n${JSON.stringify(msg.dialogTree, null, 2)}`;
    }

    if (mode === "llm" && msg.context) {
      return `${msg.content}\n\n📎 Контекст:\n${msg.context}`;
    }

    return msg.content;
  };

  return (
    <section className="chat-page">
      <div className="chat-container">
        {/* Заголовок чата */}
        <div className="chat-header">
          <div className="chat-header-left">
            <h1>Чат с документами</h1>
            <p className="chat-subtitle">
                {mode === "dialog-tree"
                    ? "🌳 Режим: Дерево диалога"
                    : "🤖 Режим: LLM"}
            </p>
          </div>
          <button
            className={`btn mode-toggle-btn ${mode === "dialog-tree" ? "btn--active" : ""}`}
            onClick={toggleMode}
            title={mode === "llm" ? "Переключить на дерево диалога" : "Переключить на LLM"}
          >
            {mode === "llm" ? "🌳 Дерево диалога" : "🤖 LLM"}
          </button>
        </div>

        {/* Область сообщений */}
        <div className="chat-messages">
          {messages.length === 0 && (
            <div className="chat-empty">
              <span>💬</span>
              <p>Начните диалог, задав вопрос о документах</p>
            </div>
          )}
          {messages.map((msg, index) => (
            <div
              key={index}
              className={`message ${msg.role === "user" ? "message-user" : "message-assistant"}`}
            >
              <div className="message-content">
                {msg.role === "user" ? (
                  <span className="message-icon">👤</span>
                ) : (
                  <span className="message-icon">
                    {mode === "dialog-tree" ? "🌳" : "🤖"}
                  </span>
                )}
                <div className="message-text" style={{ whiteSpace: "pre-wrap" }}>
                  {formatMessage(msg)}
                </div>
              </div>
            </div>
          ))}
          {loading && (
            <div className="message message-assistant">
              <div className="message-content">
                <span className="message-icon">
                  {mode === "dialog-tree" ? "🌳" : "🤖"}
                </span>
                <div className="message-text typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Поле ввода */}
        <div className="chat-input-area">
          <textarea
            className="chat-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Введите ваш вопрос..."
            rows={3}
            disabled={loading}
          />
          <button
            className="btn btn--primary chat-send-btn"
            onClick={handleSend}
            disabled={loading || !input.trim()}
          >
            {loading ? "Отправка..." : "Отправить"}
          </button>
        </div>
      </div>
    </section>
  );
}