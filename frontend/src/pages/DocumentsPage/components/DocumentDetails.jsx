import DocumentStatusBadge from "./DocumentStatusBadge";
import EmptyState from "./EmptyState";

export default function DocumentDetails({ document, onOpenProcessing }) {
  if (!document) {
    return (
      <aside className="details-panel panel">
        <h2 className="section-title">Информация о документе</h2>
        <EmptyState text="Выберите документ из списка" />
      </aside>
    );
  }

  const isProcessed = document.status === "Обработан";

  return (
    <aside className="details-panel panel">
      <div className="details-header">
        <h2>Информация о документе</h2>
        <DocumentStatusBadge status={document.status} />
      </div>

      <div className="details-content">
        <section className="details-section">
          <h3>Основная информация</h3>
          <div className="property-list">
            <Property name="Имя" value={document.name} />
            <Property name="Тип" value={document.type} />
            <Property name="Размер" value={document.size} />
            <Property name="Дата" value={document.created_at} />
          </div>
        </section>

        <section className="details-section">
          <h3>Технические данные</h3>
          <div className="property-list">
            <Property name="ID" value={document.id} />
            <Property name="Статус" value={document.status} />
          </div>
        </section>

        <section className="details-section">
          <h3>Действия</h3>
          <div className="details-actions">
            <button
              type="button"
              className="btn btn--primary"
              disabled={isProcessed}
              onClick={() => onOpenProcessing(document)}
            >
              {isProcessed ? "Документ обработан" : "Открыть обработку"}
            </button>
          </div>
        </section>
      </div>
    </aside>
  );
}

function Property({ name, value }) {
  return (
    <div className="property-row">
      <span>{name}</span>
      <strong>{value ?? "-"}</strong>
    </div>
  );
}