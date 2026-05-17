from __future__ import annotations

from typing import Dict, List, Optional

import json
import html as html_mod
from pathlib import Path
import networkx as nx

from backend.src.common.annotation.nlp.utils.word_chunk import LexType, ChunkType, WordChunk
from backend.src.storage.graph.config import BASE_STYLES, NODE_STYLES, LEX_STYLES


class Graph:
	def __init__(self, output_file: str):
		self.graph = nx.DiGraph()
		self.output_file = output_file

	@staticmethod
	def _index_of(
			graph: str, key: str,
			chunk: WordChunk
	) -> str:
		return f"{graph}__n[{key}|({chunk.start}:{chunk.end})]_{chunk.norm}"


	# -------------------------
	# Upsert document (Insert / Update)
	# -------------------------

	def upsert(
			self,
			doc:    dict,
			chunks: Dict[str, List[WordChunk]]
	) -> None:

		# struct_graph = build_struct_graph(doc)
		#
		# self.graph.add_node(
		# 	doc['id'],
		# 	title=doc["title"], type="SUBGRAPH", data=struct_graph
		# )

		# ======================================================================
		# 1) Узлы
		# ======================================================================

		for key, value in chunks.items():
			self._upsert_nodes(
				"root", key, value
			)

		# ======================================================================
		# 2) Ребра
		# ======================================================================

		for key, value in chunks.items():
			self._upsert_edges(
				"root", key, value
			)

		# 	for spans_key, spans_value in spans:
		# 		connects = spans_key, spans_value)
		# 		dict_of_connects.update(connects)
		#
		# 	for spans_key, spans_value in spans.items():
		# 		self.(spans_key, spans_value, dict_of_connects)

	def _upsert_nodes(
			self, graph: str, key: str, chunks: List[WordChunk]
	) -> None:
		for chunk in chunks:
			node_index = self._index_of(graph, key, chunk)

			text = f"({chunk.start}:{chunk.end})[t] - {chunk.text}"
			norm = f"({chunk.start}:{chunk.end})[l] - {chunk.norm}"

			if not self.graph.has_node(node_index):
				self.graph.add_node(
					node_index,
					data = {
						"text": f"{text}",
						"norm": f"{norm}",

						"type":  (chunk.chunk_type, chunk.lex_type),
						"level": chunk.level,
					},
					label = f"{key} = {text}",
					type  = "TERM"
				)
			else:
				pass

		pass

		# 	# for i in range(span.start, span.end):
		# 	# 	dict_of_connects[i] = node_index
		# 	# dict_of_connects[f"({span.start}:{span.end})"] = node_index
		#
		# 	# 	if self.graph.has_node(node_id):
		# 	# 		(id_, data=GraphNode(type_, text_, layer_, intent_, value_))
		# 	# 	elif layer_ not in self.graph.nodes[id_]["data"].layer:
		# 	# 		self.graph.nodes[id_]["data"].layer.append(layer_)

	def _upsert_edges(
			self, graph: str, key: str, chunks: List[WordChunk]
	) -> None:
		for chunk in chunks:
			node_index = self._index_of(graph, key, chunk)

			# text = f"({chunk.start}:{chunk.end})[t] - {chunk.text}"
			# norm = f"({chunk.start}:{chunk.end})[l] - {chunk.norm}"

			# ==================================================================
			# 1) Обработка внешних связей (link)
			# ==================================================================

			if chunk.link is not None:
				link_index = self._index_of(graph, key, chunk.link)

				if not self.graph.has_edge(node_index, link_index):
					self.graph.add_edge(
						node_index,
						link_index,
						data = {

						},
						label = f"link [{chunk.source.tokens[0].dep}]",
					)
				else:
					pass

				pass

			# ==================================================================
			# 2) Обработка иерархических связей (parent / children)
			# ==================================================================

			if chunk.parent is not None:
				parent_index = self._index_of(graph, key, chunk.parent)

				if not self.graph.has_edge(node_index, parent_index):

					self.graph.add_edge(
						node_index,
						parent_index,
						data = {},
						label = f"parent",
					)
				else:
					pass

			# ==================================================================
			# 3) Обработка структурных связей (document)
			# ==================================================================

		pass

	# @staticmethod
	# def _chunk_key(
	# 		chunk: WordChunk
	# ) -> Tuple[int, int, str]:
	# 	return chunk.start, chunk.end, chunk.norm


	# -------------------------
	# Delete document
	# -------------------------


	# -------------------------
	# Search document
	# -------------------------






		# def __load_data_node__(self, node_list, cluster, id_, type_, text_, layer_, intent_, value_):
		# 	if cluster:
		# 		node_list[0].append((id_, cluster.index))
		# 	if cluster and cluster.connect_index:
		# 		node_list[1].append((id_, cluster.connect_index[0]))
		#

		# 	name = "REPRESENT::" + cluster.p_name
		# 	lemma = "NODE::INT::" + cluster.p_lemma
		# 	if cluster.f_value[0]:
		# 		lemma += "-Meaning"
		# 	else:
		# 		lemma += "-Intent"
		#
		# 	self.__load_data_node__(
		# 		None, None, name, "Represent", cluster.p_name, self.static_layer + cluster.layer, None, None
		# 	)
		# 	self.__load_data_node__(
		# 		node_list, cluster, lemma, "NodeInt", cluster.p_lemma, self.static_layer + cluster.layer,
		# 		cluster.f_intent[0], cluster.f_value[0]
		# 	)






	def draw_graph(self):
		out = Path(self.output_file)
		out.parent.mkdir(parents=True, exist_ok=True)

		graph_store = {}
		visited = set()

		graph_store["root"] = self._serialize_graph(
			self.graph, graph_id="root", parent_id=None, breadcrumb=("root",)
		)
		store_json = json.dumps(graph_store, ensure_ascii=False)

		html_text = f"""
			<!DOCTYPE html>
			<html lang="ru">
				<head>
					<meta charset="utf-8" />
					<meta name="viewport" content="width=device-width, initial-scale=1" />
					<title>Graph Viewer</title>
					
					<script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
					
					<style>
						html, body {{
							margin: 0;
							width: 100%;
							height: 100%;
							overflow: hidden;
							font-family: Arial, sans-serif;
							background: #F8FAFC;
						}}
						
						#toolbar {{
							height: 56px;
							display: flex;
							align-items: center;
							gap: 12px;
							padding: 0 16px;
							border-bottom: 1px solid #E5E7EB;
							background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%);
							box-sizing: border-box;
						}}
						
						#backBtn {{
							appearance: none;
							border: 1px solid #CBD5E1;
							background: white;
							color: #0F172A;
							border-radius: 10px;
							padding: 8px 14px;
							cursor: pointer;
							font-size: 14px;
							font-weight: 600;
							box-shadow: 0 1px 2px rgba(0,0,0,0.05);
						}}

						#backBtn:disabled {{
							opacity: 0.45;
							cursor: not-allowed;
						}}
						
						#path {{
							font-size: 14px;
							color: #334155;
							overflow: hidden;
							text-overflow: ellipsis;
							white-space: nowrap;
							flex: 1;
						}}

						#hint {{
							font-size: 12px;
							color: #64748B;
							white-space: nowrap;
							flex: 1;
						}}

						#mynetwork {{
							width: 100%;
							height: calc(100% - 56px);
							background: radial-gradient(circle at 20% 20%, #FFFFFF 0%, #F8FAFC 60%, #EEF2FF 100%);
						}}
					</style>
				</head>
				<body>
					<div id="toolbar">
						<button id="backBtn" disabled>← Назад</button>
						<div id="path">root</div>
						<div id="hint">###</div>
					</div>
					<div id="mynetwork"></div>
					
					<script>
						const DATA = {store_json};
						
						
						
			const container = document.getElementById("mynetwork");
			const backBtn = document.getElementById("backBtn");
			const pathEl = document.getElementById("path");

			const state = {{
				currentGraphId: "root",
				history: []
			}};
				
			const data = {{
				nodes: new vis.DataSet([]),
				edges: new vis.DataSet([])
			}};

			const options = {{
				autoResize: true,
				interaction: {{
					hover: true,
					multiselect: false,
					navigationButtons: true,
					keyboard: true
				}},
				physics: {{
					enabled: true,
					stabilization: {{
						iterations: 150
					}},
					barnesHut: {{
						gravitationalConstant: -25000,
						springLength: 140,
						springConstant: 0.04,
						damping: 0.12
					}}
				}},
				nodes: {{
					borderWidth: 2,
					shadow: true,
					margin: 10,
					font: {{
						face: "Arial"
					}}
				}},
				edges: {{
					arrows: {{
						to: {{
							enabled: true,
							scaleFactor: 0.7
						}}
					}},
					width: 1.2,
					color: {{
						color: "#94A3B8",
						highlight: "#0F172A"
					}},
					smooth: {{
						type: "dynamic"
					}},
					font: {{
						face: "Arial"
					}}
				}}
			}};

			const network = new vis.Network(container, data, options);

			function renderGraph(graphId, pushHistory = true) {{
				const g = DATA[graphId];
				if (!g) return;

				if (pushHistory && state.currentGraphId !== graphId) {{
					state.history.push(state.currentGraphId);
				}}

				state.currentGraphId = graphId;
				pathEl.textContent = g.breadcrumb || graphId;
				backBtn.disabled = state.history.length === 0;

				data.nodes.clear();
				data.edges.clear();
				data.nodes.add(g.nodes);
				data.edges.add(g.edges);

				network.stabilize(120);
				network.fit({{ animation: {{ duration: 350, easingFunction: "easeInOutQuad" }} }});
			}}

			backBtn.addEventListener("click", () => {{
				if (state.history.length === 0) return;
				const prev = state.history.pop();
				renderGraph(prev, false);
				backBtn.disabled = state.history.length === 0;
			}});

			network.on("doubleClick", function(params) {{
				if (!params.nodes || params.nodes.length !== 1) return;

				const nodeId = params.nodes[0];
				const g = DATA[state.currentGraphId];
				if (!g) return;

				const meta = g.nodeMeta[nodeId];
				if (!meta || meta.kind !== "subgraph") return;

				const childId = meta.child;
				if (!DATA[childId]) return;

				renderGraph(childId, true);
			}});

			renderGraph("root", false);		
						
						
					</script>
				</body>
			</html>
		"""

		out.write_text(html_text, encoding="utf-8")
		return str(out)

	# 	const container = document.getElementById("mynetwork");
	# 	const data = {{
	# 	  nodes: new vis.DataSet(DATA.nodes),
	# 	  edges: new vis.DataSet(DATA.edges)
	# 	}};
	#
	# 	const options = {{
	# 	  autoResize: true,
	# 	  interaction: {{
	# 		hover: true,
	# 		multiselect: false,
	# 		navigationButtons: true,
	# 		keyboard: true
	# 	  }},
	# 	  physics: {{
	# 		enabled: true,
	# 		stabilization: {{
	# 		  iterations: 200
	# 		}},
	# 		barnesHut: {{
	# 		  gravitationalConstant: -30000,
	# 		  springLength: 140,
	# 		  springConstant: 0.04,
	# 		  damping: 0.12
	# 		}}
	# 	  }},
	# 	  nodes: {{
	# 		borderWidth: 2,
	# 		shadow: true,
	# 		margin: 10,
	# 		font: {{
	# 		  face: "Arial"
	# 		}}
	# 	  }},
	# 	  edges: {{
	# 		arrows: {{
	# 		  to: {{
	# 			enabled: true,
	# 			scaleFactor: 0.8
	# 		  }}
	# 		}},
	# 		width: 1.2,
	# 		color: {{
	# 		  color: "#94A3B8",
	# 		  highlight: "#0F172A"
	# 		}},
	# 		smooth: {{
	# 		  type: "dynamic"
	# 		}},
	# 		font: {{
	# 		  face: "Arial"
	# 		}}
	# 	  }}
	# 	}};
	#
	# 	const network = new vis.Network(container, data, options);
	#
	# 	network.once("stabilizationIterationsDone", function () {{
	# 	  network.fit({{ animation: {{ duration: 350, easingFunction: "easeInOutQuad" }} }});
	# 	}});
	#
	# 	network.on("doubleClick", function (params) {{
	# 	  if (params.nodes && params.nodes.length === 1) {{
	# 		const nodeId = params.nodes[0];
	# 		const node = data.nodes.get(nodeId);
	# 		console.log("node:", node);
	# 	  }}
	# 	}});
	#   </script>
	# </body>
	# </html>
	# """

	def _serialize_graph(
			self, graph: nx.DiGraph,
			graph_id: str = "root", parent_id: Optional[str] = None, breadcrumb = ()
	):
		# if graph_id in visited:
		# 	return
		# visited.add(graph_id)

		# --- Nodes ---
		nodes = self._serialize_nodes(graph)

		# --- Edges ---
		edges = self._serialize_edges(graph)

		# return nodes, edges
		return {
			"id": graph_id,
			"parentId": parent_id,
			"breadcrumb": " / ".join(breadcrumb) if breadcrumb else "root",
			"nodes": nodes,
			"edges": edges,
			# "nodeMeta": node_meta,
		}

	def _serialize_nodes(self, graph: nx.DiGraph):
		nodes = []

		for idx, (node, attrs) in enumerate(graph.nodes(data=True)):
			node_id = node
			attrs   = dict(attrs or {})

			node_label = attrs.get("label", attrs["data"].get("text", "###"))

			node_data  = attrs.get("data", {})
			node_type  = attrs.get("type", "DEFAULT")

			node_style = self._node_style(node_data, node_type)

			if node_type == "SUBGRAPH":
				# subgraph_obj = None
				# if isinstance(node, nx.Graph):
				# 	subgraph_obj = node
				# elif isinstance(attrs.get("data"), nx.Graph):
				# 	subgraph_obj = attrs["data"]

				# if subgraph_obj is not None:
				# 	child_id = graph_id_for(subgraph_obj)
				# 	style = node_style("SUBGRAPH")
				#
				# 	nodes.append({
				# 		"id": vis_id,
				# 		"label": str(title),
				# 		"title": f"Двойной клик: открыть «{html_mod.escape(str(title))}»",
				# 		"shape": style["shape"],
				# 		"color": style["color"],
				# 		"font": style["font"],
				# 		"size": style["size"],
				# 		"borderWidth": 2,
				# 		"shadow": True,
				# 	})
				# 	node_meta[vis_id] = {
				# 		"kind": "subgraph",
				# 		"child": child_id,
				# 		"title": str(title),
				# 	}
				#
				# 	serialize_graph(
				# 		subgraph_obj,
				# 		graph_id=child_id,
				# 		parent_id=graph_id,
				# 		breadcrumb=breadcrumb + (str(title),),
				# 	)

				pass
			else:
				tooltip = (
					f"{html_mod.escape(str(node_label))}<br>"
					f"type:  {html_mod.escape(str(node_type))}<br>"
					f"level: [{node_data['type']} - {node_data['level']}]"
				)

				# "type": (chunk.chunk_type, chunk.lex_type),
				# "level": chunk.level,

				# if "span" in attrs:
				# 	tooltip += f"<br>span: {html_mod.escape(str(attrs['span']))}"
				# if node_type == "TERM":
				# 	tooltip += f"<br>value: {html_mod.escape(str(attrs.get('value', label)))}"

				nodes.append({
					"id":    node_id,
					"label": str(node_label),
					"title": tooltip,
					"shape": node_style["shape"],
					"color": node_style["color"],
					"font":  node_style["font"],
					"size":  node_style["size"],
					"borderWidth": 2,
					"shadow": True,
				})
				# node_meta[vis_id] = {
				# 	"kind": "node",
				# 	"type": node_type,
				# 	"title": str(label),
				# }

		return nodes

	# node_meta = {}
	# local_map = {}
	#
	# for idx, (node, attrs) in enumerate(graph.nodes(data=True)):
	# 	attrs = dict(attrs or {})
	# 	node_id = f"{graph_id}__n[{node}]"
	# 	# local_map[node] = node_id
	#
	# 	node_label = attrs.get("label", attrs["data"].get("text", "###"))
	# 	node_type  = attrs.get("type",  "DEFAULT")
	# 	node_level = attrs.get("level", (0, 0))
	#
	# 	if node_type == "SUBGRAPH":
	# 		# subgraph_obj = None
	# 		# if isinstance(node, nx.Graph):
	# 		# 	subgraph_obj = node
	# 		# elif isinstance(attrs.get("data"), nx.Graph):
	# 		# 	subgraph_obj = attrs["data"]
	#
	# 		# if subgraph_obj is not None:
	# 		# 	child_id = graph_id_for(subgraph_obj)
	# 		# 	style = node_style("SUBGRAPH")
	# 		#
	# 		# 	nodes.append({
	# 		# 		"id": vis_id,
	# 		# 		"label": str(title),
	# 		# 		"title": f"Двойной клик: открыть «{html_mod.escape(str(title))}»",
	# 		# 		"shape": style["shape"],
	# 		# 		"color": style["color"],
	# 		# 		"font": style["font"],
	# 		# 		"size": style["size"],
	# 		# 		"borderWidth": 2,
	# 		# 		"shadow": True,
	# 		# 	})
	# 		# 	node_meta[vis_id] = {
	# 		# 		"kind": "subgraph",
	# 		# 		"child": child_id,
	# 		# 		"title": str(title),
	# 		# 	}
	# 		#
	# 		# 	serialize_graph(
	# 		# 		subgraph_obj,
	# 		# 		graph_id=child_id,
	# 		# 		parent_id=graph_id,
	# 		# 		breadcrumb=breadcrumb + (str(title),),
	# 		# 	)
	#
	# 		pass
	# 	else:
	# 		node_label = attrs.get("label", attrs["data"].get("text", "###"))
	# 		node_style = Graph._node_style(node_type, node_level)
	#
	# 		tooltip = (
	# 			f"{html_mod.escape(str(node_label))}<br>"
	# 			f"type:  {html_mod.escape(str(node_type))}<br>"
	# 			f"level: {node_level}"
	# 		)
	# 		# if "span" in attrs:
	# 		# 	tooltip += f"<br>span: {html_mod.escape(str(attrs['span']))}"
	# 		# if node_type == "TERM":
	# 		# 	tooltip += f"<br>value: {html_mod.escape(str(attrs.get('value', label)))}"
	#
	# 		nodes.append({
	# 			"id": node_id,
	# 			"label": str(node_label),
	# 			"title": tooltip,
	# 			"shape": node_style["shape"],
	# 			"color": node_style["color"],
	# 			"font": node_style["font"],
	# 			"size": node_style.get("size", 10),
	# 			"borderWidth": 2,
	# 			"shadow": True,
	# 		})
	# 		# node_meta[vis_id] = {
	# 		# 	"kind": "node",
	# 		# 	"type": node_type,
	# 		# 	"title": str(label),
	# 		# }

	def _serialize_edges(self, graph: nx.DiGraph):
		edges = []
		edge_idx = 0

		for u, v, attrs in graph.edges(data=True):
			attrs = dict(attrs or {})
			e_type = attrs.get("label", "")

			edges.append({
				"id": f"e{edge_idx}",
				"from": str(u),
				"to": str(v),
				"arrows": "to" if graph.is_directed() else "",
				"label": e_type,
				"title": e_type,
				"color": {"color": "#94A3B8", "highlight": "#111827"},
				"smooth": {"type": "dynamic"},
				"font": {"size": 12, "align": "middle", "face": "Arial"},
			})
			edge_idx += 1

		return edges


	@staticmethod
	def _node_style(
			node_data: dict, node_type: str
	):
		style = {
			"shape": "dot",
			"size":  10,
			"color": {
				"background": "#E5E7EB",
				"border":     "#6B7280"
			},
			"font": {
				"color": "#111827",
				"size":  14,
				"face":  "Arial"
			}
		}

		if node_type in BASE_STYLES:
			style = BASE_STYLES.get(node_type, style)

			# --- Кастомизация TERM ---
			if node_type == "TERM":
				chunk_type, lex_type = node_data.get("type", (ChunkType.NONE, LexType.NONE))

				chunk_style = NODE_STYLES.get(chunk_type, NODE_STYLES[ChunkType.NONE])
				lex_style   = LEX_STYLES.get(lex_type, LEX_STYLES[LexType.NONE])

				if chunk_type != ChunkType.NONE:
					if chunk_type in (ChunkType.TYPE_1, ChunkType.TYPE_2):
						style["shape"] = "box"
					elif chunk_type == ChunkType.TYPE_3:
						style["shape"] = "dot"

					style["color"] = {
						"background": chunk_style["background"],
						"border":     chunk_style["border"],
					}

				else:
					style["shape"] = "dot"
					style["color"] = {
						"background": lex_style["background"],
						"border":     lex_style["border"],
					}
		else:

			pass

		return style
