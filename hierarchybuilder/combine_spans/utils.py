from hierarchybuilder import utils as ut
import nltk
from nltk.corpus import wordnet
from hierarchybuilder.DAG import DAG_utils as DAG_utils


def get_synonyms_by_word(word):
    synonyms = set()
    for syn in wordnet.synsets(word):
        for l in syn.lemmas():
            synonyms.add(l.name())
    return synonyms


def from_words_to_lemma_lst(span):
    lemmas_lst = []
    for word in span:
        lemma = ut.dict_word_to_lemma.get(word, None)
        if lemma is None:
            lemma = word
        lemmas_lst.append(lemma)
    return lemmas_lst


def word_contained_in_list_by_edit_distance(word, lst_words_ref):
    for word_ref in lst_words_ref:
        val = nltk.edit_distance(word, word_ref)
        if val / max(len(word), len(word_ref)) <= 0.25:
            return True, word_ref
    return False, None


def compare_edit_distance_of_synonyms(synonyms, token, lemma_ref):
    close_words = set()
    for synonym in synonyms:
        edit_distance = nltk.edit_distance(synonym, token)
        edit_distance_lemma = nltk.edit_distance(synonym, lemma_ref)
        if edit_distance / max(len(token), len(synonym)) <= 0.25:
            close_words.add((synonym, token))
            continue
        if edit_distance_lemma / max(len(lemma_ref), len(synonym)) <= 0.25:
            close_words.add((synonym, lemma_ref))
            continue
    return list(close_words)


def remove_token_if_in_span(token, span):
    if token in span:
        span.remove(token)
        return True
    else:
        synonyms_lst = set(ut.dict_lemma_to_synonyms.get(token, []))
        for word_lemma in span:
            if set(ut.dict_lemma_to_synonyms.get(word_lemma, [])).intersection(synonyms_lst):
                span.remove(word_lemma)
                return True
    return False


def is_similar_meaning_between_span(span_1_lemma_lst, span_2_lemma_lst):
    not_satisfied = []
    span_1_lemma_lst = span_1_lemma_lst.copy()
    span_2_lemma_lst = span_2_lemma_lst.copy()
    for lemma in span_1_lemma_lst:
        is_exist = remove_token_if_in_span(lemma, span_2_lemma_lst)
        if not is_exist:
            not_satisfied.append(lemma)
    if len(not_satisfied) > 2:
        return False
    if len(span_1_lemma_lst) == 1 and not_satisfied:
        return False
    for lemma in not_satisfied:
        is_exist, lemma_to_remove = word_contained_in_list_by_edit_distance(lemma, span_2_lemma_lst)
        if is_exist:
            span_2_lemma_lst.remove(lemma_to_remove)
            continue
        return False
    return True


def create_dicts_length_to_span_and_span_to_list(span_to_group_members):
    dict_length_to_span = {}
    for span, sub_set in span_to_group_members.items():
        span_as_lst = ut.dict_span_to_lemma_lst[span]
        dict_length_to_span[len(span_as_lst)] = dict_length_to_span.get(len(span_as_lst), [])
        dict_length_to_span[len(span_as_lst)].append((span, span_as_lst))
        ut.dict_span_to_lemma_lst[span] = span_as_lst
    return dict_length_to_span


def get_average_value(spans_lst, dict_span_to_rank):
    average_val = 0
    for span in spans_lst:
        average_val += dict_span_to_rank.get(span, 2)
    average_val = average_val / len(spans_lst)
    return int(average_val * 10)


def create_dict_lemma_word2vec_and_edit_distance():
    words_lst = list(ut.dict_word_to_lemma.keys())
    dict_lemma_to_close_words = {}
    counter = 0
    for word, lemma in ut.dict_word_to_lemma.items():
        dict_lemma_to_close_words[word] = []
        # if word not in vocab_word2vec:
        #     counter += 1
        #     continue
        for word_ref_idx in range(counter + 1, len(words_lst)):
            word_ref = words_lst[word_ref_idx]
            lemma_ref = ut.dict_word_to_lemma[word_ref]
            synonyms = [word, lemma] + ut.dict_lemma_to_synonyms[lemma]
            synonyms = list(set(synonyms))
            if lemma == lemma_ref or lemma_ref in synonyms:
                continue
            dict_lemma_to_close_words[word].extend(compare_edit_distance_of_synonyms(synonyms, word_ref, lemma_ref))
        counter += 1
    return dict_lemma_to_close_words


def get_weighted_average_vector_of_some_vectors_embeddings(spans_embeddings, common_np_lst):
    weighted_average_vector = torch.zeros(spans_embeddings[0].shape)
    for idx, embedding_vector in enumerate(spans_embeddings):
        weighted_average_vector += embedding_vector
    weighted_average_vector /= len(common_np_lst)
    return weighted_average_vector


def get_non_clustered_group_numbers(span_to_group_members, dict_label_to_longest_nps_group):
    all_group_numbers = set(dict_label_to_longest_nps_group.keys())
    already_grouped = set()
    common_span_lst = []
    for common_span, group_numbers in span_to_group_members.items():
        already_grouped.update(group_numbers)
        common_span_lst.append(common_span)
    res_group_numbers = [item for item in all_group_numbers if item not in already_grouped]
    dict_label_to_longest_np_without_common_sub_np = {}
    for num in res_group_numbers:
        dict_label_to_longest_np_without_common_sub_np[num] = dict_label_to_longest_nps_group[num]
    return dict_label_to_longest_np_without_common_sub_np, common_span_lst


def get_most_frequent_span(lst_of_spans):
    most_frequent_span_value = -1
    most_frequent_span = None
    for span in lst_of_spans:
        val = ut.dict_span_to_counter.get(span, 0)
        if val > most_frequent_span_value:
            most_frequent_span_value = val
            most_frequent_span = span
    return most_frequent_span


def convert_dict_label_to_spans_to_most_frequent_span_to_label(dict_label_to_spans_group):
    dict_span_to_label = {}
    for label, tuple_of_spans_lst in dict_label_to_spans_group.items():
        spans_lst = [tuple_of_span[0] for tuple_of_span in tuple_of_spans_lst]
        most_frequent_span = get_most_frequent_span(spans_lst)
        dict_span_to_label[most_frequent_span] = label
    return dict_span_to_label


def update_span_to_group_members_with_longest_answers_dict(span_to_group_members, dict_label_to_longest_nps_group,
                                                           dict_span_to_similar_spans):
    dict_longest_answer_to_label_temp = {}
    for label, spans_lst in dict_label_to_longest_nps_group.items():
        most_frequent_span = get_most_frequent_span(spans_lst)
        is_common_span = False
        if most_frequent_span in span_to_group_members:
            continue
        for span, label_lst in span_to_group_members.items():
            if label in label_lst:
                similar_spans_lst = dict_span_to_similar_spans[span]
                intersection_spans_lst = set(spans_lst).intersection(similar_spans_lst)
                if intersection_spans_lst:
                    dict_span_to_similar_spans[span].update(spans_lst)
                    is_common_span = True
                    break
        if not is_common_span:
            dict_longest_answer_to_label_temp[most_frequent_span] = [label]
            dict_span_to_similar_spans[most_frequent_span] = set(spans_lst)

    span_to_group_members.update(dict_longest_answer_to_label_temp)


def get_dict_spans_group_to_score(span_to_group_members, dict_span_to_rank, dict_span_to_similar_spans,
                                  dict_label_to_longest_nps_group):
    update_span_to_group_members_with_longest_answers_dict(span_to_group_members, dict_label_to_longest_nps_group,
                                                           dict_span_to_similar_spans)
    dict_score_to_collection_of_sub_groups = {}
    for key, group in span_to_group_members.items():
        average_val = get_average_value(dict_span_to_similar_spans[key], dict_span_to_rank)
        dict_score_to_collection_of_sub_groups[average_val] = dict_score_to_collection_of_sub_groups.get(
            average_val, [])
        dict_score_to_collection_of_sub_groups[average_val].append((key, set(group)))
    dict_score_to_collection_of_sub_groups = {k: v for k, v in
                                              sorted(dict_score_to_collection_of_sub_groups.items(),
                                                     key=lambda item: item[0], reverse=True)}
    for score, sub_group_lst in dict_score_to_collection_of_sub_groups.items():
        sub_group_lst.sort(key=lambda tup: len(tup[1]), reverse=True)
    return dict_score_to_collection_of_sub_groups


def get_all_ancestors(node, visited):
    visited.add(node)
    for parent in node.parents:
        if parent in visited:
            continue
        get_all_ancestors(parent, visited)


def update_all_ancestors_node_was_combined(node, label_lst, visited=set()):
    for parent in node.parents:
        if parent in visited:
            continue
        visited.add(parent)
        num_of_labels_before_update = len(parent.label_lst)
        parent.label_lst.update(label_lst)
        num_of_labels_after_update = len(parent.label_lst)
        if num_of_labels_before_update == num_of_labels_after_update:
            continue
        update_all_ancestors_node_was_combined(parent, label_lst, visited)


def get_all_descendents(node, visited):
    visited.add(node)
    for child in node.children:
        if child in visited:
            continue
        get_all_descendents(child, visited)


def has_intersection_between_desc_and_anc(node_1, node_2):
    ancestor_lst = set()
    get_all_ancestors(node_1, ancestor_lst)
    descendent_lst = set()
    get_all_descendents(node_2, descendent_lst)
    if ancestor_lst.intersection(descendent_lst):
        return True


def is_combine_create_circle(node_1, node_2):
    has_intersection = has_intersection_between_desc_and_anc(node_1, node_2)
    if has_intersection:
        return True
    has_intersection = has_intersection_between_desc_and_anc(node_2, node_1)
    if has_intersection:
        return True
    return False


def ambiguous_descendent_in_equivalent_nodes(node_1, node_2):
    children_to_remove_from_node_1 = set()
    children_to_remove_from_node_2 = set()
    for child_1 in node_1.children:
        for child_2 in node_2.children:
            if child_1 in child_2.children:
                children_to_remove_from_node_1.add(child_1)
            elif child_2 in child_1.children:
                children_to_remove_from_node_2.add(child_2)
    for child in children_to_remove_from_node_1:
        node_1.children.remove(child)
        child.parents.remove(node_1)
    for child in children_to_remove_from_node_2:
        node_2.children.remove(child)
        if node_2 in child.parents:
            child.parents.remove(node_2)


def initialize_node_weighted_vector(node, span_to_vector):
    if not node.span_lst:
        return
    is_first = True
    weighted_average_vector = None
    for np in node.span_lst:
        if is_first:
            weighted_average_vector = span_to_vector[np]
            is_first = False
        else:
            weighted_average_vector += span_to_vector[np]
    weighted_average_vector /= len(node.span_lst)
    node.weighted_average_vector = weighted_average_vector


def has_another_path_between_nodes(children, child):
    rest_children = set(children) - {child}
    all_descendents = set()
    has_another_path = False
    for rest_child in rest_children:
        get_all_descendents(rest_child, all_descendents)
        if child in all_descendents:
            has_another_path = True
            break
    return has_another_path


def combine_nodes_lst(np_object_lst, span_to_object, dict_object_to_global_label, global_dict_label_to_object,
                      topic_object_lst, combined_nodes_lst=set()):
    first_element = np_object_lst[0]
    length = len(np_object_lst)
    is_combined = False
    for i in range(1, length):
        second_element = np_object_lst[i]
        if second_element == first_element:
            raise Exception("Parent have duplicate node")
        if second_element in first_element.children:
            if has_another_path_between_nodes(first_element.children, second_element):
                continue
            remove_node_parents_edge(first_element, second_element)
            remove_children_which_already_reached(first_element, second_element)
        elif first_element in second_element.children:
            if has_another_path_between_nodes(second_element.children, first_element):
                continue
            remove_node_parents_edge(second_element, first_element)
            remove_children_which_already_reached(second_element, first_element)
            second_element = first_element
            first_element = np_object_lst[i]
        elif is_combine_create_circle(first_element, second_element):
            continue
        else:
            ambiguous_descendent_in_equivalent_nodes(first_element, second_element)
        combined_nodes_lst.add(second_element)
        first_element.combine_nodes(second_element)
        is_combined = True
        DAG_utils.update_global_dictionaries(span_to_object, global_dict_label_to_object,
                                             dict_object_to_global_label, second_element, first_element)
        if second_element in topic_object_lst:
            topic_object_lst.remove(second_element)
        # for span in second_element.span_lst:
        #     span_to_object[span] = first_element
        # global_label_lst = dict_object_to_global_label.get(hash(second_element), None)
        # if global_label_lst:
        #     dict_object_to_global_label[hash(first_element)] = \
        #         dict_object_to_global_label.get(hash(first_element), set())
        #     for global_label in global_label_lst:
        #         global_dict_label_to_object[global_label] = first_element
        #     dict_object_to_global_label[hash(first_element)].update(global_label_lst)
    if is_combined:
        update_all_ancestors_node_was_combined(first_element, first_element.label_lst)


def update_ans_with_remove_link(node, label_lst, visited=set()):
    if node in visited:
        return
    visited.add(node)
    new_label_lst = node.label_lst - label_lst
    for child in node.children:
        new_label_lst.update(child.label_lst)
    if node.label_lst == new_label_lst:
        return
    node.label_lst = new_label_lst
    for parent in node.parents:
        update_ans_with_remove_link(parent, label_lst, visited)


def remove_node_parents_edge(node, child):
    if node in child.parents:
        child.parents.remove(node)
    while child not in node.children:
        node.children.remove(child)
    # parents_remove_lst = set()
    # for parent in child.parents:
    #     if parent in node.children:
    #         parent.children.remove(child)
    #         parents_remove_lst.add(parent)
    #         update_ans_with_remove_link(parent, child.label_lst)
    # for parent in parents_remove_lst:
    #     child.parents.remove(parent)


def remove_children_which_already_reached(node, combined_node):
    descendents = set()
    get_all_descendents(node, descendents)
    remove_lst = set()
    for child in combined_node.children:
        if child in descendents:
            remove_lst.add(child)
    for child in remove_lst:
        if combined_node in child.parents:
            child.parents.remove(combined_node)
        combined_node.children.remove(child)


def combine_node_with_equivalent_children(node, equivalent_np_object_lst, span_to_object, dict_object_to_global_label,
                                          global_dict_label_to_object, topic_object_lst, span_to_vector,
                                          combined_nodes_lst=set()):
    is_combined = False
    children = set(node.children.copy())
    for child in equivalent_np_object_lst:
        has_another_path = has_another_path_between_nodes(children, child)
        if has_another_path:
            continue
        children.remove(child)
        remove_node_parents_edge(node, child)
        remove_children_which_already_reached(node, child)
        combined_nodes_lst.add(child)
        node.combine_nodes(child)
        is_combined = True
        # for span in child.span_lst:
        #     span_to_object[span] = node
        DAG_utils.update_global_dictionaries(span_to_object, global_dict_label_to_object,
                                             dict_object_to_global_label, child, node)
        if child in topic_object_lst:
            topic_object_lst.remove(child)
        # global_label_lst = dict_object_to_global_label.get(hash(child), None)
        # if global_label_lst:
        #     dict_object_to_global_label[hash(node)] = \
        #         dict_object_to_global_label.get(hash(node), set())
        #     for global_label in global_label_lst:
        #         global_dict_label_to_object[global_label] = node
        #     dict_object_to_global_label[hash(node)].update(global_label_lst)
        # del child
    if is_combined:
        update_all_ancestors_node_was_combined(node, node.label_lst)
        initialize_node_weighted_vector(node, span_to_vector)
