import DocumentRow from "./DocumentRow";
import EmptyState from "./EmptyState";

export default function DocumentsList({
  documents,
  selectedId,
  onSelect,
  onProcess,
  onDelete,
  loadingActionId,
  search,
}) {
  const draftDocument = documents.find((doc) => doc.status !== "Обработан");
  const processedDocuments = documents.filter((doc) => doc.status === "Обработан");

  return (
    <section className="panel documents-panel">
      <h2 className="section-title">Список документов</h2>

      {draftDocument && (
        <div className="draft-block">
          <div className="draft-block__label">Необработанный документ</div>
          <DocumentRow
            document={draftDocument}
            selected={draftDocument.id === selectedId}
            onSelect={onSelect}
            onProcess={onProcess}
            onDelete={onDelete}
            loadingActionId={loadingActionId}
            draft
          />
        </div>
      )}

      <div className="table-head">
        <span>Имя</span>
        <span>Тип</span>
        <span>Размер</span>
        <span>Дата</span>
        <span>Статус</span>
        <span>Действия</span>
      </div>

      {processedDocuments.length === 0 && !draftDocument ? (
        <EmptyState text={search ? "Ничего не найдено." : "Документов пока нет."} />
      ) : (
        <div className="table-body">
          {processedDocuments.map((doc) => (
            <DocumentRow
              key={doc.id}
              document={doc}
              selected={doc.id === selectedId}
              onSelect={onSelect}
              onProcess={onProcess}
              onDelete={onDelete}
              loadingActionId={loadingActionId}
            />
          ))}
        </div>
      )}
    </section>
  );
}