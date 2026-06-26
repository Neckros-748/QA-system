import DocumentSearch from "./DocumentSearch";
import UploadDocumentButton from "./UploadDocumentButton";

export default function DocumentsToolbar({ search, onSearchChange, onUpload, uploading }) {
  return (
    <div className="documents-toolbar">
      <DocumentSearch value={search} onChange={onSearchChange} />
      <UploadDocumentButton onUpload={onUpload} uploading={uploading} />
    </div>
  );
}