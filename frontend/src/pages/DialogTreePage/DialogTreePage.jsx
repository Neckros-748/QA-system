// src/pages/DialogTreePage/DialogTreePage.jsx
import React, { useState } from "react";
import DialogTreeView from "./components/DialogTreeView";
import SceneEditor from "./components/SceneEditor";
import DialogSettings from "./components/DialogSettings";
import "./DialogTreePage.css";

export default function DialogTreePage() {
  const [selectedScene, setSelectedScene] = useState(null);
  const [updateKey, setUpdateKey] = useState(0);
  const [dialogSettings, setDialogSettings] = useState(null);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  const handleSelectScene = (sceneName) => {
    setSelectedScene(sceneName);
  };

  const handleSaveScene = (updatedScene) => {
    console.log("Сцена сохранена:", updatedScene);
  };

  const handleDeleteScene = (deletedScene) => {
    if (selectedScene === deletedScene) {
      setSelectedScene(null);
    }
    console.log("Сцена удалена:", deletedScene);
  };

  const handleTreeUpdate = () => {
    setUpdateKey(prev => prev + 1);
  };

  const handleSettingsChange = (settings) => {
    setDialogSettings(settings);
    console.log("Настройки обновлены:", settings);
  };

  const handleSettingsToggle = (isOpen) => {
    setIsSettingsOpen(isOpen);
  };

  return (
    <section className="dialog-tree-page">
      <div className="dialog-tree-container">
        <div className="tree-panel">
          <DialogTreeView
            key={updateKey}
            onSelectScene={handleSelectScene}
            selectedScene={selectedScene}
            onTreeUpdate={handleTreeUpdate}
            onSettingsToggle={handleSettingsToggle}
            isSettingsOpen={isSettingsOpen}
          />
        </div>
        <div className="editor-panel">
          {/* Настройки диалога */}
          <DialogSettings
            onSettingsChange={handleSettingsChange}
            isOpen={isSettingsOpen}
            onToggle={handleSettingsToggle}
          />

          {/* Редактор сцены - показываем только когда настройки закрыты */}
          {!isSettingsOpen && (
            <SceneEditor
              sceneName={selectedScene}
              onSave={handleSaveScene}
              onDelete={handleDeleteScene}
            />
          )}

          {/* Сообщение, когда настройки открыты */}
          {isSettingsOpen && (
            <div className="settings-overlay">
              <span className="settings-overlay-icon">⚙️</span>
              <p>Настройки контекста открыты</p>
              <p className="settings-overlay-hint">
                Закройте настройки для редактирования сцены
              </p>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}