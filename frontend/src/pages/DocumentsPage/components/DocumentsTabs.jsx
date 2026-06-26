export default function DocumentsTabs({ tabs, activeTab, onChange }) {
  return (
    <div className="tabs">
      {tabs.map((tab) => (
        <button
          key={tab.key}
          type="button"
          className={`tabs__item ${activeTab === tab.key ? "tabs__item--active" : ""}`}
          onClick={() => onChange(tab.key)}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}