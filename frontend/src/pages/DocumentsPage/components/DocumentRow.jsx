import DocumentStatusBadge from "./DocumentStatusBadge";

export default function DocumentRow({
  document,
  selected,
  onSelect,
  onProcess,
  onDelete,
  loadingActionId,
  draft = false,
}) {
  const busy = loadingActionId === document.id;

  return (
    <div
      className={`doc-row ${selected ? "doc-row--selected" : ""} ${draft ? "doc-row--draft" : ""}`}
      onClick={() => onSelect(document.id)}
      role="button"
      tabIndex={0}
    >
      <span>{document.name}</span>
      <span>{document.type}</span>
      <span>{document.size}</span>
      <span>{document.created_at}</span>
      <span>
        <DocumentStatusBadge status={document.status} />
      </span>

      <span className="doc-row__actions">
  {document.status !== "Обработан" && (<>
    <button
      type="button"
      className="btn btn--primary"
      onClick={(e) => {
        e.stopPropagation();
        onProcess(document);
      }}
      disabled={busy}
    >
      {busy ? "⟳" : "Обработка"}
    </button>
	  <button
	    type="button"
	    className="btn btn--danger"
	    onClick={(e) => {
	      e.stopPropagation();
	      onDelete(document.id);
	    }}
	    disabled={busy}
	  >
	    Удалить
	  </button>
	  </>
  )}

</span>
    </div>
  );
}