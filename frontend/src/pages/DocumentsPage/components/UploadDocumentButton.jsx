import { useRef } from "react";

export default function UploadDocumentButton({ onUpload, uploading }) {
  const inputRef = useRef(null);

  const handleClick = () => inputRef.current?.click();

  const handleChange = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    await onUpload(file);
    e.target.value = "";
  };

  return (
    <>
      <button className="btn btn--primary" type="button" onClick={handleClick}>
        {uploading ? "Загрузка..." : "Загрузить документ"}
      </button>
      <input ref={inputRef} type="file" hidden onChange={handleChange} />
    </>
  );
}