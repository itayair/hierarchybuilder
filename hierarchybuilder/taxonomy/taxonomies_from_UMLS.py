import hierarchybuilder.utils as ut
import hierarchybuilder.DAG.NounPhraseObject as NounPhrase
import hierarchybuilder.DAG.DAG_utils as DAG_utils
import hierarchybuilder.combine_spans.utils as combine_spans_utils
import requests
from hierarchybuilder.topic_clustering import utils_clustering
import json


def create_dict_RB_to_objects_lst(dict_RB_to_objects, np_object, visited, relation_type='RB'):
    if np_object in visited:
        return
    visited.add(np_object)
    try:
        post_data = json.dumps(list(np_object.span_lst))
        dict_response = requests.post('http://127.0.0.1:5000/get_broader_terms/',
                                      params={"terms": post_data, "relation_type": relation_type},
                                      timeout=3)
        output = dict_response.json()
        broader_terms = output['broader_terms']
        broader_terms_set = set()
        for term in broader_terms:
            broader_terms_set.update(term)
        for term in broader_terms_set:
            dict_RB_to_objects[term] = dict_RB_to_objects.get(term, set())
            dict_RB_to_objects[term].add(np_object)
    except Exception as e:
        print(e)
        print(np_object.span_lst)
    for child in np_object.children:
        create_dict_RB_to_objects_lst(dict_RB_to_objects, child, visited)


def is_parent_in_lst(np_object, object_lst, visited=set()):
    visited.add(np_object)
    intersect_parents = np_object.parents.intersection(object_lst)
    if intersect_parents:
        return True
    for parent in np_object.parents:
        if parent in visited:
            continue
        is_parent_in_list = is_parent_in_lst(parent, object_lst, visited)
        if is_parent_in_list:
            return True
    return False


def initialize_span_to_object_dict(dict_span_to_object, np_object, visited):
    if np_object in visited:
        return
    for span in np_object.span_lst:
        dict_span_to_object[span] = np_object
    visited.add(np_object)
    for child in np_object.children:
        initialize_span_to_object_dict(dict_span_to_object, child, visited)


def update_parents_with_new_labels(node, label_lst, visited=set()):
    for parent in node.parents:
        if parent in visited:
            continue
        visited.add(parent)
        parent.label_lst.update(label_lst)
        update_parents_with_new_labels(parent, label_lst, visited)


def link_np_object_to_RB_related_nodes(np_object, object_lst, added_edges, added_taxonomic_relation,
                                       covered_labels_by_new_topics):
    for np_object_NT in object_lst:
        if np_object_NT == np_object:
            continue
        node_ancestors = set()
        combine_spans_utils.get_all_ancestors(np_object, node_ancestors)
        if np_object_NT in node_ancestors:
            continue
        NT_node_ancestors = set()
        combine_spans_utils.get_all_ancestors(np_object_NT, NT_node_ancestors)
        if np_object in NT_node_ancestors:
            continue
        added_edges.append(np_object_NT)
        added_taxonomic_relation.add(np_object_NT)
        covered_labels_by_new_topics.update(np_object_NT.label_lst)
        np_object.add_children([np_object_NT])
        np_object_NT.parents.add(np_object)
    update_parents_with_new_labels(np_object, np_object.label_lst)


def filter_duplicate_relation(dict_RB_to_objects):
    keys_lst = list(dict_RB_to_objects.keys())
    black_lst = set()
    dict_span_to_equivalent = {}
    for idx, key in enumerate(keys_lst):
        if key in black_lst:
            continue
        for idx_ref in range(idx + 1, len(keys_lst)):
            key_ref = keys_lst[idx_ref]
            if key_ref in black_lst:
                continue
            object_lst = dict_RB_to_objects[key]
            object_lst_ref = dict_RB_to_objects[key_ref]
            if 0.67 * len(object_lst) > len(object_lst_ref):
                break
            intersect_lst = object_lst.intersection(object_lst_ref)
            if len(object_lst) != len(intersect_lst):
                continue
            black_lst.add(key_ref)
            dict_span_to_equivalent[key] = dict_span_to_equivalent.get(key, set())
            dict_span_to_equivalent[key].add(key_ref)

    dict_RB_to_objects = {key: dict_RB_to_objects[key] for key in dict_RB_to_objects if
                          key not in black_lst}
    return dict_RB_to_objects, dict_span_to_equivalent


def initialize_taxonomic_relations(topic_objects):
    dict_RB_to_objects = {}
    # Detect spans with broader term in UMLS
    visited = set()
    for np_object in topic_objects:
        create_dict_RB_to_objects_lst(dict_RB_to_objects, np_object, visited)
    dict_RB_to_objects = {k: v for k, v in
                          sorted(dict_RB_to_objects.items(), key=lambda item: len(item[1]),
                                 reverse=True)}
    # Filter objects that their parents expressed by the new taxonomic relations
    for key, object_lst in dict_RB_to_objects.items():
        remove_lst = set()
        for np_object in object_lst:
            is_parent_in_list = is_parent_in_lst(np_object, object_lst)
            if is_parent_in_list:
                remove_lst.add(np_object)
        for np_object in remove_lst:
            object_lst.remove(np_object)
    dict_RB_to_objects = {k: v for k, v in
                          sorted(dict_RB_to_objects.items(), key=lambda item: len(item[1]),
                                 reverse=True)}
    dict_RB_to_objects = {key: dict_RB_to_objects[key] for key in dict_RB_to_objects if
                          len(dict_RB_to_objects[key]) > 1}
    # Filter duplicate relation
    dict_RB_to_objects, dict_span_to_equivalent = filter_duplicate_relation(dict_RB_to_objects)
    return dict_RB_to_objects, dict_span_to_equivalent


def detect_and_update_existing_object_represent_taxonomic_relation(dict_RB_to_objects,
                                                                   dict_span_to_equivalent, dict_span_to_object):
    entries_already_counted = set()
    dict_RB_exist_objects = {}
    for RB, object_lst in dict_RB_to_objects.items():
        if RB in dict_span_to_object:
            dict_RB_exist_objects[RB] = dict_span_to_object[RB]
            entries_already_counted.add(RB)
            continue
        equivalent_span_lst = dict_span_to_equivalent.get(RB, set())
        for equivalent_span in equivalent_span_lst:
            if equivalent_span in dict_span_to_object:
                entries_already_counted.add(RB)
                dict_RB_exist_objects[RB] = dict_span_to_object[equivalent_span]
                break
    added_edges = []
    added_taxonomic_relation = set()
    covered_labels_by_new_topics = set()
    # Link exist np_object_with the new taxonomic relation to other np objects
    counter = 0
    for RB, np_object in dict_RB_exist_objects.items():
        object_lst = dict_RB_to_objects[RB]
        link_np_object_to_RB_related_nodes(np_object, object_lst, added_edges, added_taxonomic_relation,
                                           covered_labels_by_new_topics)
        counter += 1
    return dict_RB_exist_objects, added_edges, added_taxonomic_relation, covered_labels_by_new_topics


def get_most_descriptive_span(nodes_lst, span_lst):
    span_to_vector = {}
    DAG_utils.initialize_all_spans_vectors(span_lst, span_to_vector)
    max_score = 0
    best_span = ""
    max_represented_vector = None
    for span, represented_vector in span_to_vector.items():
        cos_similarity_val = 0.0
        for node in nodes_lst:
            cos_similarity_val += ut.cos(represented_vector, node.weighted_average_vector)
        if cos_similarity_val >= max_score:
            best_span = span
            max_score = cos_similarity_val
            max_represented_vector = represented_vector
    return best_span, max_represented_vector


# Create and add the new taxonomic relation to the DAG
def create_and_add_new_taxonomic_object_to_DAG(dict_RB_exist_objects, dict_RB_to_objects,
                                               dict_span_to_equivalent, dict_span_to_rank, span_to_vector):
    black_lst = set(dict_RB_exist_objects.keys())
    new_taxonomic_np_objects = set()
    for RB, object_lst in dict_RB_to_objects.items():
        if RB in black_lst:
            continue
        equivalent_span_lst = dict_span_to_equivalent.get(RB, set())
        equivalent_span_lst.add(RB)
        equivalent_span_lst = list(equivalent_span_lst)
        span_tuple_lst = []
        span, represented_vector = get_most_descriptive_span(object_lst, equivalent_span_lst)
        span_to_vector[span] = represented_vector
        span_as_doc = ut.nlp(span)
        lemma_lst = utils_clustering.from_tokens_to_lemmas(span_as_doc)
        span_tuple_lst.append((span, lemma_lst))
        dict_span_to_rank[span] = len(lemma_lst)
        label_lst = set()
        for np_object in object_lst:
            label_lst.update(np_object.label_lst)
        new_np_object = NounPhrase.NP(span_tuple_lst, label_lst)
        new_np_object.weighted_average_vector = represented_vector
        new_taxonomic_np_objects.add(new_np_object)
        new_np_object.add_children(object_lst)
        for np_object in object_lst:
            np_object.parents.add(new_np_object)
    return new_taxonomic_np_objects


def covered_by_taxonomic_relation(new_taxonomic_np_objects, added_edges, added_taxonomic_relation,
                                  covered_labels_by_new_topics):
    # Check the coverage by the new components
    for np_object in new_taxonomic_np_objects:
        added_edges.extend(np_object.children)
        added_taxonomic_relation.update(np_object.children)
        covered_labels_by_new_topics.update(np_object.label_lst)


def initialize_nodes_weighted_average_vector(nodes_lst, global_index_to_similar_longest_np):
    for node in nodes_lst:
        DAG_utils.initialize_node_weighted_vector(node)
        node.frequency = DAG_utils.get_frequency_from_labels_lst(global_index_to_similar_longest_np,
                                                                 node.label_lst)


def add_taxonomies_to_DAG_by_UMLS(topic_objects, dict_span_to_rank, dict_span_to_object, span_to_vector):
    dict_RB_to_objects, dict_span_to_equivalent = initialize_taxonomic_relations(topic_objects)
    # Find exist np objects that represent the taxonomic relation
    print("End initialization of taxonomic relations")
    dict_RB_exist_objects, added_edges, added_taxonomic_relation, covered_labels_by_new_topics = \
        detect_and_update_existing_object_represent_taxonomic_relation(dict_RB_to_objects, dict_span_to_equivalent,
                                                                       dict_span_to_object)
    ut.isCyclic(topic_objects)
    print("End detect and update existing object represent taxonomic relation")
    DAG_utils.update_symmetric_relation_in_DAG(topic_objects)
    new_taxonomic_np_objects = create_and_add_new_taxonomic_object_to_DAG(dict_RB_exist_objects,
                                                                          dict_RB_to_objects, dict_span_to_equivalent,
                                                                          dict_span_to_rank, span_to_vector)
    print("End create and add new taxonomic object to DAG")
    topic_objects.extend(new_taxonomic_np_objects)
    # covered_by_taxonomic_relation(new_taxonomic_np_objects, added_edges, added_taxonomic_relation,
    #                               covered_labels_by_new_topics)
    return new_taxonomic_np_objects
