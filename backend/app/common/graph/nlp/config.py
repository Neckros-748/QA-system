NOMINAL_POS = {
	"NOUN",                     #
	"PROPN",                    #
	"PRON",                     #
	"NUM"                       #
}

HARD_SPLIT_DEPS = {
	# Соединительные связи
	"cc",                       # союз в однородных
	# "conj",                     # однородные члены
	"punct",                    # пунктиация
	# Разделители чанков
	"appos",                    # приложение
	"case",                     # предлог

}

NOUN_EXPAND_DEPS = {
	"ROOT",                     #
	"amod",                     # прилагательные
	"nmod",                     # именное определение / родительный / PP-атрибут
	"compound",                 # сложные номинальные конструкции
	"det",                      # детерминативы
	"nummod",                   # числительные
	"nummod:entity",            #
	"nummod:gov",               #
	"flat",                     #
	"flat:name",                #
	"flat:foreign",             #
}

NOUN_SUBTREE_DEPS = {
	"amod",                     # прилагательные
	"nmod",                     # именное определение / родительный / PP-атрибут
	"appos",
	"compound",
	"flat",
	"flat:name",
	"flat:foreign"
}

# CHUNK_DEPS = {
#	 "ROOT",
#	 "acl", "acl:relcl",
#	 "advcl", "advmod",
#	 "amod",
#	 "appos",
#	 "aux", "aux:pass",
#	 "case",
#	 "cc",
#	 "ccomp",
#	 "compound",
#	 "conj",
#	 "cop",
#	 "csubj", "csubj:pass",
#	 "dep",
#	 "det",
#	 "discourse",
#	 "expl",
#	 "fixed",
#	 "flat", "flat:foreign", "flat:name",
#	 "iobj",
#	 "list",
#	 "mark",
#	 "nmod",
#	 "nsubj", "nsubj:pass",
#	 "nummod", "nummod:entity", "nummod:gov",
#	 "obj",
#	 "obl", "obl:agent",
#	 "orphan",
#	 "parataxis",
#	 "punct",
#	 "xcomp",
# }