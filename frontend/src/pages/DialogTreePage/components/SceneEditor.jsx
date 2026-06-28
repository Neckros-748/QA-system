// components/SceneEditor.jsx
import React, { useState, useEffect } from "react";
import { documentsApi } from "../../../api/documents";
import "./SceneEditor.css";

export default function SceneEditor({ sceneName, onSave, onDelete }) {
  const [scene, setScene] = useState(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (sceneName) {
      loadScene();
    } else {
      setScene(null);
    }
  }, [sceneName]);

  const loadScene = async () => {
    try {
      setLoading(true);
      const response = await documentsApi.getScene(sceneName);
      if (response.success) {
        setScene(response.scene);
        setError(null);
      } else {
        setError(response.error || "Ошибка загрузки сцены");
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
      const response = await documentsApi.updateScene(sceneName, scene);
      if (response.success) {
        onSave?.(response.scene);
      } else {
        setError(response.error || "Ошибка сохранения");
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!confirm(`Удалить сцену "${sceneName}"?`)) return;
    try {
      const response = await documentsApi.deleteScene(sceneName);
      if (response.success) {
        onDelete?.(sceneName);
      } else {
        setError(response.error || "Ошибка удаления");
      }
    } catch (err) {
      setError(err.message);
    }
  };

  const handleChange = (field, value) => {
    setScene(prev => ({ ...prev, [field]: value }));
  };

  if (!sceneName) {
    return (
      <div className="scene-editor empty">
        <p>Выберите сцену из дерева слева</p>
      </div>
    );
  }

  if (loading) {
    return <div className="scene-editor loading">Загрузка сцены...</div>;
  }

  if (error) {
    return <div className="scene-editor error">{error}</div>;
  }

  if (!scene) {
    return <div className="scene-editor empty">Сцена не найдена</div>;
  }

  return (
    <div className="scene-editor">
      <div className="scene-header">
        <h3>📝 {scene.name || "Новая сцена"}</h3>
        <div className="scene-actions">
          <button
            className="btn btn--primary"
            onClick={handleSave}
            disabled={saving}
          >
            {saving ? "Сохранение..." : "💾 Сохранить"}
          </button>
          <button
            className="btn btn--danger"
            onClick={handleDelete}
          >
            🗑 Удалить
          </button>
        </div>
      </div>

      <div className="scene-form">
        <div className="form-group">
          <label>Название сцены</label>
          <input
            type="text"
            value={scene.name || ""}
            onChange={(e) => handleChange("name", e.target.value)}
            placeholder="Введите название сцены"
          />
        </div>

        <div className="form-group">
          <label>Шаблон ответа</label>
          <textarea
            value={scene.answer_template || ""}
            onChange={(e) => handleChange("answer_template", e.target.value)}
            placeholder="Введите шаблон ответа с {переменными}"
            rows={6}
          />
        </div>

        <div className="form-group">
          <label>Краткий ответ</label>
          <textarea
            value={scene.short_answer || ""}
            onChange={(e) => handleChange("short_answer", e.target.value)}
            placeholder="Краткий ответ на вопрос"
            rows={2}
          />
        </div>

        <div className="form-group">
          <label>Уточняющий вопрос</label>
          <textarea
            value={scene.clarifying_question || ""}
            onChange={(e) => handleChange("clarifying_question", e.target.value)}
            placeholder="Вопрос для уточнения"
            rows={2}
          />
        </div>

        <div className="form-group">
          <label>Доступные интенты</label>
          <input
            type="text"
            value={(scene.available_intents_list || []).join(", ")}
            onChange={(e) => {
              const intents = e.target.value.split(",").map(s => s.trim()).filter(Boolean);
              handleChange("available_intents_list", intents);
            }}
            placeholder="intent1, intent2, intent3"
          />
        </div>

        <div className="form-group">
          <label>Условия перехода</label>
          <textarea
            value={(scene.pass_conditions || []).map(cond => cond.join(", ")).join("\n")}
            onChange={(e) => {
              const conditions = e.target.value
                .split("\n")
                .filter(Boolean)
                .map(line => line.split(",").map(s => s.trim()).filter(Boolean));
              handleChange("pass_conditions", conditions);
            }}
            placeholder="условие1, условие2, условие3&#10;условие4, условие5"
            rows={3}
          />
        </div>

        <div className="form-group">
          <label>Высота сцены (автоматически)</label>
          <input
            type="number"
            value={scene.height || 0}
            readOnly
            className="readonly"
          />
        </div>
      </div>
    </div>
  );
}