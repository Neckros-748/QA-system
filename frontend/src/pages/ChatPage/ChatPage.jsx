import React, { useState, useRef, useEffect } from "react";
import { documentsApi } from "../../api/documents";
import "./ChatPage.css";

export default function ChatPage() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
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
      const response = await documentsApi.ask(question);
      if (response.success) {
        const assistantMessage = {
          role: "assistant",
          content: response.answer,
          context: response.context, // можно не отображать, но сохранить
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

  return (
    <section className="chat-page">
      <div className="chat-container">
        {/* Заголовок чата */}
        <div className="chat-header">
          <h1>Чат с документами</h1>
          <p className="chat-subtitle">
            Задайте вопрос по загруженным документам
          </p>
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
                  <span className="message-icon">🤖</span>
                )}
                <div className="message-text">{msg.content}</div>
              </div>
            </div>
          ))}
          {loading && (
            <div className="message message-assistant">
              <div className="message-content">
                <span className="message-icon">🤖</span>
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