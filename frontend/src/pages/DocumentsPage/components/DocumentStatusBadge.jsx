export default function DocumentStatusBadge({ status }) {
  const cls =
    status === "Обработан"
      ? "status status--done"
      : status === "Ожидание"
      ? "status status--queue"
      : "status status--work";

  return <span className={cls}>{status}</span>;
}