
const API_BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

async function request(url, options = {}) {
  const response = await fetch(`${API_BASE}${url}`, options);
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed: ${response.status}`);
  }
  return response.json();
}


export const documentsApi = {
	list(search = "") {
		const query = search ? `?search=${encodeURIComponent(search)}` : "";
		return request(`/api/documents${query}`);
	},

	upload(file) {
		const formData = new FormData();
		formData.append("file", file);

		return request("/api/documents", {
			method: "POST",
			body: formData,
		});
	},

	process(id) {
		return request(`/api/documents/${id}/process`, {
			method: "POST",
		});
	},

	remove(id) {
		return request(`/api/documents/${id}`, {
			method: "DELETE",
		});
	},

	dictionary() {
		return request("/api/dictionary");
	},

	graph() {
		return request("/api/knowledge-graph");
	},

	storages() {
		return request("/api/storages");
	},



// Получить текущий обрабатываемый документ (из application.annotator.handler.doc)
  getContent() {
    return request("/api/documents/content");
  },

  // Обновить флаг _include для элемента
  updateFlags(targetId, include) {
    const params = new URLSearchParams({ target_id: targetId, include });
    return request(`/api/documents/content/update-flags?${params}`, {
      method: "POST",
    });
  },




};

