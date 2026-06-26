export default function DocumentStages({ stages, currentStage }) {
  const currentIndex = stages.indexOf(currentStage);

  return (
    <div className="stages">
      {stages.map((stage, index) => (
        <button
          key={stage}
          type="button"
          className={`stages__item ${
            index === currentIndex ? "stages__item--active" : ""
          }`}
        >
          {stage}
        </button>
      ))}
    </div>
  );
}