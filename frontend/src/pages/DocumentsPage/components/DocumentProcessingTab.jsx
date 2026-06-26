import React, { useState, useEffect, useMemo, useCallback, useRef } from "react";
import { documentsApi } from "../../../api/documents";
import "./DocumentProcessingTab.css";

// ---- Вспомогательные функции ----

function flattenDocument(doc, parentId = null, level = 0) {
  const elements = [];

  function processNode(node, currentLevel, parentId) {
    if (!node) return;

    // Корневой документ
    if (node.type === "DOCUMENT: DOCX" || node.type === "DOCUMENT") {
      if (node.sections) {
        for (const section of node.sections) {
          processNode(section, currentLevel, node.id);
        }
      }
      return;
    }

    // SECTION
    if (node.type === "SECTION") {
      const sectionItem = {
        id: node.id,
        type: "section",
        title: node.title || "(без названия)",
        level: currentLevel,
        parentId: parentId,
        _include: node._include !== false,
        _process: node._process || false,
      };
      elements.push(sectionItem);

      const contentStack = node.stack?.content_stack || [];
      for (const childId of contentStack) {
        let child = null;
        if (node.paragraphs) {
          child = node.paragraphs.find((p) => p.id === childId);
        }
        if (!child && node.sections) {
          child = node.sections.find((s) => s.id === childId);
        }
        if (!child && node.stack?.tables) {
          child = node.stack.tables.find((t) => t.id === childId);
        }
        if (child) {
          processNode(child, currentLevel + 1, node.id);
        }
      }
      return;
    }

    // PARAGRAPH или BREAK
    if (node.type === "PARAGRAPH" || node.type === "BREAK") {
      const isBreak = node.type === "BREAK";
      elements.push({
        id: node.id,
        type: isBreak ? "break" : "paragraph",
        text: node.text || "",
        level: currentLevel,
        parentId: parentId,
        _include: node._include !== false,
        _process: node._process || false,
        style: node.style || {},
        lines: node.stack?.lines || [],
        isBreak,
      });
      return;
    }

    // TABLE
    if (node.type === "TABLE") {
      elements.push({
        id: node.id,
        type: "table",
        title: node.title || "",
        level: currentLevel,
        parentId: parentId,
        _include: node._include !== false,
        _process: node._process || false,
        content: node.content || {},
        isTable: true,
      });
      return;
    }
  }

  processNode(doc, level, parentId);
  return elements;
}

function renderParagraphLines(lines, text) {
  const lineData = lines && lines.length > 0 ? lines : [{ text: text || "", style: {} }];
  return lineData.map((line, idx) => {
    const classes = [];
    if (line.style?.bold) classes.push("bold");
    if (line.style?.italic) classes.push("italic");
    if (line.style?.underline) classes.push("underline");
    return (
      <span key={idx} className={classes.join(" ")}>
        {line.text}
      </span>
    );
  });
}

function renderTableElement(content) {
  if (!content || !content.rows) return null;
  const headers = content.headers || [];
  const rows = content.rows || [];
  return (
    <table className="document-table">
      {headers.length > 0 && (
        <thead>
          {headers.map((row, ri) => (
            <tr key={ri}>
              {row.map((cell, ci) => (
                <th key={ci} colSpan={cell.colspan || 1} rowSpan={cell.rowspan || 1}>
                  {cell.text.join(" ")}
                </th>
              ))}
            </tr>
          ))}
        </thead>
      )}
      <tbody>
        {rows.map((row, ri) => (
          <tr key={ri}>
            {row.map((cell, ci) => (
              <td key={ci} colSpan={cell.colspan || 1} rowSpan={cell.rowspan || 1}>
                {cell.text.join(" ")}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

// ---- Основной компонент ----

export default function DocumentProcessingTab({
  onProcessStep,
  onBackToDocuments,
  loadingActionId,
}) {
  const [doc, setDoc] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedElementId, setSelectedElementId] = useState(null);
  const [updating, setUpdating] = useState(false);
  const contentRef = useRef(null);

  // Загрузка документа
  useEffect(() => {
    let mounted = true;
    const loadDoc = async () => {
      try {
        setLoading(true);
        const data = await documentsApi.getContent();
        if (mounted) {
          if (data && data.content) {
            setDoc(data.content);
          } else {
            setError("Документ не содержит данных");
          }
        }
      } catch (err) {
        console.error("Ошибка загрузки:", err);
        if (mounted) {
          setError(err.message || "Не удалось загрузить документ");
        }
      } finally {
        if (mounted) setLoading(false);
      }
    };
    loadDoc();
    return () => {
      mounted = false;
    };
  }, []);

  // Построение плоского списка и фильтрация корневого раздела sct_h0:1
  const flatElements = useMemo(() => {
    if (!doc) return [];
    try {
      const all = flattenDocument(doc);
      // Исключаем корневой раздел sct_h0:1 и всё, что с ним связано (он всегда должен быть включён)
      return all.filter((el) => el.id !== "sct_h0:1");
    } catch (e) {
      console.error("Ошибка flattenDocument:", e);
      return [];
    }
  }, [doc]);

  // Оглавление
  const tableOfContents = useMemo(() => {
    return flatElements.filter((el) => el.type === "section");
  }, [flatElements]);

  // Поиск
  const searchResults = useMemo(() => {
    if (!searchQuery.trim() || searchQuery.length < 2) return [];
    const q = searchQuery.toLowerCase();
    return flatElements.filter((el) => {
      if (el.type === "paragraph") {
        const text = el.text?.toLowerCase() || "";
        return text.includes(q) || (el.lines && el.lines.some((l) => l.text.toLowerCase().includes(q)));
      }
      if (el.type === "section") {
        return el.title.toLowerCase().includes(q);
      }
      return false;
    });
  }, [flatElements, searchQuery]);

  // Переключение флага (обновление состояния с глубоким копированием)
  const handleToggle = useCallback(
    async (targetId, include) => {
      if (updating) return;
      try {
        setUpdating(true);
        await documentsApi.updateFlags(targetId, include);
        // После успешного обновления перезагружаем документ с сервера
        const data = await documentsApi.getContent();
        setDoc(data.content);
      } catch (err) {
        console.error("Ошибка обновления флага:", err);
        alert("Не удалось обновить флаг");
      } finally {
        setUpdating(false);
      }
    },
    [updating]
  );

  // Прокрутка к элементу
  const scrollToElement = (id) => {
    const el = document.getElementById(`doc-elem-${id}`);
    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "center" });
      setSelectedElementId(id);
    }
  };

  // Состояния загрузки/ошибки
  if (loading) {
    return <div className="processing-tab-loading">Загрузка документа...</div>;
  }

  if (error) {
    return (
      <div className="processing-tab-error">
        <p>Ошибка: {error}</p>
        <button className="btn btn--primary" onClick={() => window.location.reload()}>
          Повторить
        </button>
        <button className="btn btn--ghost" onClick={onBackToDocuments}>
          Назад к списку
        </button>
      </div>
    );
  }

  if (!doc) {
    return (
      <div className="processing-tab-empty">
        <p>Нет документа для обработки.</p>
        <button className="btn btn--ghost" onClick={onBackToDocuments}>
          Назад к списку
        </button>
      </div>
    );
  }

  if (flatElements.length === 0) {
    return (
      <div className="processing-tab-empty">
        <p>Документ не содержит элементов для отображения.</p>
        <button className="btn btn--ghost" onClick={onBackToDocuments}>
          Назад к списку
        </button>
      </div>
    );
  }

  return (
    <div className="processing-viewer">
      <div className="processing-header">
        <div className="processing-title">Редактирование документа</div>
        <div className="processing-controls">
          <div className="search-box">
            <input
              type="text"
              placeholder="Поиск по документу..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            {searchQuery && (
              <span className="search-results-count">{searchResults.length} совпадений</span>
            )}
          </div>
          <button className="btn btn--ghost" onClick={onBackToDocuments}>
            Назад к списку
          </button>
        </div>
      </div>

      <div className="processing-body">
        {/* Оглавление */}
        <aside className="toc-panel">
          <div className="toc-title">Оглавление</div>
          <nav className="toc-nav">
            {tableOfContents.map((item) => (
              <div
                key={item.id}
                className={`toc-item level-${item.level}`}
                onClick={() => scrollToElement(item.id)}
                style={{ paddingLeft: `${item.level * 12}px` }}
              >
                {item.title}
              </div>
            ))}
          </nav>
        </aside>

        {/* Основной контент */}
        <main className="document-content" ref={contentRef}>
          {flatElements.map((el) => {
            const isExcluded = !el._include;
            const isSelectable = !el.isBreak && el.type !== "table";
            const id = el.id;

            return (
              <div
                id={`doc-elem-${id}`}
                key={id}
                className={`document-element ${isExcluded ? "excluded" : ""} ${
                  selectedElementId === id ? "selected" : ""
                }`}
                style={{ marginLeft: `${el.level * 20}px` }}
              >
                {isSelectable && (
                  <button
                    className="exclude-icon"
                    onClick={() => handleToggle(el.id, !isExcluded)}
                    disabled={updating}
                    title={isExcluded ? "Включить" : "Исключить"}
                  >
                    {isExcluded ? "✕" : "✓"}
                  </button>
                )}

                {el.type === "section" && (
                  <div className={`section-heading level-${el.level}`}>
                    <strong>{el.title}</strong>
                  </div>
                )}

                {el.type === "paragraph" && (
                  <div className="paragraph-text" style={{ textAlign: el.style?.alignment || "justify" }}>
                    {renderParagraphLines(el.lines, el.text)}
                  </div>
                )}

                {el.type === "table" && (
                  <div className="table-wrapper">
                    {renderTableElement(el.content)}
                    {el.title && <div className="table-caption">{el.title}</div>}
                  </div>
                )}

                {el.isBreak && (
                  <div className="break-element">
                    <hr />
                  </div>
                )}
              </div>
            );
          })}
        </main>
      </div>

      {/* Кнопка перехода к следующему шагу */}
      <div className="next-step-button">
        <button
          className="btn btn--primary btn-next"
          onClick={onProcessStep}
          disabled={loadingActionId !== null || updating}
        >
          {loadingActionId ? "Обработка..." : "Далее →"}
        </button>
      </div>
    </div>
  );
}