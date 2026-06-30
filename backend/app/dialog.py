from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from app.common.graph.nlp.utils.word_chunk import WordChunk
from app.storage.storage import Storage
import pickle as pc
import pymorphy3
import re
import os
from typing import Optional

morph = pymorphy3.MorphAnalyzer()


class IntentTemplate:
    def __init__(self, name, idx=None, has_value=True):
        self.name = name
        self.has_value = has_value


class IntentValue:
    def __init__(self, name, value=None):
        self.name = name
        self.value = value


class Scene:
    def __init__(self, name=None, children=None, pass_conditions=None,
                 answer=None, questions=None, short_answer=None,
                 clarifying_question=None, available_intents_list=None,
                 answer_template=None, context_terms=None):
        self.name = name
        self.children = []
        self.pass_conditions = []
        self.height = 0
        self.answer = answer
        self.questions = []
        self.short_answer = short_answer
        self.clarifying_question = clarifying_question
        self.available_intents_list = available_intents_list or []
        self.answer_template = answer_template
        self.context_terms = context_terms or []
        if children is not None:
            for child in children:
                self.add_child(child)
        if pass_conditions is not None:
            for condition in pass_conditions:
                self.add_condition(condition)
        if questions is not None:
            for question in questions:
                self.add_question(question)

    def add_condition(self, condition):
        self.pass_conditions.append(condition)

    def add_child(self, node):
        assert isinstance(node, Scene)
        self.children.append(node)

    def add_question(self, question):
        self.questions.append(question)

    def set_answer(self, answer):
        answer = answer.removesuffix(' | ')
        answer_list = answer.split(' | ')
        answer_list_final = []
        for answer_word in answer_list:
            if "Интент" in answer_word:
                to_add_intent = answer_word.split("Интент ")[1]
                answer_list_final.append(
                    IntentTemplate(name=to_add_intent))
            elif "Значение" in answer_word:
                to_add_intent = answer_word.split("Значение ")[1]
                answer_list_final.append(
                    IntentValue(name=to_add_intent))
            else:
                answer_list_final.append(answer_word)

        self.answer = answer_list_final

    def set_short_answer(self, answer):
        answer = answer.removesuffix(' | ')
        answer_list = answer.split(' | ')
        answer_list_final = []
        for answer_word in answer_list:
            if "Интент" in answer_word:
                answer_list_final.append(
                    IntentTemplate(name=answer_word.split("Интент ")[1]))
            elif "Значение" in answer_word:
                answer_list_final.append(
                    IntentValue(name=answer_word.split("Значение ")[1]))
            else:
                answer_list_final.append(answer_word)

        self.short_answer = answer_list_final

    def set_question(self, question):
        question = question.removesuffix(' | ')
        question_list = question.split(' | ')
        question_list_final = []
        for question_word in question_list:
            if "Интент" in question_word:
                question_list_final.append(
                    IntentTemplate(name=question_word.split("Интент ")[1]))
            elif "Значение" in question_word:
                question_list_final.append(
                    IntentValue(name=question_word.split("Значение ")[1]))
            else:
                question_list_final.append(question_word)
        self.questions = question_list_final

    def set_name(self, name):
        self.name = name

    def set_clarifying_question(self, clarifying_question):
        clarifying_question = clarifying_question.removesuffix(' | ')
        question_list = clarifying_question.split(' | ')
        question_list_final = []
        for question_word in question_list:
            if "Интент" in question_word:
                question_list_final.append(
                    IntentTemplate(name=question_word.split("Интент ")[1]))
            elif "Значение" in question_word:
                question_list_final.append(
                    IntentValue(name=question_word.split("Значение ")[1]))
            else:
                question_list_final.append(question_word)
        self.clarifying_question = question_list_final

    def add_intent_in_list(self, intent):
        if self.available_intents_list is None:
            self.available_intents_list = [intent]
        else:
            self.available_intents_list.append(intent)

    def print_children(self):
        for child in self.children:
            child.print_children()

    def get_testing_pretty(self):
        res = {}
        res["name"] = self.name
        res["height"] = self.height
        return res

    def get_pretty(self):
        return ("---" * self.height + self.name + ", " +
                str(self.height) + "\n")

    def print_pretty_children(self):
        child_counter = 0
        while child_counter < len(self.children) / 2:
            self.children[child_counter].print_pretty_children()
            child_counter += 1
        while child_counter < len(self.children):
            self.children[child_counter].print_pretty_children()
            child_counter += 1

    def get_testing_pretty_children(self, all_scenes):
        child_counter = 0
        while child_counter < len(self.children) / 2:
            self.children[child_counter].get_testing_pretty_children(
                all_scenes)
            child_counter += 1
        all_scenes.append(self.get_testing_pretty())
        while child_counter < len(self.children):
            self.children[child_counter].get_testing_pretty_children(
                all_scenes)
            child_counter += 1
        return all_scenes

    def get_pretty_children(self, all_scenes):
        child_counter = 0
        while child_counter < len(self.children) / 2:
            all_scenes = (self.children[child_counter].
                          get_pretty_children(all_scenes))
            child_counter += 1
        all_scenes += self.get_pretty()
        while child_counter < len(self.children):
            all_scenes = (self.children[child_counter].
                          get_pretty_children(all_scenes))
            child_counter += 1
        return all_scenes

    def set_height(self, height):
        self.height = height
        return height + 1

    def set_height_all(self, height):
        new_height = self.set_height(height)
        for child in self.children:
            child.set_height_all(new_height)

    def print_answer(self):
        answer = ""
        for ans in self.answer:
            answer += " " + ans
        answer += ' '

    def give_answer(self, intents_dicts):
        answer = ""
        for ans in self.answer:
            if isinstance(ans, IntentTemplate):
                for intent in intents_dicts:
                    if intent.get("intent") == ans.name:
                        answer += ' ' + str(intent.get("intent"))
            elif isinstance(ans, IntentValue):
                for intent in intents_dicts:
                    if intent.get("intent") == ans.name:
                        answer += ' ' + str(intent.get("meaning"))
            else:
                answer += " " + ans

        return answer

    def get_work_question(self, user_question):
        user_question_list = user_question.split()
        intent_dict = []
        intent_count = 0
        for question in self.questions:
            for elem in question:
                if type(elem) == IntentTemplate:
                    intent_count += 1
            for idx, user_word in enumerate(user_question_list):
                intent_idx = idx
                for idx2, elem in enumerate(question):
                    if ((type(elem) == IntentTemplate) and
                            (idx2 == intent_idx)):

                        elem.idx = idx
                        intent_values = (self.get_intent_values
                                         (elem.name,
                                          user_question_list, question))

                        if not intent_values:
                            intent_dict.append({"intent": elem.name,
                                                "meaning": None})
                        else:
                            intent_dict.append({"intent": elem.name,
                                                "meaning": intent_values})

                        intent_count -= 1

            if intent_count == 0:
                return intent_dict
            else:
                intent_count = 0

        return False

    def get_intent_values(self, name, user_question_list, question):
        values_list = []
        for idx2, word2 in enumerate(question):
            if type(word2) == IntentValue:
                if word2.name == name:
                    for idx, word in enumerate(user_question_list):
                        if idx2 == idx:
                            values_list.append(word)
        return values_list

    def to_scene_rec(self, scene_name):
        if self.name == scene_name:
            return self
        else:
            for child in self.children:
                result = child.to_scene_rec(scene_name)
                if result:
                    return result
            return None

    def check_scene_rec(self, intents):
        intents.sort()
        checklist = []
        for value in self.questions:
            if isinstance(value, IntentTemplate):
                if value.name in intents:
                    checklist.append(value.name)
            checklist = list(set(checklist))
            checklist.sort()
            if checklist == intents:
                return self.name
        for child in self.children:
            return child.check_scene_rec(intents)

    def pass_to_children(self, key_words):
        key_words.sort()
        pass_count = 0
        for pass_cond in self.pass_conditions:
            pass_count += 1
            checklist = []
            for int in pass_cond:
                if int in key_words:
                    checklist.append(int)
            checklist = list(set(checklist))
            checklist.sort()
            if checklist == key_words and checklist != []:
                if self.children == []:
                    return self.name
                else:
                    return self.children[pass_count - 1].name
        for child in self.children:
            return child.pass_to_children(key_words)

    def count_descendants(self, counter, descendant_list):
        if self.children is not None:
            for child in self.children:
                counter += 1
                descendant_list.append(child)
                child.count_descendants(counter, descendant_list)
        return counter, descendant_list

    def check_to_enter(self, only_intents):
        if self.available_intents_list is None or len(self.available_intents_list) == 0:
            return False

        print(f"[DEBUG] Проверка сцены '{self.name}'")
        print(f"[DEBUG]   Интенты сцены: {self.available_intents_list}")
        print(f"[DEBUG]   Интенты вопроса: {only_intents}")

        # Проверяем, что все интенты из сцены есть в интентах вопроса
        # Поддерживаем как отдельные слова, так и фразы
        for intent in self.available_intents_list:
            # Если интент - фраза (содержит пробел)
            if ' ' in intent:
                # Проверяем, что все слова фразы есть в интентах вопроса
                words = intent.split()
                if not all(word in only_intents for word in words):
                    print(f"[DEBUG]   Фраза '{intent}' не найдена полностью в {only_intents}")
                    return False
            else:
                # Если отдельное слово - проверяем наличие
                if intent not in only_intents:
                    print(f"[DEBUG]   Интент '{intent}' не найден в {only_intents}")
                    return False

        print(f"[DEBUG]   Совпадение найдено!")
        return True

    def generate_answer_from_template(self, intent_values: List[Dict], storage: Storage, question) -> Tuple[
        str, Dict[str, List[str]]]:
        if not self.answer_template:
            return self._generate_fallback_answer(intent_values, storage), {}

        if isinstance(question, list):
            string_parts = []
            for item in question:
                if isinstance(item, str):
                    string_parts.append(item)
                elif hasattr(item, 'name') and isinstance(item.name, str):
                    string_parts.append(item.name)
            question = ' '.join(string_parts)

        answer = self.answer_template
        sources = {}

        # Кэшируем значения для каждого интента, чтобы не искать повторно
        cache = {}

        placeholders = re.findall(r'\{([^:}]+)(?::([^}]+))?\}', answer)

        for placeholder in placeholders:
            intent_name = placeholder[0]
            value_type = placeholder[1] if len(placeholder) > 1 else None

            # Проверяем кэш
            if intent_name in cache:
                found_values = cache[intent_name]['values']
                intent_sources = cache[intent_name]['sources']
            else:
                found_values = []
                intent_sources = []

                for item in intent_values:
                    if item['intent'] == intent_name and item['meaning']:
                        found_values = item['meaning']
                        intent_sources = item.get('sources', [])
                        break

                if not found_values:
                    graph_values, graph_sources = get_all_values_with_sources_for_intent(intent_name, storage)
                    found_values = find_values_in_question(graph_values, question)
                    if not found_values and graph_values:
                        found_values = graph_values[:3]
                        intent_sources = graph_sources[:3]

                if not found_values and ' ' in intent_name:
                    parts = intent_name.split()
                    for part in parts:
                        part_values, part_sources = get_all_values_with_sources_for_intent(part, storage)
                        if part_values:
                            found_values.extend(part_values[:2])
                            intent_sources.extend(part_sources[:2])

                if found_values:
                    found_values = list(set(found_values))
                    if intent_sources:
                        sources[intent_name] = list(set(intent_sources))

                # Сохраняем в кэш
                cache[intent_name] = {
                    'values': found_values,
                    'sources': intent_sources
                }

            if found_values:
                inflected_values = []
                for val in found_values:
                    if val and isinstance(val, str):
                        words = val.split()
                        inflected_words = inflect_words(words, 'gent')
                        inflected_values.append(' '.join(inflected_words))
                found_values = inflected_values

            if found_values:
                if value_type == 'list':
                    replacement = '\n- ' + '\n- '.join(found_values)
                elif value_type == 'count':
                    replacement = str(len(found_values))
                else:
                    replacement = ', '.join(found_values)
            else:
                replacement = intent_name

            answer = answer.replace(f'{{{intent_name}{":" + value_type if value_type else ""}}}', replacement)

        return answer, sources

    def _generate_fallback_answer(self, intent_values: List[Dict], storage: Storage) -> str:
        if not intent_values:
            return "Информация по вашему запросу не найдена."

        answer_parts = []
        for item in intent_values:
            intent = item['intent']
            meaning = item['meaning']
            values = get_all_values_for_intent(intent, storage)

            if meaning:
                answer_parts.append(f"• {intent}: {', '.join(meaning)}")
                if values:
                    extra = [v for v in values[:3] if v not in meaning]
                    if extra:
                        answer_parts.append(f"  Связанные термины: {', '.join(extra)}")
            else:
                if values:
                    answer_parts.append(f"• {intent}: {', '.join(values[:3])}")
                else:
                    answer_parts.append(f"• {intent}: информация найдена в документе")

        return '\n'.join(answer_parts)


class SceneTree:
    def __init__(self, root):
        self.root = root

    def to_scene(self, scene_name):
        return self.root.to_scene_rec(scene_name)

    def print_nodes(self):
        self.root.print_children()

    def print_pretty_nodes(self):
        self.root.print_pretty_children()

    def set_height_tree(self):
        self.root.set_height_all(0)

    def get_testing_pretty_nodes(self):
        all_scenes = []
        self.root.get_testing_pretty_children(all_scenes)
        return all_scenes

    def get_pretty_nodes(self):
        all_scenes = ""
        all_scenes += self.root.get_pretty_children(all_scenes)
        return all_scenes

    def get_final_nodes(self):
        all_scenes += self.root.get_pretty_children(all_scenes)

    def scene_add(self, parent_scene, name=None, children=None,
                  pass_conditions=None, answer=None, questions=None,
                  clarifying_question=None):
        new_scene = Scene(name=name, children=children,
                          pass_conditions=pass_conditions, answer=answer,
                          questions=questions,
                          clarifying_question=clarifying_question)

        parent_scene.add_child(new_scene)
        return new_scene

    def find_scene(self, intents):
        self.root.check_scene_rec(intents)

    def get_scenes_list(self):
        counter, scenes_list = self.root.count_descendants(0, [self.root])
        return counter, scenes_list

    def final_pass_to_scene(self, only_intents):
        if not only_intents:
            return False

        print(f"[DEBUG] Поиск сцены для интентов: {only_intents}")

        all_scenes = []
        self._collect_all_scenes(self.root, all_scenes)
        all_scenes.sort(key=lambda x: x.height, reverse=True)

        for scene in all_scenes:
            if scene.name == "root":
                continue
            if scene.check_to_enter(only_intents):
                print(f"[DEBUG] Найдена подходящая сцена: {scene.name}")
                return scene

        print(f"[DEBUG] Подходящая сцена не найдена")
        return False

    def _collect_all_scenes(self, scene: Scene, result: List[Scene]):
        if scene.name != "root":
            result.append(scene)
        for child in scene.children:
            self._collect_all_scenes(child, result)


# ==============================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ==============================================================================

def inflect_words(words: List[str], case: str = 'gent') -> List[str]:
    if not words:
        return []

    inflected = []
    for word in words:
        if word and isinstance(word, str):
            parsed = morph.parse(word)[0]
            inflected_word = parsed.inflect({case})
            if inflected_word:
                inflected.append(inflected_word.word)
            else:
                inflected.append(word)

    return inflected


# ==============================================================================
# ФУНКЦИИ ДЛЯ РАБОТЫ С STORAGE
# ==============================================================================

# app/dialog.py - замените функцию

def find_intents_from_word_chunks(word_chunks: List[WordChunk], storage: Storage) -> List[str]:
    intents = []

    graph = get_graph_from_storage(storage)
    if graph is None:
        print("[WARNING] Граф не найден в storage")
        return intents

    try:
        all_nodes = graph.get_all_nodes()
    except Exception as e:
        print(f"[WARNING] Ошибка получения узлов графа: {e}")
        return intents

    for chunk in word_chunks:
        if hasattr(chunk, 'norm'):
            lemma = chunk.norm
        elif isinstance(chunk, str):
            lemma = chunk
        else:
            continue

        if lemma in all_nodes:
            node_data = all_nodes[lemma]
            if node_data.get('type') and node_data['type'][0] == 'TERM':
                intents.append(lemma)

    return list(set(intents))


def get_all_values_with_sources_for_intent(intent_lemma: str, storage: Storage) -> Tuple[List[str], List[str]]:
    values = []
    sources = []

    # Пробуем получить граф из разных источников
    graph = None
    if hasattr(storage, 'graph_index'):
        graph = storage.graph_index
    elif hasattr(storage, 'graph'):
        graph = storage.graph
    elif hasattr(storage, 'get_graph'):
        graph = storage.get_graph()

    if graph is None:
        print("[WARNING] Граф не найден в storage")
        return values, sources

    try:
        all_nodes = graph.get_all_nodes()
    except Exception as e:
        print(f"[WARNING] Ошибка получения узлов графа: {e}")
        return values, sources

    if intent_lemma in all_nodes:
        node_data = all_nodes[intent_lemma]
        doc_sources = node_data.get('documents', {})

        for relation_type in ['in', 'out']:
            if relation_type in node_data:
                for rel_key, rel_values in node_data[relation_type].items():
                    if rel_key == 'link':
                        if isinstance(rel_values, list):
                            for val in rel_values:
                                if val and isinstance(val, str):
                                    values.append(val)
                                    if val in all_nodes:
                                        val_sources = all_nodes[val].get('documents', {})
                                        for doc_id, doc_refs in val_sources.items():
                                            if isinstance(doc_refs, list):
                                                sources.extend(doc_refs)

        for doc_id, doc_refs in doc_sources.items():
            if isinstance(doc_refs, list):
                sources.extend(doc_refs)

    values = [v for v in set(values) if v and isinstance(v, str)]
    sources = [s for s in set(sources) if s and isinstance(s, str)]

    return values, sources


def get_related_terms(intent_lemma: str, storage: Storage) -> List[str]:
    related = []

    # Пробуем получить граф из разных источников
    graph = None
    if hasattr(storage, 'graph_index'):
        graph = storage.graph_index
    elif hasattr(storage, 'graph'):
        graph = storage.graph
    elif hasattr(storage, 'get_graph'):
        graph = storage.get_graph()

    if graph is None:
        print("[WARNING] Граф не найден в storage")
        return related

    try:
        all_nodes = graph.get_all_nodes()
    except Exception as e:
        print(f"[WARNING] Ошибка получения узлов графа: {e}")
        return related

    if intent_lemma in all_nodes:
        node_data = all_nodes[intent_lemma]

        if 'parent' in node_data:
            if isinstance(node_data['parent'], list):
                for p in node_data['parent']:
                    if p and isinstance(p, str):
                        related.append(p)
            elif isinstance(node_data['parent'], dict):
                for parent_values in node_data['parent'].values():
                    if isinstance(parent_values, list):
                        for p in parent_values:
                            if p and isinstance(p, str):
                                related.append(p)

        for node_label, node_data2 in all_nodes.items():
            if node_label != intent_lemma:
                if 'parent' in node_data2:
                    if isinstance(node_data2['parent'], list):
                        if intent_lemma in node_data2['parent']:
                            if node_label and isinstance(node_label, str):
                                related.append(node_label)
                    elif isinstance(node_data2['parent'], dict):
                        for parent_values in node_data2['parent'].values():
                            if isinstance(parent_values, list) and intent_lemma in parent_values:
                                if node_label and isinstance(node_label, str):
                                    related.append(node_label)

    return list(set(related))


def get_values_for_intent(intent_lemma: str, storage: Storage) -> List[str]:
    return get_all_values_for_intent(intent_lemma, storage)


def find_values_in_question(values: List[str], question_text) -> List[str]:
    if not values:
        return []

    if not isinstance(values, list):
        return []

    if not question_text:
        return []

    if isinstance(question_text, list):
        string_parts = []
        for item in question_text:
            if isinstance(item, str):
                string_parts.append(item)
            elif hasattr(item, 'name') and isinstance(item.name, str):
                string_parts.append(item.name)
        question_text = ' '.join(string_parts)

    found_values = []
    question_lower = question_text.lower()

    for value in values:
        if value and isinstance(value, str) and value.lower() in question_lower:
            found_values.append(value)

    return found_values


def get_document_name(doc_id: str, storage: Storage) -> str:
    return doc_id


def process_question_with_storage(question, storage: Storage, app) -> Tuple[List[WordChunk], np.ndarray, List[str]]:
    if isinstance(question, list):
        string_parts = []
        for item in question:
            if isinstance(item, str):
                string_parts.append(item)
            elif hasattr(item, 'name') and isinstance(item.name, str):
                string_parts.append(item.name)
        question = ' '.join(string_parts)

    processed_question = app.annotator.request_preprocessing(question)

    # Исправление: request_processing может возвращать одно или два значения
    result = app.annotator.request_processing(processed_question)

    # Проверяем тип результата
    if isinstance(result, tuple) and len(result) >= 2:
        word_chunks, embedding = result[0], result[1]
    elif isinstance(result, list):
        # Если возвращает список WordChunk
        word_chunks = result
        # Создаем пустой embedding если его нет
        embedding = np.array([])
    else:
        # Если возвращает что-то другое
        word_chunks = result if result else []
        embedding = np.array([])

    intents = find_intents_from_word_chunks(word_chunks, storage)

    return word_chunks, embedding, intents


def use_clarifying_question(scene: Scene, intents_values: List[Dict], storage: Storage) -> str:
    clarifying_question_return = ''

    for word in scene.clarifying_question:
        if isinstance(word, IntentTemplate):
            found = False
            for item in intents_values:
                if item['intent'] == word.name:
                    clarifying_question_return += word.name
                    found = True
                    break
            if not found:
                clarifying_question_return += word.name
        elif isinstance(word, IntentValue):
            for item in intents_values:
                if item['intent'] == word.name:
                    clarifying_question_return += word.name
                    break
        elif isinstance(word, str):
            clarifying_question_return += word
        clarifying_question_return += ' '

    return clarifying_question_return.strip()


def new_dialog(question,
               storage: Storage,
               dialog_tree: 'SceneTree',
               app,
               previous_intents: Optional[List[str]] = None) -> List[Any]:
    # Проверяем состояние графа при первом вызове
    graph_info = check_graph_storage(storage)
    print(f"[DEBUG] Состояние графа: {graph_info}")

    print(storage)
    print("jdsdfhsfkjhksdfjhksfhhke")
    print_graph_to_console(storage)

    if isinstance(question, list):
        string_parts = []
        for item in question:
            if isinstance(item, str):
                string_parts.append(item)
            elif hasattr(item, 'name') and isinstance(item.name, str):
                string_parts.append(item.name)
        question_str = ' '.join(string_parts)
    else:
        question_str = question

    word_chunks, embedding, question_intents = process_question_with_storage(question_str, storage, app)

    print(f"[DEBUG] Найденные интенты из вопроса: {question_intents}")

    if previous_intents:
        all_intents = list(set(question_intents + previous_intents))
    else:
        all_intents = question_intents

    print(f"[DEBUG] Все интенты: {all_intents}")

    current_scene = dialog_tree.final_pass_to_scene(all_intents)

    if not current_scene or current_scene.name == "root":
        return [
            "Я не нашел точного соответствия. Пожалуйста, уточните ваш вопрос.",
            "root",
            [],
            [],
            [],
            all_intents,
            {}
        ]

    print(f"[DEBUG] Найденная сцена: {current_scene.name}")

    scene_intents = []
    for question in current_scene.questions:
        for word in question:
            if isinstance(word, IntentTemplate):
                scene_intents.append(word.name)
    scene_intents = list(set(scene_intents))

    intent_values = []
    for intent in scene_intents:
        all_values, all_sources = get_all_values_with_sources_for_intent(intent, storage)
        found_values = find_values_in_question(all_values, question_str)
        found_sources = []

        if found_values:
            for val in found_values:
                if val in all_values:
                    idx = all_values.index(val)
                    if idx < len(all_sources):
                        found_sources.append(all_sources[idx])
        else:
            if all_values:
                found_values = all_values[:3]
                found_sources = all_sources[:3] if all_sources else []

        if not found_values and ' ' in intent:
            parts = intent.split()
            combined_values = []
            combined_sources = []
            for part in parts:
                part_values, part_sources = get_all_values_with_sources_for_intent(part, storage)
                part_found = find_values_in_question(part_values, question_str)
                if part_found:
                    for val in part_found:
                        if val in part_values:
                            idx = part_values.index(val)
                            if idx < len(part_sources):
                                combined_sources.append(part_sources[idx])
                    combined_values.extend(part_found)
                elif part_values:
                    combined_values.extend(part_values[:2])
                    combined_sources.extend(part_sources[:2] if part_sources else [])
            if combined_values:
                found_values = list(set(combined_values))
                found_sources = list(set(combined_sources))

        if not found_values:
            related = get_related_terms(intent, storage)
            if related:
                found_values = related[:3]
                for rel in found_values:
                    _, rel_sources = get_all_values_with_sources_for_intent(rel, storage)
                    found_sources.extend(rel_sources)

        if found_values:
            intent_values.append({
                'intent': intent,
                'meaning': found_values,
                'sources': list(set(found_sources)) if found_sources else []
            })
        else:
            intent_values.append({'intent': intent, 'meaning': None, 'sources': []})

    if current_scene.answer_template:
        answer, sources = current_scene.generate_answer_from_template(intent_values, storage, question_str)
    else:
        answer = current_scene._generate_fallback_answer(intent_values, storage)
        sources = {}

    all_sources = {}
    for item in intent_values:
        if item.get('sources'):
            for src in item['sources']:
                if '[' in src and ']' in src:
                    doc_id = src.split('[')[0].rstrip('_')
                    ref = src
                else:
                    doc_id = '1-1-1'
                    ref = src

                if doc_id not in all_sources:
                    all_sources[doc_id] = []
                all_sources[doc_id].append(ref)

    # Вывод найденных терминов и значений (ВСЕ интенты)
    intent_info = "\n\n📊 Найденные термины и их значения:"

    for intent in all_intents:
        all_values, all_sources_for_intent = get_all_values_with_sources_for_intent(intent, storage)

        if all_values is None:
            all_values = []
        if not isinstance(all_values, list):
            all_values = []

        found_values = find_values_in_question(all_values, question_str)
        found_sources = []

        if not found_values:
            if all_values:
                found_values = all_values[:3]
                if all_sources_for_intent:
                    found_sources = all_sources_for_intent[:3]
        else:
            for val in found_values:
                if val in all_values:
                    idx = all_values.index(val)
                    if all_sources_for_intent and idx < len(all_sources_for_intent):
                        found_sources.append(all_sources_for_intent[idx])

        if not found_values:
            related = get_related_terms(intent, storage)
            if related:
                found_values = related[:3]
                for rel in found_values:
                    _, rel_sources = get_all_values_with_sources_for_intent(rel, storage)
                    if rel_sources:
                        found_sources.extend(rel_sources[:2])

        if found_values:
            found_values = list(set(found_values))
            intent_info += f"\n• {intent}: {', '.join(found_values)}"

            if found_sources:
                unique_sources = list(set(found_sources))
                intent_info += f"\n  📄 Источники: {', '.join(unique_sources[:3])}"
        else:
            intent_info += f"\n• {intent}: значения не найдены"

    if all_sources:
        source_info = "\n\n📄 **Источники информации:**"
        for doc_id, refs in all_sources.items():
            doc_name = get_document_name(doc_id, storage)
            source_info += f"\n• Документ: {doc_name}"
            for ref in set(refs):
                source_info += f"\n  - {ref}"
        answer = answer + source_info

    answer = answer + intent_info

    return [answer, current_scene.name, intent_values, scene_intents, [], all_intents, all_sources]


def make_words_normal(question, storage):
    words = question.split()
    normal_words = []
    for word in words:
        parsed = morph.parse(word)[0]
        normal_words.append(parsed.normal_form)
    return ' '.join(normal_words)


def find_intents(all_intents_text, question_text):
    question_words = question_text.split()
    found_intents = []
    for intent in all_intents_text:
        if intent in question_words:
            found_intents.append(intent)
    return found_intents





def create_example_dialog_tree() -> SceneTree:
    return create_simple_dialog_tree()


def save_dialog_tree(tree: SceneTree, filepath: str):
    with open(filepath, "wb") as f:
        pc.dump(tree, f)


def load_dialog_tree(filepath: str) -> SceneTree:
    with open(filepath, "rb") as f:
        tree = pc.load(f)
    return tree

def create_empty_dialog_tree() -> SceneTree:
    """
    Создать пустое дерево диалога (только корень)

    Returns:
        SceneTree: Пустое дерево с корневой сценой
    """
    root = Scene(
        name="root",
        answer=["Добро пожаловать! Дерево диалога пусто. Создайте сцены для начала работы."],
        questions=[],
        available_intents_list=[]
    )
    tree = SceneTree(root)
    tree.set_height_tree()
    return tree


def save_dialog_tree_safe(tree: SceneTree, filepath: str) -> bool:
    """
    Сохранить дерево диалога в файл с обработкой ошибок

    Args:
        tree: Дерево диалога
        filepath: Путь к файлу

    Returns:
        bool: True если сохранение успешно, False в противном случае
    """
    try:
        # Создаем директорию если её нет
        directory = os.path.dirname(filepath)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            print(f"[INFO] Создана директория: {directory}")

        with open(filepath, "wb") as f:
            pc.dump(tree, f)
        print(f"[INFO] Дерево успешно сохранено в {filepath}")
        return True
    except PermissionError as e:
        print(f"[ERROR] Нет прав на запись в файл {filepath}: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Ошибка сохранения дерева: {e}")
        return False


def load_dialog_tree_safe(filepath: str) -> Optional[SceneTree]:
    """
    Загрузить дерево диалога из файла с обработкой ошибок

    Args:
        filepath: Путь к файлу

    Returns:
        SceneTree: Загруженное дерево или None в случае ошибки
    """
    try:
        if not os.path.exists(filepath):
            print(f"[WARNING] Файл не найден: {filepath}")
            return None

        if os.path.getsize(filepath) == 0:
            print(f"[WARNING] Файл пуст: {filepath}")
            return None

        with open(filepath, "rb") as f:
            tree = pc.load(f)

        if not isinstance(tree, SceneTree):
            print(f"[ERROR] Неверный формат данных в файле {filepath}")
            return None

        print(f"[INFO] Дерево успешно загружено из {filepath}")
        return tree
    except FileNotFoundError:
        print(f"[WARNING] Файл не найден: {filepath}")
        return None
    except pc.UnpicklingError as e:
        print(f"[ERROR] Ошибка распаковки файла {filepath}: {e}")
        return None
    except Exception as e:
        print(f"[ERROR] Ошибка загрузки дерева из {filepath}: {e}")
        return None


def load_or_create_dialog_tree(filepath: str) -> SceneTree:
    """
    Загрузить дерево или создать пустое, если файл не существует или поврежден

    Args:
        filepath: Путь к файлу

    Returns:
        SceneTree: Загруженное или новое пустое дерево
    """
    tree = load_dialog_tree_safe(filepath)

    if tree is not None:
        return tree

    print(f"[INFO] Создание пустого дерева диалога")
    tree = create_empty_dialog_tree()

    # Пытаемся сохранить пустое дерево
    save_dialog_tree_safe(tree, filepath)

    return tree


def get_tree_info(tree: SceneTree) -> Dict[str, Any]:
    """
    Получить информацию о дереве

    Args:
        tree: Дерево диалога

    Returns:
        Dict: Информация о дереве
    """
    if not tree:
        return {
            "exists": False,
            "scenes_count": 0,
            "max_depth": 0
        }

    count, scenes = tree.get_scenes_list()
    return {
        "exists": True,
        "scenes_count": count,
        "max_depth": tree.root.height
    }


def scene_to_dict(scene: Scene) -> Dict[str, Any]:
    """
    Преобразовать сцену в словарь для JSON сериализации

    Args:
        scene: Сцена

    Returns:
        Dict: Словарь с данными сцены
    """
    return {
        "name": scene.name,
        "height": scene.height,
        "answer_template": scene.answer_template,
        "short_answer": scene.short_answer if scene.short_answer else "",
        "clarifying_question": scene.clarifying_question if scene.clarifying_question else "",
        "available_intents_list": scene.available_intents_list or [],
        "pass_conditions": scene.pass_conditions or [],
        "questions": scene.questions or [],
        "answer": scene.answer if scene.answer else "",
        "children": [scene_to_dict(child) for child in scene.children]
    }


def tree_to_dict(tree: SceneTree) -> Dict[str, Any]:
    """
    Преобразовать дерево в словарь для JSON сериализации

    Args:
        tree: Дерево диалога

    Returns:
        Dict: Словарь с данными дерева
    """
    if not tree:
        return {"name": "root", "children": []}
    return scene_to_dict(tree.root)


def dict_to_scene(data: Dict[str, Any]) -> Scene:
    """
    Преобразовать словарь в сцену

    Args:
        data: Словарь с данными сцены

    Returns:
        Scene: Сцена
    """
    scene = Scene(
        name=data.get("name", ""),
        answer_template=data.get("answer_template", ""),
        short_answer=data.get("short_answer", ""),
        clarifying_question=data.get("clarifying_question", ""),
        available_intents_list=data.get("available_intents_list", [])
    )

    if "pass_conditions" in data:
        scene.pass_conditions = data["pass_conditions"]

    if "questions" in data:
        scene.questions = data["questions"]

    if "children" in data:
        for child_data in data["children"]:
            child = dict_to_scene(child_data)
            scene.add_child(child)

    return scene


def find_scene_by_name(tree: SceneTree, scene_name: str) -> Optional[Scene]:
    """
    Найти сцену по имени

    Args:
        tree: Дерево диалога
        scene_name: Имя сцены

    Returns:
        Scene: Найденная сцена или None
    """
    if not tree:
        return None
    return tree.to_scene(scene_name)


def delete_scene_by_name(tree: SceneTree, scene_name: str) -> bool:
    """
    Удалить сцену по имени

    Args:
        tree: Дерево диалога
        scene_name: Имя сцены для удаления

    Returns:
        bool: True если удаление успешно
    """
    if not tree or scene_name == "root":
        return False

    def find_and_remove(parent: Scene, name: str) -> bool:
        for i, child in enumerate(parent.children):
            if child.name == name:
                parent.children.pop(i)
                return True
            if find_and_remove(child, name):
                return True
        return False

    result = find_and_remove(tree.root, scene_name)
    if result:
        tree.set_height_tree()
    return result


def create_scene_in_tree(tree: SceneTree, parent_name: str, scene_data: Dict[str, Any]) -> Optional[str]:
    """
    Создать новую сцену в дереве

    Args:
        tree: Дерево диалога
        parent_name: Имя родительской сцены
        scene_data: Данные новой сцены

    Returns:
        str: Имя созданной сцены или None
    """
    print("Создание дерева")

    if not tree:
        return None

    parent = tree.to_scene(parent_name) if parent_name else tree.root
    if not parent:
        parent = tree.root

    new_scene = Scene(
        name=scene_data.get("name", "new_scene"),
        answer_template=scene_data.get("answer_template", ""),
        short_answer=scene_data.get("short_answer", ""),
        clarifying_question=scene_data.get("clarifying_question", ""),
        available_intents_list=scene_data.get("available_intents_list", [])
    )

    if "questions" in scene_data and scene_data["questions"]:
        new_scene.questions = scene_data["questions"]

    if "pass_conditions" in scene_data and scene_data["pass_conditions"]:
        new_scene.pass_conditions = scene_data["pass_conditions"]

    parent.add_child(new_scene)
    tree.set_height_tree()

    print_graph_to_console(storage)
    return new_scene.name


def update_scene_in_tree(tree: SceneTree, scene_name: str, data: Dict[str, Any]) -> bool:
    """
    Обновить сцену в дереве

    Args:
        tree: Дерево диалога
        scene_name: Имя сцены
        data: Данные для обновления

    Returns:
        bool: True если обновление успешно
    """
    if not tree:
        return False

    scene = tree.to_scene(scene_name)
    if not scene:
        return False

    # Обновление полей
    for key, value in data.items():
        if key == "answer_template":
            scene.answer_template = value
        elif key == "short_answer":
            if isinstance(value, str):
                scene.short_answer = value.split(' | ') if value else []
            else:
                scene.short_answer = value
        elif key == "clarifying_question":
            if isinstance(value, str):
                scene.clarifying_question = value.split(' | ') if value else []
            else:
                scene.clarifying_question = value
        elif key == "available_intents_list":
            scene.available_intents_list = value if isinstance(value, list) else []
        elif key == "pass_conditions":
            scene.pass_conditions = value if isinstance(value, list) else []
        elif key == "name":
            scene.name = value
        elif key == "questions":
            scene.questions = value if isinstance(value, list) else []
        elif key == "answer":
            if isinstance(value, str):
                scene.answer = value.split(' | ') if value else []
            else:
                scene.answer = value

    return True


# app/dialog.py - добавьте новую функцию

def check_graph_storage(storage: Storage) -> Dict[str, Any]:
    """
    Проверка состояния графа в storage для отладки
    """
    result = {
        "has_graph": False,
        "graph_source": None,
        "nodes_count": 0,
        "sample_nodes": [],
        "term_nodes": []
    }

    graph = get_graph_from_storage(storage)

    if graph is None:
        print("[DEBUG] Граф не найден")
        return result

    if hasattr(storage, 'graph_index'):
        result["graph_source"] = "graph_index"
    elif hasattr(storage, 'graph'):
        result["graph_source"] = "graph"
    elif hasattr(storage, 'get_graph'):
        result["graph_source"] = "get_graph()"

    result["has_graph"] = True

    try:
        all_nodes = graph.get_all_nodes()
        if all_nodes:
            result["nodes_count"] = len(all_nodes)
            result["sample_nodes"] = list(all_nodes.keys())[:10]

            # Находим TERM узлы
            for node, data in all_nodes.items():
                if data.get('type') and data['type'][0] == 'TERM':
                    result["term_nodes"].append(node)

            print(f"[DEBUG] Проверка графа:")
            print(f"[DEBUG]   Источник: {result['graph_source']}")
            print(f"[DEBUG]   Всего узлов: {result['nodes_count']}")
            print(f"[DEBUG]   TERM узлов: {len(result['term_nodes'])}")
            print(f"[DEBUG]   Примеры TERM узлов: {result['term_nodes'][:5]}")
    except Exception as e:
        print(f"[DEBUG] Ошибка при проверке графа: {e}")

    return result

def get_graph_from_storage(storage: Storage):
    if hasattr(storage, 'graph_index'):
        return storage.graph_index
    elif hasattr(storage, 'graph'):
        return storage.graph
    elif hasattr(storage, 'get_graph'):
        return storage.get_graph()
    else:
        print("[WARNING] Граф не найден в storage")
        return None


def get_graph_from_storage(storage: Storage):
    """
    Универсальная функция для получения графа из storage
    """
    print(f"[DEBUG] Тип storage: {type(storage)}")
    print(f"[DEBUG] Атрибуты storage: {[attr for attr in dir(storage) if not attr.startswith('_')]}")

    if hasattr(storage, 'graph_index'):
        print("[DEBUG] Найден graph_index")
        return storage.graph_index
    elif hasattr(storage, 'graph'):
        print("[DEBUG] Найден graph")
        return storage.graph
    elif hasattr(storage, 'get_graph'):
        print("[DEBUG] Найден get_graph()")
        return storage.get_graph()
    else:
        print("[WARNING] Граф не найден в storage")
        return None


def print_graph_to_console(storage: Storage):
    """Вывод графа в консоль с отображением связей in/out"""
    print("\n" + "=" * 80)
    print("📊 ГРАФ ЗНАНИЙ (связи in/out)")
    print("=" * 80)

    try:
        graph = get_graph_from_storage(storage)
        if graph is None:
            print("❌ Граф не найден")
            return

        all_nodes = graph.get_all_nodes()

        if not all_nodes:
            print("❌ Граф пуст")
            return

        print(f"📈 Всего узлов: {len(all_nodes)}")
        print("-" * 80)

        # Сортируем узлы для удобства
        sorted_nodes = sorted(all_nodes.items())

        # Выводим все узлы с их связями
        for node_id, node_data in sorted_nodes:
            print(f"\n🔹 {node_id}")
            print(f"   Тип: {node_data.get('type', [])}")

            # Документы
            docs = node_data.get('documents', {})
            if docs:
                doc_names = []
                for doc_id, doc_refs in docs.items():
                    if isinstance(doc_refs, list):
                        doc_names.append(f"{doc_id} ({len(doc_refs)} ссылок)")
                    else:
                        doc_names.append(str(doc_id))
                print(f"   Документы: {', '.join(doc_names)}")

            # Вывод связей IN
            if 'in' in node_data and node_data['in']:
                print(f"   📥 IN:")
                for rel_key, rel_values in node_data['in'].items():
                    if isinstance(rel_values, list):
                        if rel_key == 'link':
                            print(f"      🔗 link: {', '.join(rel_values[:5])}{'...' if len(rel_values) > 5 else ''}")
                        else:
                            print(f"      {rel_key}: {', '.join(str(v) for v in rel_values[:5])}{'...' if len(rel_values) > 5 else ''}")
                    else:
                        print(f"      {rel_key}: {rel_values}")

            # Вывод связей OUT
            if 'out' in node_data and node_data['out']:
                print(f"   📤 OUT:")
                for rel_key, rel_values in node_data['out'].items():
                    if isinstance(rel_values, list):
                        if rel_key == 'link':
                            print(f"      🔗 link: {', '.join(rel_values[:5])}{'...' if len(rel_values) > 5 else ''}")
                        else:
                            print(f"      {rel_key}: {', '.join(str(v) for v in rel_values[:5])}{'...' if len(rel_values) > 5 else ''}")
                    else:
                        print(f"      {rel_key}: {rel_values}")

            # Если нет связей
            if 'in' not in node_data or not node_data.get('in', {}):
                if 'out' not in node_data or not node_data.get('out', {}):
                    print("   (нет связей)")

        print("\n" + "=" * 80)
        print("✅ Вывод графа завершен")
        print("=" * 80 + "\n")

    except Exception as e:
        print(f"❌ Ошибка при выводе графа: {e}")
        import traceback
        traceback.print_exc()


def create_simple_dialog_tree() -> SceneTree:
    root = Scene(
        name="root",
        answer=["Здравствуйте! Я могу помочь с вопросами по травматологии и ортопедии."],
        questions=[],
        available_intents_list=[]
    )

    scene_hip_fracture = Scene(
        name="перелом_шейки_бедра",
        pass_conditions=[
            ["перелом", "шейка", "бедренный"],
            ["перелом", "шейка", "бедро"],
            ["перелом", "проксимальный", "отдел"]
        ],
        answer_template="""



📍 **ЛОКАЛИЗАЦИЯ**
{перелом шейка бедро}

🔬 **ТИПЫ ПЕРЕЛОМОВ**
{перелом:list}

🏥 **МЕТОДЫ ЛЕЧЕНИЯ**
{лечение больных:list}

👨‍⚕️ **СПЕЦИАЛИСТЫ**
{врач травматолог-ортопеды}

💊 **ПРОФИЛАКТИКА ОСЛОЖНЕНИЙ**
{профилактика венозный тромбоэмболических осложнение}

📋 **КЛИНИЧЕСКИЕ РЕКОМЕНДАЦИИ**
{клинический рекомендация:list}

📄 **НАЦИОНАЛЬНЫЕ СТАНДАРТЫ**
{национальный стандарт:list}

═══════════════════════════════════════════════════════════════════
Источник: Клинические рекомендации по лечению переломов 
проксимального отдела бедренной кости.
""",
        short_answer=[
            "Перелом шейки бедра - серьезная травма. Лечение зависит от типа перелома и состояния пациента."
        ],
        questions=[
            [IntentTemplate("перелом"), IntentTemplate("шейка"), IntentTemplate("бедренный")],
            [IntentTemplate("перелом"), IntentTemplate("шейка"), IntentTemplate("бедро")],
            [IntentTemplate("перелом"), IntentTemplate("проксимальный"), IntentTemplate("отдел")]
        ],
        clarifying_question=[
            "Уточните, что именно вас интересует: классификация переломов, методы лечения, осложнения или профилактика?"
        ],
        available_intents_list=[
            "перелом шейка",
            "перелом шейка бедро",
            "шейка",
            "бедро",
            "перелом"
        ]
    )
    root.add_child(scene_hip_fracture)

    scene_treatment = Scene(
        name="лечение_переломов",
        pass_conditions=[
            ["лечение", "перелом"]
        ],
        answer_template="""
**МЕТОДЫ ЛЕЧЕНИЯ ПЕРЕЛОМОВ**

{лечение:list}

{лечение больных:list}

{оперативный лечение:list}

{консервативный лечение:list}
""",
        short_answer=[
            "Лечение переломов может быть консервативным или оперативным."
        ],
        questions=[
            [IntentTemplate("лечение"), IntentTemplate("перелом")]
        ],
        clarifying_question=[
            "Уточните, какой метод лечения вас интересует?"
        ],
        available_intents_list=["лечение", "перелом"]
    )
    root.add_child(scene_treatment)

    tree = SceneTree(root)
    tree.set_height_tree()
    return tree

def create_fracture_dialog_tree() -> SceneTree:
    """
    Дерево диалога о переломах с иерархией родитель-дочерние сцены
    """
    root = Scene(name="root")

    # ========================================================================
    # РАЗДЕЛ 1: ОПРЕДЕЛЕНИЯ (родитель - scene_definitions)
    # ========================================================================

    scene_definitions = Scene(
        name="определения",
        answer_template="Раздел определений. Выберите тип перелома или термин.",
        available_intents_list=["определение", "что такое"]
    )
    root.add_child(scene_definitions)

    scene_what_shbk = Scene(
        name="что_такое_шбк",
        pass_conditions=[["шбк"], ["перелом", "шейка", "бедро"]],
        answer_template="ШБК — перелом шейки бедренной кости, внутрисуставный перелом, чаще у пожилых.",
        available_intents_list=["шбк", "шейка", "бедро"]
    )
    scene_definitions.add_child(scene_what_shbk)

    scene_what_ppobk = Scene(
        name="что_такое_ппобк",
        pass_conditions=[["ппобк"], ["перелом", "проксимальный"]],
        answer_template="ППОБК — перелом проксимального отдела бедренной кости (шейка, вертельная область, головка).",
        available_intents_list=["ппобк", "проксимальный"]
    )
    scene_definitions.add_child(scene_what_ppobk)

    scene_what_intraarticular = Scene(
        name="что_такое_внутрисуставный",
        pass_conditions=[["внутрисуставный", "перелом"]],
        answer_template="Внутрисуставный перелом — перелом, проходящий внутри сустава, затрагивает суставную поверхность.",
        available_intents_list=["внутрисуставный"]
    )
    scene_definitions.add_child(scene_what_intraarticular)

    scene_what_extraarticular = Scene(
        name="что_такое_внесуставный",
        pass_conditions=[["внесуставной", "перелом"], ["внекапсульный", "перелом"]],
        answer_template="Внесуставной перелом — перелом за пределами сустава, не затрагивает суставную поверхность.",
        available_intents_list=["внесуставной", "внекапсульный"]
    )
    scene_definitions.add_child(scene_what_extraarticular)

    scene_what_trochanteric = Scene(
        name="что_такое_вертельный",
        pass_conditions=[["вертельный", "перелом"], ["чрезвертельный", "перелом"]],
        answer_template="Вертельный перелом — внесуставной перелом в области вертелов бедренной кости.",
        available_intents_list=["вертельный", "чрезвертельный"]
    )
    scene_definitions.add_child(scene_what_trochanteric)

    scene_what_head = Scene(
        name="что_такое_перелом_головки",
        pass_conditions=[["перелом", "головка", "бедро"]],
        answer_template="Перелом головки бедренной кости — внутрисуставный перелом, требует восстановления суставной поверхности.",
        available_intents_list=["головка", "бк"]
    )
    scene_definitions.add_child(scene_what_head)

    scene_what_osteosynthesis = Scene(
        name="что_такое_остеосинтез",
        pass_conditions=[["остеосинтез"]],
        answer_template="Остеосинтез — соединение отломков кости металлическими конструкциями.",
        available_intents_list=["остеосинтез"]
    )
    scene_definitions.add_child(scene_what_osteosynthesis)

    scene_what_endoprosthetics = Scene(
        name="что_такое_эндопротезирование",
        pass_conditions=[["эндопротезирование"], ["замена", "сустав"]],
        answer_template="Эндопротезирование — замена поврежденного сустава на искусственный имплант.",
        available_intents_list=["эндопротезирование"]
    )
    scene_definitions.add_child(scene_what_endoprosthetics)

    scene_what_regional_anesthesia = Scene(
        name="что_такое_регионарная_анестезия",
        pass_conditions=[["регионарная", "анестезия"]],
        answer_template="Регионарная анестезия — обезболивание определенной области без отключения сознания.",
        available_intents_list=["регионарная", "анестезия"]
    )
    scene_definitions.add_child(scene_what_regional_anesthesia)

    scene_what_vte = Scene(
        name="что_такое_втэо",
        pass_conditions=[["втэо"], ["венозный", "тромбоэмболических"]],
        answer_template="ВТЭО — венозные тромбоэмболические осложнения (тромбоз глубоких вен, ТЭЛА).",
        available_intents_list=["втэо", "тромбоэмболических"]
    )
    scene_definitions.add_child(scene_what_vte)

    scene_what_perioperative = Scene(
        name="что_такое_периоперационное_ведение",
        pass_conditions=[["периоперационное", "ведение"]],
        answer_template="Периоперационное ведение — подготовка к операции, анестезия, обезболивание, профилактика осложнений.",
        available_intents_list=["периоперационное"]
    )
    scene_definitions.add_child(scene_what_perioperative)

    # ========================================================================
    # РАЗДЕЛ 2: КЛАССИФИКАЦИЯ (родитель - scene_classification)
    # ========================================================================

    scene_classification = Scene(
        name="классификация",
        answer_template="Раздел классификации переломов бедра.",
        available_intents_list=["классификация", "виды", "типы"]
    )
    root.add_child(scene_classification)

    scene_types_fractures = Scene(
        name="виды_переломов",
        pass_conditions=[["виды", "перелом", "проксимальный"], ["типы", "перелом", "бедро"]],
        answer_template="Переломы проксимального отдела: шейки (внутрисуставный), вертельной области (внесуставной), головки.",
        available_intents_list=["виды", "типы"]
    )
    scene_classification.add_child(scene_types_fractures)

    scene_diff_intra_extra = Scene(
        name="отличие_внутри_от_вне",
        pass_conditions=[["внутрисуставный", "отличие", "внесуставной"]],
        answer_template="Внутрисуставный перелом проходит внутри сустава, внесуставной — за его пределами.",
        available_intents_list=["внутрисуставный", "внесуставной"]
    )
    scene_classification.add_child(scene_diff_intra_extra)

    scene_intraarticular_types = Scene(
        name="внутрисуставные_переломы",
        pass_conditions=[["внутрисуставный", "перелом", "какие"], ["какие", "внутрисуставные"]],
        answer_template="К внутрисуставным относятся переломы шейки бедра и головки бедренной кости.",
        available_intents_list=["внутрисуставный"]
    )
    scene_classification.add_child(scene_intraarticular_types)

    scene_extraarticular_types = Scene(
        name="внесуставные_переломы",
        pass_conditions=[["внесуставной", "перелом", "какие"], ["какие", "внесуставные"]],
        answer_template="К внесуставным относятся переломы вертельной области (чрезвертельные, подвертельные).",
        available_intents_list=["внесуставной", "вертельный"]
    )
    scene_classification.add_child(scene_extraarticular_types)

    # ========================================================================
    # РАЗДЕЛ 3: ЛЕЧЕНИЕ (родитель - scene_treatment)
    # ========================================================================

    scene_treatment = Scene(
        name="лечение",
        answer_template="Раздел лечения переломов бедра.",
        available_intents_list=["лечение", "лечить"]
    )
    root.add_child(scene_treatment)

    scene_treatment_shbk = Scene(
        name="методы_лечения_шбк",
        pass_conditions=[["лечение", "шбк"], ["лечить", "шейка"]],
        answer_template="Лечение ШБК: консервативное (без операции) или хирургическое (остеосинтез, эндопротезирование).",
        available_intents_list=["шбк"]
    )
    scene_treatment.add_child(scene_treatment_shbk)

    scene_treatment_intra = Scene(
        name="лечение_внутрисуставных",
        pass_conditions=[["внутрисуставный", "лечить"], ["внутрисуставный", "лечение"]],
        answer_template="Внутрисуставные переломы чаще лечат хирургически для восстановления суставной поверхности.",
        available_intents_list=["внутрисуставный"]
    )
    scene_treatment.add_child(scene_treatment_intra)

    scene_treatment_extra = Scene(
        name="лечение_внесуставных",
        pass_conditions=[["внесуставной", "лечить"], ["внесуставной", "лечение"]],
        answer_template="Внесуставные переломы могут лечиться консервативно или остеосинтезом.",
        available_intents_list=["внесуставной"]
    )
    scene_treatment.add_child(scene_treatment_extra)

    scene_conservative = Scene(
        name="консервативное_лечение",
        pass_conditions=[["консервативный", "лечение"]],
        answer_template="Консервативное лечение — без операции: постельный режим, обезболивание, иммобилизация.",
        available_intents_list=["консервативный"]
    )
    scene_treatment.add_child(scene_conservative)

    scene_surgical = Scene(
        name="хирургическое_лечение",
        pass_conditions=[["хирургический", "лечение"], ["операция", "перелом"]],
        answer_template="Хирургическое лечение: остеосинтез (фиксация) или эндопротезирование (замена сустава).",
        available_intents_list=["хирургический", "операция"]
    )
    scene_treatment.add_child(scene_surgical)

    scene_comparison_osteo_endoprost = Scene(
        name="сравнение_остеосинтеза_и_эндопротезирования",
        pass_conditions=[["остеосинтез", "эндопротезирование", "сравнение"]],
        answer_template="Остеосинтез сохраняет свой сустав, но риск несращения. Эндопротезирование надежнее у пожилых.",
        available_intents_list=["остеосинтез", "эндопротезирование"]
    )
    scene_treatment.add_child(scene_comparison_osteo_endoprost)

    # ========================================================================
    # РАЗДЕЛ 4: ПЕРИОПЕРАЦИОННЫЙ ПЕРИОД (родитель - scene_perioperative)
    # ========================================================================

    scene_perioperative = Scene(
        name="периоперационный_период",
        answer_template="Раздел периоперационного ведения.",
        available_intents_list=["периоперационный", "периоперационное"]
    )
    root.add_child(scene_perioperative)

    scene_preoperative = Scene(
        name="предоперационная_подготовка",
        pass_conditions=[["подготовка", "операция"], ["предоперационный"]],
        answer_template="Предоперационная подготовка: обследование, коррекция болезней, профилактика тромбозов.",
        available_intents_list=["подготовка", "предоперационный"]
    )
    scene_perioperative.add_child(scene_preoperative)

    scene_intraoperative = Scene(
        name="интраоперационный_период",
        pass_conditions=[["интраоперационный"], ["во время", "операции"]],
        answer_template="Интраоперационный период — проведение операции, выбор анестезии, контроль кровопотери.",
        available_intents_list=["интраоперационный"]
    )
    scene_perioperative.add_child(scene_intraoperative)

    scene_postoperative = Scene(
        name="послеоперационное_ведение",
        pass_conditions=[["послеоперационный"], ["после", "операции"]],
        answer_template="Послеоперационное ведение: обезболивание, ранняя активизация, профилактика осложнений.",
        available_intents_list=["послеоперационный"]
    )
    scene_perioperative.add_child(scene_postoperative)

    # ========================================================================
    # РАЗДЕЛ 5: АНЕСТЕЗИЯ (родитель - scene_anesthesia)
    # ========================================================================

    scene_anesthesia = Scene(
        name="анестезия",
        answer_template="Раздел анестезии при переломах.",
        available_intents_list=["анестезия", "обезболивание"]
    )
    root.add_child(scene_anesthesia)

    scene_regional_anesthesia = Scene(
        name="регионарная_анестезия_подробно",
        pass_conditions=[["регионарная", "анестезия", "зачем"], ["регионарная", "анестезия", "что"]],
        answer_template="Регионарная анестезия — обезболивание во время операции и в раннем послеоперационном периоде.",
        available_intents_list=["регионарная"]
    )
    scene_anesthesia.add_child(scene_regional_anesthesia)

    scene_anesthesia_thrombosis = Scene(
        name="анестезия_и_тромбозы",
        pass_conditions=[["регионарная", "влияет", "тромбоз"], ["анестезия", "втэо"]],
        answer_template="Регионарная анестезия снижает риск тромбозов за счет улучшения кровотока и ранней активизации.",
        available_intents_list=["регионарная", "тромбоз"]
    )
    scene_anesthesia.add_child(scene_anesthesia_thrombosis)

    # ========================================================================
    # РАЗДЕЛ 6: ОСЛОЖНЕНИЯ И ПРОФИЛАКТИКА (родитель - scene_complications)
    # ========================================================================

    scene_complications = Scene(
        name="осложнения",
        answer_template="Раздел осложнений и их профилактики.",
        available_intents_list=["осложнение", "риск"]
    )
    root.add_child(scene_complications)

    scene_complications_list = Scene(
        name="осложнения_шбк",
        pass_conditions=[["осложнение", "шбк"], ["осложнение", "шейка"]],
        answer_template="Осложнения ШБК: тромбозы, инфекции, несращение, аваскулярный некроз головки, летальность.",
        available_intents_list=["шбк", "осложнение"]
    )
    scene_complications.add_child(scene_complications_list)

    scene_vte = Scene(
        name="втэо_подробно",
        pass_conditions=[["втэо", "что"], ["тромбоэмболических", "осложнение"]],
        answer_template="ВТЭО — тромбоз глубоких вен и тромбоэмболия легочной артерии. Частое осложнение при переломах.",
        available_intents_list=["втэо", "тромбоэмболических"]
    )
    scene_complications.add_child(scene_vte)

    scene_vte_risk = Scene(
        name="риск_втэо",
        pass_conditions=[["риск", "втэо"], ["риск", "тромбоз", "перелом"]],
        answer_template="Риск ВТЭО высокий у пожилых, при задержке операции, ожирении, онкологии.",
        available_intents_list=["риск", "втэо"]
    )
    scene_complications.add_child(scene_vte_risk)

    scene_prevention_med = Scene(
        name="медикаментозная_профилактика",
        pass_conditions=[["медикаментозный", "профилактика"], ["препараты", "профилактика"]],
        answer_template="Медикаментозная профилактика ВТЭО — антикоагулянты (гепарины, ривароксабан).",
        available_intents_list=["медикаментозный", "препараты"]
    )
    scene_complications.add_child(scene_prevention_med)

    scene_prevention_nonmed = Scene(
        name="немедикаментозная_профилактика",
        pass_conditions=[["немедикаментозный", "профилактика"], ["компрессионный", "трикотаж"]],
        answer_template="Немедикаментозная профилактика — ранняя активизация, эластичные бинты, пневмокомпрессия.",
        available_intents_list=["немедикаментозный", "компрессия"]
    )
    scene_complications.add_child(scene_prevention_nonmed)

    scene_anticoagulants_duration = Scene(
        name="длительность_антикоагулянтов",
        pass_conditions=[["антикоагулянты", "долго"], ["сколько", "антикоагулянты"]],
        answer_template="Антикоагулянты назначают на 4-6 недель после операции, по показаниям — дольше.",
        available_intents_list=["антикоагулянты", "длительность"]
    )
    scene_complications.add_child(scene_anticoagulants_duration)

    scene_anticoagulants_drugs = Scene(
        name="препараты_антикоагулянты",
        pass_conditions=[["препараты", "антикоагулянты"], ["какие", "антикоагулянты"]],
        answer_template="Антикоагулянты: низкомолекулярные гепарины (эноксапарин), прямые ингибиторы (ривароксабан).",
        available_intents_list=["препараты", "антикоагулянты"]
    )
    scene_complications.add_child(scene_anticoagulants_drugs)

    # ========================================================================
    # РАЗДЕЛ 7: НОРМАТИВНЫЕ ДОКУМЕНТЫ (родитель - scene_regulatory)
    # ========================================================================

    scene_regulatory = Scene(
        name="нормативные_документы",
        answer_template="Раздел нормативных документов.",
        available_intents_list=["стандарт", "рекомендация", "гост"]
    )
    root.add_child(scene_regulatory)

    scene_standards_rf = Scene(
        name="национальные_стандарты",
        pass_conditions=[["национальный", "стандарт"], ["гост", "перелом"]],
        answer_template="В РФ действуют национальные стандарты (ГОСТ) по лечению переломов.",
        available_intents_list=["стандарт", "гост"]
    )
    scene_regulatory.add_child(scene_standards_rf)

    scene_guidelines_rf = Scene(
        name="клинические_рекомендации",
        pass_conditions=[["клинический", "рекомендация", "россия"], ["рекомендация", "шбк"]],
        answer_template="В России действуют клинические рекомендации Минздрава по лечению переломов проксимального отдела.",
        available_intents_list=["клинический", "рекомендация"]
    )
    scene_regulatory.add_child(scene_guidelines_rf)

    # ========================================================================
    # РАЗДЕЛ 8: ВОПРОСЫ НА РАССУЖДЕНИЕ (родитель - scene_analytics)
    # ========================================================================

    scene_analytics = Scene(
        name="аналитика",
        answer_template="Раздел аналитических вопросов.",
        available_intents_list=["анализ", "сравнение", "зависимость"]
    )
    root.add_child(scene_analytics)

    scene_diff_treatment = Scene(
        name="отличие_лечения_внутри_вне",
        pass_conditions=[["внутрисуставный", "отличие", "внесуставной", "лечение"]],
        answer_template="Внутрисуставные переломы чаще оперируют. Внесуставные могут лечить консервативно или остеосинтезом.",
        available_intents_list=["внутрисуставный", "внесуставной"]
    )
    scene_analytics.add_child(scene_diff_treatment)

    scene_perioperative_vte = Scene(
        name="периоперационное_и_втэо",
        pass_conditions=[["периоперационное", "связь", "втэо"]],
        answer_template="Периоперационное ведение включает профилактику ВТЭО: антикоагулянты, компрессия, ранняя активизация.",
        available_intents_list=["периоперационное", "втэо"]
    )
    scene_analytics.add_child(scene_perioperative_vte)

    scene_factors_choice = Scene(
        name="факторы_выбора_лечения",
        pass_conditions=[["фактор", "выбор", "метод"], ["возраст", "тип", "перелом"]],
        answer_template="Выбор метода зависит от возраста, типа перелома, срока травмы и общего состояния.",
        available_intents_list=["фактор", "возраст", "тип"]
    )
    scene_analytics.add_child(scene_factors_choice)

    scene_outcome_factors = Scene(
        name="возраст_или_профилактика",
        pass_conditions=[["возраст", "профилактика", "прогноз"]],
        answer_template="И возраст, и профилактика важны. Возраст определяет исход, профилактика снижает осложнения.",
        available_intents_list=["возраст", "профилактика"]
    )
    scene_analytics.add_child(scene_outcome_factors)

    scene_anesthesia_vte_effect = Scene(
        name="анестезия_снижает_втэо",
        pass_conditions=[["регионарная", "снижает", "втэо"]],
        answer_template="Да, регионарная анестезия снижает частоту ВТЭО благодаря улучшению венозного оттока.",
        available_intents_list=["регионарная", "втэо"]
    )
    scene_analytics.add_child(scene_anesthesia_vte_effect)

    scene_unified_protocol = Scene(
        name="отсутствие_единого_протокола",
        pass_conditions=[["единый", "протокол", "отсутствует"]],
        answer_template="Единый протокол отсутствует из-за разнообразия переломов, возраста пациентов и доступных методов.",
        available_intents_list=["протокол", "отсутствует"]
    )
    scene_analytics.add_child(scene_unified_protocol)

    # ========================================================================
    # РАЗДЕЛ 9: ПАЦИЕНТЫ (родитель - scene_patients)
    # ========================================================================

    scene_patients = Scene(
        name="пациенты",
        answer_template="Раздел о пациентах с переломами.",
        available_intents_list=["пациент", "больной"]
    )
    root.add_child(scene_patients)

    scene_risk_groups = Scene(
        name="группы_риска",
        pass_conditions=[["кто", "болеет"], ["риск", "перелом"], ["группа", "риск"]],
        answer_template="Переломы чаще у пожилых (старше 60), с остеопорозом, сопутствующими болезнями.",
        available_intents_list=["риск", "пожилой"]
    )
    scene_patients.add_child(scene_risk_groups)

    scene_mortality = Scene(
        name="смертность_после_перелома",
        pass_conditions=[["смертность", "перелом"], ["исход", "перелом"]],
        answer_template="Смертность после перелома бедра выше у пожилых, зависит от сопутствующих болезней и осложнений.",
        available_intents_list=["смертность", "исход"]
    )
    scene_patients.add_child(scene_mortality)

    # ========================================================================
    # СБОРКА ДЕРЕВА
    # ========================================================================

    tree = SceneTree(root)
    tree.set_height_tree()
    return tree