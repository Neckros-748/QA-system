export default function DocumentStatusBadge({ status }) {
  const cls =
    status === "Обработан"
      ? "status status--done"
      : status === "В очереди"
      ? "status status--queue"
      : "status status--work";

  return <span className={cls}>{status}</span>;
}