import React, { useState, useMemo, useCallback, useEffect, useRef } from 'react';
import './DocumentProcessingViewer.css';

// Вспомогательная функция для построения плоского списка элементов
function flattenDocument(doc, parentId = null, level = 0) {
  const elements = [];
  const stack = doc.stack?.content_stack || [];

  // Рекурсивный обход разделов и параграфов
  function traverse(node, currentLevel) {
    // Если узел - раздел
    if (node.type === 'SECTION') {
      const sectionItem = {
        id: node.id,
        type: 'section',
        title: node.title || '(без названия)',
        level: currentLevel,
        parentId: parentId,
        _include: node._include !== false, // по умолчанию true
        _process: node._process || false,
        children: [],
      };
      elements.push(sectionItem);

      // Обрабатываем содержимое в порядке content_stack
      const contentStack = node.stack?.content_stack || [];
      for (const childId of contentStack) {
        // Ищем дочерний элемент по id среди paragraphs, sections, tables
        let child = null;
        if (node.paragraphs) {
          child = node.paragraphs.find(p => p.id === childId);
        }
        if (!child && node.sections) {
          child = node.sections.find(s => s.id === childId);
        }
        if (!child && node.stack?.tables) {
          child = node.stack.tables.find(t => t.id === childId);
        }
        if (child) {
          const childElements = flattenDocumentItem(child, node.id, currentLevel + 1);
          elements.push(...childElements);
        }
      }
    }
    // Если узел - параграф
    else if (node.type === 'PARAGRAPH') {
      const isBreak = node.type === 'BREAK';
      const item = {
        id: node.id,
        type: isBreak ? 'break' : 'paragraph',
        text: node.text || '',
        level: currentLevel,
        parentId: parentId,
        _include: node._include !== false,
        _process: node._process || false,
        style: node.style || {},
        lines: node.stack?.lines || [],
        isBreak,
      };
      elements.push(item);
    }
    // Если узел - таблица
    else if (node.type === 'TABLE') {
      const item = {
        id: node.id,
        type: 'table',
        title: node.title || '',
        level: currentLevel,
        parentId: parentId,
        _include: node._include !== false,
        _process: node._process || false,
        content: node.content || {},
        isTable: true,
      };
      elements.push(item);
    }
  }

  // Начинаем с корневого документа
  traverse(doc, level);
  return elements;
}

function flattenDocumentItem(node, parentId, level) {
  const items = [];
  if (node.type === 'SECTION') {
    // Рекурсивно обрабатываем раздел
    const sectionItem = {
      id: node.id,
      type: 'section',
      title: node.title || '(без названия)',
      level: level,
      parentId: parentId,
      _include: node._include !== false,
      _process: node._process || false,
    };
    items.push(sectionItem);
    // Обрабатываем детей
    const contentStack = node.stack?.content_stack || [];
    for (const childId of contentStack) {
      let child = null;
      if (node.paragraphs) {
        child = node.paragraphs.find(p => p.id === childId);
      }
      if (!child && node.sections) {
        child = node.sections.find(s => s.id === childId);
      }
      if (!child && node.stack?.tables) {
        child = node.stack.tables.find(t => t.id === childId);
      }
      if (child) {
        const childItems = flattenDocumentItem(child, node.id, level + 1);
        items.push(...childItems);
      }
    }
  } else if (node.type === 'PARAGRAPH' || node.type === 'BREAK') {
    const isBreak = node.type === 'BREAK';
    items.push({
      id: node.id,
      type: isBreak ? 'break' : 'paragraph',
      text: node.text || '',
      level: level,
      parentId: parentId,
      _include: node._include !== false,
      _process: node._process || false,
      style: node.style || {},
      lines: node.stack?.lines || [],
      isBreak,
    });
  } else if (node.type === 'TABLE') {
    items.push({
      id: node.id,
      type: 'table',
      title: node.title || '',
      level: level,
      parentId: parentId,
      _include: node._include !== false,
      _process: node._process || false,
      content: node.content || {},
      isTable: true,
    });
  }
  return items;
}

// Основной компонент
export default function DocumentProcessingViewer({
  parsedDocument,
  onToggleFlag,
  onProcessNext,
  loading,
}) {
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedSections, setExpandedSections] = useState(new Set());
  const [selectedElementId, setSelectedElementId] = useState(null);
  const contentRef = useRef(null);

  // Построение плоского списка элементов с учетом исключенных (для отображения)
  const flatElements = useMemo(() => {
    if (!parsedDocument) return [];
    return flattenDocument(parsedDocument);
  }, [parsedDocument]);

  // Оглавление (только разделы и подразделы)
  const tableOfContents = useMemo(() => {
    return flatElements.filter(el => el.type === 'section');
  }, [flatElements]);

  // Поиск
  const searchResults = useMemo(() => {
    if (!searchQuery.trim() || searchQuery.length < 2) return [];
    const q = searchQuery.toLowerCase();
    return flatElements.filter(el => {
      if (el.type === 'paragraph') {
        const text = el.text?.toLowerCase() || '';
        return text.includes(q) || (el.lines && el.lines.some(line => line.text.toLowerCase().includes(q)));
      }
      if (el.type === 'section') {
        return el.title.toLowerCase().includes(q);
      }
      return false;
    });
  }, [flatElements, searchQuery]);

  // Функция для рендеринга текста параграфа с учётом стилей
  const renderParagraph = (element) => {
    if (element.isBreak) {
      return <hr className="document-break" />;
    }
    const lines = element.lines && element.lines.length > 0 ? element.lines : [{ text: element.text, style: {} }];
    return lines.map((line, idx) => {
      const classes = [];
      if (line.style?.bold) classes.push('bold');
      if (line.style?.italic) classes.push('italic');
      if (line.style?.underline) classes.push('underline');
      return (
        <span key={idx} className={classes.join(' ')}>
          {line.text}
        </span>
      );
    });
  };

  // Рендер таблицы
  const renderTable = (element) => {
    const content = element.content;
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
                    {cell.text.join(' ')}
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
                  {cell.text.join(' ')}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    );
  };

  // Переключение чекбокса
  const handleToggle = (element) => {
    // Нельзя исключать таблицы и BREAK
    if (element.isBreak || element.type === 'table') return;
    const newInclude = !element._include;
    onToggleFlag(element.id, newInclude);
  };

  // Прокрутка к элементу
  const scrollToElement = (id) => {
    const el = document.getElementById(`doc-elem-${id}`);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'center' });
      setSelectedElementId(id);
    }
  };

  // Поиск с подсветкой
  const highlightText = (text, query) => {
    if (!query || query.length < 2) return text;
    const parts = text.split(new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi'));
    return parts.map((part, i) =>
      part.toLowerCase() === query.toLowerCase() ? <mark key={i}>{part}</mark> : part
    );
  };

  // Эффект для подсветки результата поиска
  useEffect(() => {
    if (searchResults.length > 0 && contentRef.current) {
      const first = searchResults[0];
      scrollToElement(first.id);
    }
  }, [searchResults]);

  if (!parsedDocument) {
    return <div className="processing-empty">Документ не загружен для обработки</div>;
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
              <span className="search-results-count">
                {searchResults.length} совпадений
              </span>
            )}
          </div>
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
            // Пропускаем элементы, которые не должны отображаться (если _include === false, но мы всё равно показываем с зачёркиванием)
            const isExcluded = !el._include;
            const isSelectable = !el.isBreak && el.type !== 'table';
            const id = el.id;

            return (
              <div
                id={`doc-elem-${id}`}
                key={id}
                className={`document-element ${isExcluded ? 'excluded' : ''} ${selectedElementId === id ? 'selected' : ''}`}
                style={{ marginLeft: `${el.level * 20}px` }}
              >
                {isSelectable && (
                  <label className="exclude-checkbox">
                    <input
                      type="checkbox"
                      checked={isExcluded}
                      onChange={() => handleToggle(el)}
                    />
                    <span className="checkbox-label">Исключить</span>
                  </label>
                )}

                {el.type === 'section' && (
                  <div className="section-heading level-{el.level}">
                    <strong>{el.title}</strong>
                  </div>
                )}

                {el.type === 'paragraph' && (
                  <div className="paragraph-text" style={{ textAlign: el.style?.alignment || 'justify' }}>
                    {renderParagraph(el)}
                  </div>
                )}

                {el.type === 'table' && (
                  <div className="table-wrapper">
                    {renderTable(el)}
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
          className="btn btn-primary btn-next"
          onClick={onProcessNext}
          disabled={loading}
        >
          {loading ? 'Обработка...' : 'Следующий шаг →'}
        </button>
      </div>
    </div>
  );
}