from hierarchybuilder.combine_spans import utils as combine_spans_utils
from hierarchybuilder import utils as ut
import torch


def is_span_as_lemma_already_exist(span_as_lemmas, span_as_lemmas_lst):
    for span in span_as_lemmas_lst:
        if len(set(span)) != len(set(span_as_lemmas)):
            continue
        intersection_span = set(span).intersection(set(span_as_lemmas))
        if len(intersection_span) == len(set(span_as_lemmas)):
            return True
    return False


def nps_lst_to_string(nps_lst):
    span_lst = set()
    list_of_span_as_lemmas_lst = []
    for np in nps_lst:
        span_lst.add(np[0])
        if not is_span_as_lemma_already_exist(np[1], list_of_span_as_lemmas_lst):
            list_of_span_as_lemmas_lst.append(np[1])
    return span_lst, list_of_span_as_lemmas_lst


class NP:
    def __init__(self, np, label_lst):
        self.span_lst, self.list_of_span_as_lemmas_lst = nps_lst_to_string(np)
        self.lemma_to_occurrences_dict = {}
        self.dict_key_to_synonyms_keys = {}
        self.calculate_common_denominators_of_spans(self.list_of_span_as_lemmas_lst)
        self.common_lemmas_in_spans = []
        self.length = 0
        self.update_top_lemmas_in_spans()
        self.label_lst = set(label_lst)
        self.children = []
        self.parents = set()
        self.frequency = 0
        self.score = 0.0
        self.marginal_val = 0.0
        self.combined_nodes_lst = set()
        self.weighted_average_vector = torch.zeros(768, 1)

    def get_average_length_of_lemmas_lst(self):
        sum_length_lemma_lst = 0
        for span_as_lemmas_lst in self.list_of_span_as_lemmas_lst:
            sum_length_lemma_lst += len(span_as_lemmas_lst)
        return sum_length_lemma_lst / len(self.list_of_span_as_lemmas_lst)

    def does_lemma_lst_contain_lemma(self, lemma_lst, lemma):
        synonyms = self.dict_key_to_synonyms_keys[lemma]
        if set(lemma_lst).intersection(set(synonyms)):
            return True
        return False

    def get_all_span_as_lemma_lst_contain_common_lemma(self):
        contain_common_lemma_lst = self.list_of_span_as_lemmas_lst.copy()
        for common_lemma in self.common_lemmas_in_spans:
            synonyms = self.dict_key_to_synonyms_keys[common_lemma]
            new_contain_common_lemma_lst = []
            for span_as_lemmas_lst in contain_common_lemma_lst:
                if set(span_as_lemmas_lst).intersection(set(synonyms)):
                    new_contain_common_lemma_lst.append(span_as_lemmas_lst)
                contain_common_lemma_lst = new_contain_common_lemma_lst
        return contain_common_lemma_lst

    def get_best_match(self, average_val):
        contain_common_lemma_lst = self.get_all_span_as_lemma_lst_contain_common_lemma()
        self.lemma_to_occurrences_dict = {k: v for k, v in
                                          sorted(self.lemma_to_occurrences_dict.items(), key=lambda item: item[1],
                                                 reverse=True)}
        for lemma, occurrences in self.lemma_to_occurrences_dict.items():
            is_added = False
            if lemma in self.common_lemmas_in_spans:
                continue
            new_contain_common_lemma_lst = []
            for lemma_lst in contain_common_lemma_lst:
                if self.does_lemma_lst_contain_lemma(lemma_lst, lemma):
                    new_contain_common_lemma_lst.append(lemma_lst)
                    is_added = True
            if is_added and (len(new_contain_common_lemma_lst) > 1 or len(self.common_lemmas_in_spans) == 0):
                self.common_lemmas_in_spans.append(lemma)
                contain_common_lemma_lst = new_contain_common_lemma_lst
            if len(self.common_lemmas_in_spans) < average_val * 0.7:
                break
        self.length = len(self.common_lemmas_in_spans)

    def update_top_lemmas_in_spans(self):
        lemma_to_average_occurrences_dict = {key: value / len(self.list_of_span_as_lemmas_lst)
                                             for key, value in self.lemma_to_occurrences_dict.items()}
        self.common_lemmas_in_spans = [key for key, value in lemma_to_average_occurrences_dict.items() if
                                       value > 0.7]
        self.length = len(self.common_lemmas_in_spans)
        average_val = self.get_average_length_of_lemmas_lst()
        if self.length + 0.5 < average_val:
            self.get_best_match(average_val)
            # most_frequent_span = combine_spans_utils.get_most_frequent_span(self.span_lst)
            # self.common_lemmas_in_spans = ut.dict_span_to_lemma_lst[most_frequent_span]

    def get_lemmas_synonyms_in_keys(self, lemma):
        lemmas_keys_lst = list(self.lemma_to_occurrences_dict.keys())
        for lemma_key in lemmas_keys_lst:
            for key in self.dict_key_to_synonyms_keys[lemma_key]:
                if lemma in ut.dict_lemma_to_synonyms.get(key, []) or \
                        key in ut.dict_lemma_to_synonyms.get(lemma, []):
                    return lemma_key
            is_similar, lemma_ref = \
                combine_spans_utils.word_contained_in_list_by_edit_distance(lemma,
                                                                            self.dict_key_to_synonyms_keys[lemma_key])
            if is_similar:
                return lemma_key
        return None

    def calculate_common_denominators_of_spans(self, span_as_lemmas_lst_to_update):
        for span_as_lst in span_as_lemmas_lst_to_update:
            already_counted = set()
            for lemma in span_as_lst:
                lemma_key = self.get_lemmas_synonyms_in_keys(lemma)
                if lemma_key in already_counted:
                    continue
                if lemma_key:
                    already_counted.add(lemma_key)
                    self.lemma_to_occurrences_dict[lemma_key] += 1
                    self.dict_key_to_synonyms_keys[lemma_key].add(lemma)
                else:
                    already_counted.add(lemma)
                    self.lemma_to_occurrences_dict[lemma] = 1
                    self.dict_key_to_synonyms_keys[lemma] = set()
                    self.dict_key_to_synonyms_keys[lemma].add(lemma)

    def add_children(self, children):
        for child in children:
            if child == self:
                continue
            if child not in self.children:
                self.children.append(child)
        for child in children:
            self.label_lst.update(child.label_lst)

    def add_unique_lst(self, span_as_tokens_lst):
        new_span_lst = []
        for span_as_tokens in span_as_tokens_lst:
            is_already_exist = is_span_as_lemma_already_exist(span_as_tokens, self.list_of_span_as_lemmas_lst)
            # for span in self.list_of_span_as_lemmas_lst:
            #     if len(set(span)) != len(set(span_as_tokens)):
            #         continue
            #     intersection_span = set(span).intersection(set(span_as_tokens))
            #     if len(intersection_span) == len(span_as_tokens):
            #         is_already_exist = True
            #         break
            if not is_already_exist:
                new_span_lst.append(span_as_tokens)
        if new_span_lst:
            self.list_of_span_as_lemmas_lst.extend(new_span_lst)
            self.calculate_common_denominators_of_spans(new_span_lst)
            self.update_top_lemmas_in_spans()

    def update_parents_label(self, np_object, label_lst, visited):
        for parent_object in np_object.parents:
            if parent_object in visited:
                continue
            parent_object.label_lst.update(label_lst)
            visited.add(parent_object)
            self.update_parents_label(parent_object, label_lst, visited)

    def update_children_with_new_parent(self, children, previous_parent):
        for child in children:
            if previous_parent in child.parents:
                child.parents.remove(previous_parent)
            if child == self:
                continue
            child.parents.add(self)

    def update_parents_with_new_node(self, parents, previous_node):
        for parent in parents:
            if previous_node in parent.children:
                parent.children.remove(previous_node)
            if self == parent:
                continue
            if self not in parent.children:
                parent.children.append(self)

    def combine_nodes(self, np_object):
        self.span_lst.update(np_object.span_lst)
        self.add_unique_lst(np_object.list_of_span_as_lemmas_lst)
        # self.np.extend(np_object.np)
        self.label_lst.update(np_object.label_lst)
        self.update_parents_label(np_object, self.label_lst, set())
        self.update_parents_with_new_node(np_object.parents, np_object)
        self.update_children_with_new_parent(np_object.children, np_object)
        self.parents.update(np_object.parents)
        self.add_children(np_object.children)
        del np_object

    def __gt__(self, ob2):
        return self.marginal_val < ob2.marginal_val
