// src/pages/DialogTreePage/components/DialogTreeView.jsx
import React, { useState, useEffect } from "react";
import { documentsApi } from "../../../api/documents";
import "./DialogTreeView.css";

function TreeNode({ node, onSelect, selected, level = 0 }) {
  const [expanded, setExpanded] = useState(true);

  if (!node) return null;

  return (
    <div className="tree-node" style={{ paddingLeft: `${level * 20}px` }}>
      <div
        className={`tree-node-label ${selected === node.name ? "selected" : ""}`}
        onClick={() => onSelect(node.name)}
      >
        {node.children && node.children.length > 0 && (
          <button
            className="tree-toggle"
            onClick={(e) => {
              e.stopPropagation();
              setExpanded(!expanded);
            }}
          >
            {expanded ? "▼" : "▶"}
          </button>
        )}
        <span className="tree-node-icon">📄</span>
        <span className="tree-node-name">{node.name || "Корень"}</span>
      </div>
      {expanded && node.children && node.children.length > 0 && (
        <div className="tree-children">
          {node.children.map((child, index) => (
            <TreeNode
              key={index}
              node={child}
              onSelect={onSelect}
              selected={selected}
              level={level + 1}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export default function DialogTreeView({
  onSelectScene,
  selectedScene,
  onTreeUpdate,
  onSettingsToggle,
  isSettingsOpen
}) {
  const [treeData, setTreeData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [treeInfo, setTreeInfo] = useState(null);
  const [creating, setCreating] = useState(false);
  const [showAddModal, setShowAddModal] = useState(false);
  const [newSceneName, setNewSceneName] = useState("");
  const [newSceneParent, setNewSceneParent] = useState("root");
  const [addLoading, setAddLoading] = useState(false);

  useEffect(() => {
    loadTree();
  }, []);

  const loadTree = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await documentsApi.getDialogTree();
      if (response.success) {
        setTreeData(response.tree);
        if (response.info) {
          setTreeInfo(response.info);
        }
      } else {
        setError(response.error || "Ошибка загрузки дерева");
      }
    } catch (err) {
      console.error("Ошибка загрузки дерева:", err);
      setError(err.message || "Не удалось загрузить дерево");
    } finally {
      setLoading(false);
    }
  };

  const handleCreateDefaultTree = async () => {
    if (!confirm("Создать дерево с примерами? Текущее дерево будет заменено.")) return;

    try {
      setCreating(true);
      const response = await documentsApi.createDefaultTree();
      if (response.success) {
        setTreeData(response.tree);
        setError(null);
        alert("✅ Дерево с примерами создано!");
        if (onTreeUpdate) {
          onTreeUpdate();
        }
      } else {
        alert(`❌ Ошибка: ${response.error || "Не удалось создать дерево"}`);
      }
    } catch (err) {
      alert(`❌ Ошибка: ${err.message}`);
    } finally {
      setCreating(false);
    }
  };

  const handleAddScene = async () => {
    if (!newSceneName.trim()) {
      alert("Введите название сцены");
      return;
    }

    try {
      setAddLoading(true);
      const response = await documentsApi.createScene(newSceneParent, {
        name: newSceneName.trim(),
        answer_template: "",
        short_answer: "",
        clarifying_question: "",
        available_intents_list: [],
        pass_conditions: []
      });

      if (response.success) {
        alert(`✅ Сцена "${newSceneName}" создана!`);
        setShowAddModal(false);
        setNewSceneName("");
        await loadTree();
        if (response.scene && response.scene.name) {
          onSelectScene(response.scene.name);
        }
        if (onTreeUpdate) {
          onTreeUpdate();
        }
      } else {
        alert(`❌ Ошибка: ${response.error || "Не удалось создать сцену"}`);
      }
    } catch (err) {
      alert(`❌ Ошибка: ${err.message}`);
    } finally {
      setAddLoading(false);
    }
  };

  const isEmpty = treeData && treeData.children && treeData.children.length === 0;

  if (loading) return <div className="tree-loading">⏳ Загрузка дерева...</div>;
  if (error) return (
    <div className="tree-error">
      <span className="error-icon">❌</span>
      <p>{error}</p>
      <button className="btn btn--small" onClick={loadTree}>Повторить</button>
    </div>
  );
  if (!treeData) return <div className="tree-empty">Дерево пусто</div>;

  return (
    <div className="dialog-tree-view">
      <div className="tree-header">
        <h3>🌳 Дерево диалога</h3>
        <div style={{ display: "flex", gap: "6px" }}>
          {isEmpty && (
            <button
              className="btn btn--primary btn--small"
              onClick={handleCreateDefaultTree}
              disabled={creating}
            >
              {creating ? "⏳" : "📝 Создать"}
            </button>
          )}
          <button
            className="btn btn--primary btn--small"
            onClick={() => setShowAddModal(true)}
          >
            + Добавить
          </button>
          <button
            className="btn btn--small"
            onClick={loadTree}
          >
            🔄
          </button>
        </div>
      </div>

      {treeInfo && (
        <div className="tree-info">
          <span>Сцен: {treeInfo.scenes_count || 1}</span>
          <span>Глубина: {treeInfo.max_depth || 0}</span>
        </div>
      )}

      {isEmpty ? (
        <div className="tree-empty-state">
          <span className="empty-icon">🌳</span>
          <p>Дерево диалога пусто</p>
          <p className="empty-hint">Нажмите "Создать" для добавления примеров</p>
        </div>
      ) : (
        <div className="tree-body">
          <TreeNode
            node={treeData}
            onSelect={onSelectScene}
            selected={selectedScene}
          />
        </div>
      )}

      {/* Кнопка настроек внизу */}
      <div className="tree-footer">
        <button
          className={`btn settings-toggle-btn ${isSettingsOpen ? "active" : ""}`}
          onClick={() => onSettingsToggle && onSettingsToggle(!isSettingsOpen)}
        >
          <span className="settings-icon">⚙️</span>
          {isSettingsOpen ? "Скрыть настройки" : "Настройки контекста"}
          <span className="settings-arrow">{isSettingsOpen ? "▲" : "▼"}</span>
        </button>
      </div>

      {/* Модальное окно для добавления сцены */}
      {showAddModal && (
        <div className="modal-overlay" onClick={() => setShowAddModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3>➕ Добавить новую сцену</h3>

            <div className="form-group">
              <label>Название сцены</label>
              <input
                type="text"
                value={newSceneName}
                onChange={(e) => setNewSceneName(e.target.value)}
                placeholder="Введите название сцены"
                autoFocus
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    handleAddScene();
                  }
                }}
              />
            </div>

            <div className="form-group">
              <label>Родительская сцена</label>
              <select
                value={newSceneParent}
                onChange={(e) => setNewSceneParent(e.target.value)}
              >
                <option value="root">Корень</option>
                {treeData && treeData.children && treeData.children.map(child => (
                  <option key={child.name} value={child.name}>
                    {child.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="modal-actions">
              <button
                className="btn"
                onClick={() => setShowAddModal(false)}
                disabled={addLoading}
              >
                Отмена
              </button>
              <button
                className="btn btn--primary"
                onClick={handleAddScene}
                disabled={addLoading || !newSceneName.trim()}
              >
                {addLoading ? "⏳ Создание..." : "✅ Создать"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}