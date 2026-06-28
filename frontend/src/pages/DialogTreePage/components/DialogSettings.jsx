// src/pages/DialogTreePage/components/DialogSettings.jsx
import React, { useState, useEffect } from "react";
import { documentsApi } from "../../../api/documents";
import "./DialogSettings.css";

export default function DialogSettings({
  onSettingsChange,
  isOpen,
  onToggle
}) {
  const [settings, setSettings] = useState({
    max_context_messages: 10,
    fixed_first_messages: 3
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await documentsApi.getDialogSettings();
      if (response.success) {
        setSettings(response.settings);
        if (onSettingsChange) {
          onSettingsChange(response.settings);
        }
      } else {
        setError(response.error || "Ошибка загрузки настроек");
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      setError(null);
      setSuccess(false);

      const response = await documentsApi.updateDialogSettings(settings);
      if (response.success) {
        setSuccess(true);
        if (onSettingsChange) {
          onSettingsChange(settings);
        }
        setTimeout(() => setSuccess(false), 3000);
      } else {
        setError(response.error || "Ошибка сохранения настроек");
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  const handleChange = (field, value) => {
    const numValue = parseInt(value) || 0;
    setSettings(prev => ({
      ...prev,
      [field]: Math.max(0, numValue)
    }));
  };

  if (loading) {
    return <div className="dialog-settings loading">⏳ Загрузка настроек...</div>;
  }

  return (
    <div className={`dialog-settings ${isOpen ? "expanded" : "collapsed"}`}>
      <div className="settings-body">
        {error && (
          <div className="settings-error">❌ {error}</div>
        )}

        {success && (
          <div className="settings-success">✅ Настройки сохранены!</div>
        )}

        <div className="setting-group">
          <label htmlFor="max_context_messages">
            Максимальное количество сообщений в контексте
          </label>
          <div className="setting-control">
            <input
              id="max_context_messages"
              type="number"
              min="1"
              max="100"
              value={settings.max_context_messages}
              onChange={(e) => handleChange("max_context_messages", e.target.value)}
            />
            <span className="setting-hint">
              Сообщения сверх этого лимита будут удаляться
            </span>
          </div>
        </div>

        <div className="setting-group">
          <label htmlFor="fixed_first_messages">
            Количество первых (незамещаемых) сообщений
          </label>
          <div className="setting-control">
            <input
              id="fixed_first_messages"
              type="number"
              min="0"
              max="50"
              value={settings.fixed_first_messages}
              onChange={(e) => handleChange("fixed_first_messages", e.target.value)}
            />
            <span className="setting-hint">
              Эти сообщения всегда остаются в контексте
            </span>
          </div>
        </div>

        <div className="settings-info">
          <p>💡 <strong>Как это работает:</strong></p>
          <ul>
            <li>
              <strong>Максимальное количество сообщений</strong> —
              ограничивает общее количество сообщений в контексте.
              При превышении лимита удаляются старые сообщения.
            </li>
            <li>
              <strong>Незамещаемые сообщения</strong> —
              это количество первых сообщений, которые никогда не удаляются
              (обычно это системный промпт и начальный контекст).
            </li>
            <li>
              Текущий контекст:
              <strong> {settings.fixed_first_messages} </strong>
              фиксированных + до
              <strong> {Math.max(0, settings.max_context_messages - settings.fixed_first_messages)} </strong>
              динамических сообщений
            </li>
          </ul>
        </div>

        <div className="settings-footer">
          <button
            className="btn btn--primary"
            onClick={handleSave}
            disabled={saving}
          >
            {saving ? "⏳ Сохранение..." : "💾 Сохранить"}
          </button>
          <button
            className="btn"
            onClick={loadSettings}
            disabled={loading}
          >
            🔄 Сбросить
          </button>
        </div>
      </div>
    </div>
  );
}