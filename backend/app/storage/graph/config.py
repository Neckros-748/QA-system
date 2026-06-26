from backend.app.common.graph.nlp.utils.word_chunk import LexType, ChunkType


BASE_STYLES = {
	"DOCUMENT": {
		"shape": "hexagon",
		"size":  24,
		"color": {
			"background": "#FCE7F3",
			"border":     "#DB2777"
		},
		"font": {
			"color": "#0F172A",
			"size":  16,
			"face":  "Arial"
		},
	},
	"TERM": {
		"shape": "dot",
		"size":  12,
		"color": {
			"background": "###",
			"border":     "###"
		},
		"font": {
			"color": "#111827",
			"size":  14,
			"face":  "Arial"
		},
	},

# 		"SUBGRAPH": {
# 			"shape": "hexagon",
# 			"size": 22,
# 			"color": {"background": "#FCE7F3", "border": "#DB2777"},
# 			"font": {"color": "#0F172A", "size": 16, "face": "Arial"},
# 		},
# 		"TERM": {
# 			"shape": "dot",
# 			"size": 12,
# 			"color": {"background": "#E0E7FF", "border": "#4F46E5"},
# 			"font": {"color": "#111827", "size": 14, "face": "Arial"},
# 		},
# 		"DEFAULT": {
# 			"shape": "dot",
# 			"size": 10,
# 			"color": {"background": "#E5E7EB", "border": "#6B7280"},
# 			"font": {"color": "#111827", "size": 14, "face": "Arial"},
# 		},
}

NODE_STYLES = {
	ChunkType.TYPE_1: {
		"background": "#DBEAFE",
		"border": "#2563EB",
	},
	ChunkType.TYPE_2: {
		"background": "#DCFCE7",
		"border": "#16A34A",
	},
	ChunkType.TYPE_3: {
		"background": "#FEF3C7",
		"border": "#D97706",
	},

	ChunkType.NONE: {
		"background": "###",
		"border":     "###",
	},
}

LEX_STYLES = {
	LexType.NOUN: {
		"background": "#F3F4F6",
		"border": "#4338CA",
	},
	LexType.VERB: {
		"background": "#F3F4F6",
		"border": "#DB2777",
	},
	LexType.ADJ: {
		"background": "#F3F4F6",
		"border": "#0891B2",
	},
	LexType.ADV: {
		"background": "#F3F4F6",
		"border": "#7C3AED",
	},
	LexType.NUM: {
		"background": "#F3F4F6",
		"border": "#EA580C",
	},
	LexType.OTHER: {
		"background": "#F3F4F6",
		"border": "#9CA3AF",
	},

	LexType.NONE: {
		"background": "###",
		"border": "###",
	},
}

# 	# --- стили чанков ---
# 	NODE_STYLES = {
# 		ChunkType.TYPE_1: {"background": "#DBEAFE", "border": "#2563EB"},
# 		ChunkType.TYPE_2: {"background": "#DCFCE7", "border": "#16A34A"},
# 		ChunkType.TYPE_3: {"background": "#FEF3C7", "border": "#D97706"},
# 		ChunkType.NONE:  {"background": "#F3F4F6", "border": "#6B7280"},
# 	}

# 	# --- стили лексики ---
# 	LEX_STYLES = {
# 		LexType.NOUN:  {"background": "#F3F4F6", "border": "#4338CA"},
# 		LexType.VERB:  {"background": "#F3F4F6", "border": "#DB2777"},
# 		LexType.ADJ:   {"background": "#F3F4F6", "border": "#0891B2"},
# 		LexType.ADV:   {"background": "#F3F4F6", "border": "#7C3AED"},
# 		LexType.NUM:   {"background": "#F3F4F6", "border": "#EA580C"},
# 		LexType.OTHER: {"background": "#F3F4F6", "border": "#9CA3AF"},
# 	}


# 	# --- базовые стили ---
# 	BASE_STYLES = {
# 		"STRUCT::DOCUMENT": {
# 			"shape": "ellipse",
# 			"size": 24,
# 			"color": {"background": "#DBEAFE", "border": "#2563EB"},
# 			"font": {"color": "#0F172A", "size": 18, "face": "Arial"},
# 		},
# 		"STRUCT::SECTION": {
# 			"shape": "box",
# 			"size": 18,
# 			"color": {"background": "#FEF3C7", "border": "#D97706"},
# 			"font": {"color": "#0F172A", "size": 16, "face": "Arial"},
# 		},
# 		"STRUCT::PARAGRAPH": {
# 			"shape": "dot",
# 			"size": 12,
# 			"color": {"background": "#DCFCE7", "border": "#16A34A"},
# 			"font": {"color": "#0F172A", "size": 14, "face": "Arial"},
# 		},
# 	}






styles = {
	"STRUCT::DOCUMENT": {
		"shape": "ellipse",
		"size": 24,
		"color": {
			"background": "#DBEAFE",
			"border": "#2563EB"
		},
		"font": {
			"color": "#0F172A",
			"size": 18,
			"face": "Arial"
		},
	},
	"STRUCT::SECTION": {
		"shape": "box",
		"size": 18,
		"color": {"background": "#FEF3C7", "border": "#D97706"},
		"font": {"color": "#0F172A", "size": 16, "face": "Arial"},
	},
	"STRUCT::PARAGRAPH": {
		"shape": "dot",
		"size": 12,
		"color": {
			"background": "#DCFCE7",
			"border": "#16A34A"
		},
		"font": {
			"color": "#0F172A",
			"size": 14,
			"face": "Arial"
		},
	},
}

# POS=ADV
# POS=ADJ
# POS=NOUN
# POS=VERB
# POS=NUM
# POS=ADP
# POS=PRON
# POS=PROPN
# POS=AUX
# POS=SCONJ
# POS=DET
# POS=PUNCT
# POS=PART
# POS=CCONJ
# POS=SPACE
# POS=INTJ
# POS=X
# POS=SYM
