import requests
import json
from hierarchybuilder.combine_spans import utils as combine_spans_utils


def combine_nodes_by_umls_synonymous_spans_dfs_helper(topic_object_lst, dict_span_to_object, np_object, visited,
                                                      dict_object_to_global_label,
                                                      global_dict_label_to_object, span_to_vector):
    if np_object in visited:
        return
    visited.add(np_object)
    equivalent_object_lst = set()
    post_data = json.dumps(list(np_object.span_lst))
    dict_response = requests.post('http://127.0.0.1:5000/create_synonyms_dictionary/',
                                  params={"words": post_data}, timeout=3)
    output = dict_response.json()
    synonyms_dict = output['synonyms']
    synonyms = set()
    for key, synonyms_lst in synonyms_dict.items():
        synonyms.update(synonyms_lst)
    if synonyms:
        for term in synonyms:
            equivalent_np_object = dict_span_to_object.get(term, None)
            if equivalent_np_object:
                if equivalent_np_object == np_object:
                    continue
                equivalent_object_lst.add(equivalent_np_object)
        if equivalent_object_lst:
            equivalent_object_lst = [np_object] + list(equivalent_object_lst)
            combined_nodes_lst = set()
            combine_spans_utils.combine_nodes_lst(equivalent_object_lst, dict_span_to_object,
                                                  dict_object_to_global_label,
                                                  global_dict_label_to_object, topic_object_lst, combined_nodes_lst)
            for node in combined_nodes_lst:
                visited.add(node)

    children_lst = np_object.children.copy()
    for child in children_lst:
        combine_nodes_by_umls_synonymous_spans_dfs_helper(topic_object_lst, dict_span_to_object, child, visited,
                                                          dict_object_to_global_label,
                                                          global_dict_label_to_object, span_to_vector)


def combine_nodes_by_umls_synonymous_spans(dict_span_to_object, dict_object_to_global_label,
                                           global_dict_label_to_object,
                                           topic_object_lst, span_to_vector):
    visited = set()
    topic_objects = topic_object_lst.copy()
    for topic_object in topic_objects:
        if topic_object in visited:
            topic_objects.remove(topic_object)
            continue
        combine_nodes_by_umls_synonymous_spans_dfs_helper(topic_object_lst, dict_span_to_object, topic_object, visited,
                                                          dict_object_to_global_label,
                                                          global_dict_label_to_object, span_to_vector)
