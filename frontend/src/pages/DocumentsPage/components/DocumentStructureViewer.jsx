// components/DocumentStructureViewer.jsx
import { useState } from "react";
import { documentsApi } from "../../../api/documents";

export default function DocumentStructureViewer({ docId, parsedDocument, onUpdate }) {
  const [updating, setUpdating] = useState(null);

  const handleToggle = async (elementId, currentInclude) => {
    const newInclude = !currentInclude;
    setUpdating(elementId);
    try {
      await documentsApi.updateElementFlag(docId, elementId, newInclude);
      // Обновляем локальное состояние через callback
      onUpdate(elementId, newInclude);
    } catch (error) {
      console.error("Ошибка обновления флага:", error);
    } finally {
      setUpdating(null);
    }
  };

  const renderNode = (node, level = 0) => {
    const { id, type, title, text, _include, _process } = node;
    const isSection = type === "SECTION";
    const isParagraph = type === "PARAGRAPH";
    const isBreak = type === "BREAK";
    const isTable = type === "TABLE";

    // Определяем, можно ли изменять флаг (не таблицы и не пустые строки)
    let canToggle = false;
    if (isSection) {
      canToggle = true;
    } else if (isParagraph) {
      // Если текст не пустой и не только пробелы
      const content = text || "";
      if (content.trim().length > 0) {
        canToggle = true;
      }
    }
    // Для BREAK и TABLE – не показываем чекбокс

    // Проверяем, исключён ли элемент (для отображения стиля)
    const isExcluded = (_include === false);

    return (
      <div
        key={id}
        className="structure-node"
        style={{ paddingLeft: `${level * 20}px`, opacity: isExcluded ? 0.5 : 1 }}
      >
        <div className="node-row">
          {/* Чекбокс, если разрешено */}
          {canToggle && (
            <label className="toggle-label">
              <input
                type="checkbox"
                checked={!isExcluded}
                onChange={() => handleToggle(id, !isExcluded)}
                disabled={updating === id}
              />
              {updating === id ? "..." : ""}
            </label>
          )}

          {/* Отображение содержимого */}
          <div className="node-content">
            {isSection && (
              <div className="section-title" style={{ fontWeight: "bold" }}>
                {title || "Раздел"}
                <span className="node-id"> [{id}]</span>
              </div>
            )}
            {isParagraph && (
              <div className="paragraph-text">
                {text || ""}
                <span className="node-id"> [{id}]</span>
              </div>
            )}
            {isBreak && <div className="break-line">⸻ (пустая строка)</div>}
            {isTable && <div className="table-placeholder">📊 Таблица (автоматически исключена)</div>}
          </div>

          {/* Кнопка для быстрого исключения раздела (можно добавить позже) */}
        </div>

        {/* Рекурсивный рендеринг дочерних разделов */}
        {isSection && node.sections && node.sections.length > 0 && (
          <div className="child-sections">
            {node.sections.map((child) => renderNode(child, level + 1))}
          </div>
        )}

        {/* Рендеринг параграфов (они уже показаны выше, но если они вложены в секцию, то их нужно отобразить после секций?)
            В структуре JSON параграфы лежат в массиве "paragraphs" секции, поэтому они уже обработаны выше как отдельные элементы.
            Но при рендеринге секции мы не отображаем её параграфы отдельно, потому что они уже есть в массиве sections?
            Нет, структура: у секции есть массив sections (вложенные секции) и массив paragraphs (параграфы, принадлежащие этой секции).
            Поэтому нужно отобразить и параграфы этой секции.
        */}
        {isSection && node.paragraphs && node.paragraphs.length > 0 && (
          <div className="section-paragraphs">
            {node.paragraphs.map((para) => renderNode(para, level + 1))}
          </div>
        )}
      </div>
    );
  };

  // Если нет данных, показываем сообщение
  if (!parsedDocument) {
    return <div className="empty-state">Документ ещё не обработан или отсутствует.</div>;
  }

  // Корневой элемент – сам документ (type: "DOCUMENT")
  // Обходим его секции (первый уровень)
  return (
    <div className="document-structure">
      <div className="structure-header">
        <h3>Структура документа</h3>
        <p className="hint">Отметьте элементы, которые нужно исключить из дальнейшей обработки.</p>
      </div>
      <div className="structure-body">
        {parsedDocument.sections && parsedDocument.sections.map((section) => renderNode(section, 0))}
      </div>
    </div>
  );
}