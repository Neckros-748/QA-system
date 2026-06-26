export default function DocumentSearch({ value, onChange }) {
  return (
    <input
      className="search-input"
      type="text"
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder="Поиск по имени, типу, размеру, дате, статусу..."
    />
  );
}