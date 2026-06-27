import { useEffect, useMemo, useState } from "react";
import { documentsApi } from "../../api/documents";
import DocumentsTabs from "./components/DocumentsTabs";
import DocumentsToolbar from "./components/DocumentsToolbar";
import DocumentsList from "./components/DocumentsList";
import DocumentDetails from "./components/DocumentDetails";
import DocumentProcessingTab from "./components/DocumentProcessingTab";
import DocumentProcessingViewer from './components/DocumentProcessingViewer';
import KnowledgeGraphViewer from './components/KnowledgeGraphViewer';
import EmptyState from "./components/EmptyState";
import "./DocumentsPage.css";

const BASE_TABS = [
  { key: "documents", label: "Список документов" },
  //   { key: "dictionary", label: "Справочник" },
  { key: "graph", label: "Граф знаний" },
];

export default function DocumentsPage() {
  const [activeTab, setActiveTab] = useState("documents");
  const [documents, setDocuments] = useState([]);
  const [dictionary, setDictionary] = useState([]);
  const [graph, setGraph] = useState({ nodes: [], edges: [] });

  const [search, setSearch] = useState("");
  const [selectedId, setSelectedId] = useState(null);

  const [loading, setLoading] = useState(true);
  const [loadingActionId, setLoadingActionId] = useState(null);
  const [uploading, setUploading] = useState(false);

  const selectedDocument = useMemo(
    () => documents.find((doc) => doc.id === selectedId) ?? null,
    [documents, selectedId]
  );

  const showProcessingTab = Boolean(
    selectedDocument && selectedDocument.status !== "Обработан"
  );

  const tabs = showProcessingTab
    ? [...BASE_TABS, { key: "processing", label: "Обработка" }]
    : BASE_TABS;

  async function loadDocuments(searchValue = "") {
    const data = await documentsApi.list(searchValue);
    setDocuments(data.documents ?? []);
    if (!selectedId && data.documents?.length) {
      setSelectedId(data.documents[0].id);
    }
  }

  async function loadDictionary() {
    const data = await documentsApi.dictionary();
    setDictionary(data.items ?? []);
  }

  async function loadGraph() {
    const data = await documentsApi.graph();
    setGraph({
      nodes: data.nodes ?? [],
      edges: data.edges ?? [],
    });
  }

  useEffect(() => {
    let alive = true;

    (async () => {
      try {
        setLoading(true);

        if (activeTab === "documents" || activeTab === "processing") {
          await loadDocuments(search);
        }

        if (activeTab === "dictionary") {
          await loadDictionary();
        }

        if (activeTab === "graph") {
          await loadGraph();
        }
      } finally {
        if (alive) setLoading(false);
      }
    })();

    return () => {
      alive = false;
    };
  }, [activeTab, search]);

  async function refreshDocuments(nextSearch = search) {
    const data = await documentsApi.list(nextSearch);
    setDocuments(data.documents ?? []);

    if (data.documents?.length) {
      const stillSelected = data.documents.some((d) => d.id === selectedId);
      if (!stillSelected) setSelectedId(data.documents[0].id);
    } else {
      setSelectedId(null);
    }
  }

  async function handleUpload(file) {
    try {
      setUploading(true);
      await documentsApi.upload(file);
      await refreshDocuments();
      setActiveTab("documents");
    } finally {
      setUploading(false);
    }
  }

  async function handleOpenProcessing(document) {
    setSelectedId(document.id);
    setActiveTab("processing");
  }

/*   async function handleListProcess(document) {
    setSelectedId(document.id);

    if (document.status === "Ожидание") {
      try {
        setLoadingActionId(document.id);
        await documentsApi.process(document.id);
        await refreshDocuments();
      } finally {
        setLoadingActionId(null);
      }
    }

    setActiveTab("processing");
  } */

async function handleListProcess(document) {
    setSelectedId(document.id);
    // Переводим документ в режим редактирования (статус EDIT)
    try {
        setLoadingActionId(document.id);
        await documentsApi.process(document.id);
        await refreshDocuments();
        // Открываем вкладку обработки (редактор)
        setActiveTab("processing");
    } finally {
        setLoadingActionId(null);
    }
}

//   async function handleProcessingStep() {
//     if (!selectedDocument) return;
//
//     try {
//       setLoadingActionId(selectedDocument.id);
//       await documentsApi.process(selectedDocument.id);
//       await refreshDocuments();
//
//       const updated = (await documentsApi.list(search)).documents?.find(
//         (d) => d.id === selectedDocument.id
//       );
//
//       if (updated?.status === "Обработан") {
//         setActiveTab("documents");
//       }
//     } finally {
//       setLoadingActionId(null);
//     }
//   }
//   const handleProcessingStep = async () => {
//     if (!selectedDocument) return;
//     try {
//       setLoadingActionId(selectedDocument.id);
//       await documentsApi.process(selectedDocument.id);
//       await refreshDocuments();
//
//       const updated = documents.find((d) => d.id === selectedDocument.id);
//       if (updated?.status === STATUS_DONE) {
//         setActiveTab("documents");
//       }
//     } catch (err) {
//       console.error("Ошибка обработки:", err);
//     } finally {
//       setLoadingActionId(null);
//     }
//   };


async function handleProcessingStep() {
    if (!selectedDocument) return;
    try {
        setLoadingActionId(selectedDocument.id);
        // Запускаем обработку (переход EDIT -> PROCESS -> DONE)
        await documentsApi.process(selectedDocument.id);
        await refreshDocuments();
        // После завершения обработки переходим на список документов
        setActiveTab("documents");
    } catch (err) {
        console.error("Ошибка обработки:", err);
        alert("Не удалось обработать документ");
    } finally {
        setLoadingActionId(null);
    }
}


  async function handleDelete(id) {
    try {
      setLoadingActionId(id);
      await documentsApi.remove(id);
      await refreshDocuments();

      if (selectedId === id) {
        setActiveTab("documents");
      }
    } finally {
      setLoadingActionId(null);
    }
  }







  return (
    <section className="documents-page">
      <div className="documents-page__top">
        <DocumentsTabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />

        {activeTab === "documents" && (
          <DocumentsToolbar
            search={search}
            onSearchChange={setSearch}
            onUpload={handleUpload}
            uploading={uploading}
          />
        )}
      </div>

      {activeTab === "documents" && (
        <div className="documents-layout">
          <DocumentsList
            documents={documents}
            selectedId={selectedId}
            onSelect={setSelectedId}
            onProcess={handleListProcess}
            onDelete={handleDelete}
            loadingActionId={loadingActionId}
            search={search}
          />

          <DocumentDetails
            document={selectedDocument}
            onOpenProcessing={handleOpenProcessing}
          />
        </div>
      )}

{/*       {activeTab === "processing" && ( */}
{/*         <DocumentProcessingTab */}
{/*           document={selectedDocument} */}
{/*           loading={loading} */}
{/*           loadingActionId={loadingActionId} */}
{/*           onProcessStep={handleProcessingStep} */}
{/*           onBackToDocuments={() => setActiveTab("documents")} */}
{/*         /> */}
{/*       )} */}

	{activeTab === "processing" && (
	  <DocumentProcessingTab
	    onProcessStep={handleProcessingStep}
	    onBackToDocuments={() => setActiveTab("documents")}
	    loadingActionId={loadingActionId}
	  />
	)}

      {activeTab === "dictionary" && (
        <div className="placeholder-block">
          {loading ? "Загрузка..." : "Справочник пока пуст."}
          {dictionary.length > 0 && <pre>{JSON.stringify(dictionary, null, 2)}</pre>}
        </div>
      )}

{/*       {activeTab === "graph" && (
        <div className="placeholder-block">
          {loading ? "Загрузка..." : "Граф знаний пока пуст."}
          {graph.nodes.length > 0 && <pre>{JSON.stringify(graph, null, 2)}</pre>}
        </div>
      )} */}
	  {activeTab === "graph" && (
	  <div className="graph-tab">
	    <KnowledgeGraphViewer />
	  </div>
	)}
    </section>
  );
}