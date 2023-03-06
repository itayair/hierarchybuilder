import torch
from sklearn.cluster import AgglomerativeClustering
from hierarchybuilder.combine_spans import utils as combine_spans_utils

cos = torch.nn.CosineSimilarity(dim=0, eps=1e-08)



def combine_equivalent_nodes(np_object_lst, span_to_object, dict_object_to_global_label, global_dict_label_to_object):
    if len(np_object_lst) <= 1:
        return
    node_vector_lst = []
    for np_object in np_object_lst:
        node_vector_lst.append(np_object.weighted_average_vector)
    node_vector_lst = torch.stack(node_vector_lst).reshape(len(np_object_lst), -1)
    clustering = AgglomerativeClustering(distance_threshold=0.1, n_clusters=None, linkage="average",
                                         metric="cosine", compute_full_tree=True).fit(node_vector_lst)
    dict_cluster_to_common_spans_lst = {}
    for idx, label in enumerate(clustering.labels_):
        dict_cluster_to_common_spans_lst[label] = dict_cluster_to_common_spans_lst.get(label, [])
        dict_cluster_to_common_spans_lst[label].append(np_object_lst[idx])
    for label, equivalent_nodes in dict_cluster_to_common_spans_lst.items():
        if len(equivalent_nodes) == 1:
            continue
        combine_spans_utils.combine_nodes_lst(equivalent_nodes, span_to_object, dict_object_to_global_label,
                                              global_dict_label_to_object)


def combine_equivalent_node_with_its_equivalent_children(parent, children, span_to_object, dict_object_to_global_label,
                                                         global_dict_label_to_object, topic_object_lst, span_to_vector,
                                                         visited):
    if len(children) == 0:
        return
    equivalents_children = set()
    for child in children:
        res = cos(parent.weighted_average_vector, child.weighted_average_vector)
        if res > 0.95:
            equivalents_children.add(child)
    if equivalents_children:
        combine_spans_utils.combine_node_with_equivalent_children(parent, equivalents_children, span_to_object,
                                                                  dict_object_to_global_label,
                                                                  global_dict_label_to_object, topic_object_lst,
                                                                  span_to_vector, visited)


def combine_equivalent_parent_and_children_nodes_by_semantic_DL_model(np_object_lst, span_to_object,
                                                                      dict_object_to_global_label,
                                                                      global_dict_label_to_object,
                                                                      topic_object_lst, span_to_vector, visited=set()):
    for np_object in np_object_lst:
        if np_object in visited:
            continue
        visited.add(np_object)
        combine_equivalent_parent_and_children_nodes_by_semantic_DL_model(np_object.children, span_to_object,
                                                                          dict_object_to_global_label,
                                                                          global_dict_label_to_object,
                                                                          topic_object_lst, span_to_vector, visited)
        combine_equivalent_node_with_its_equivalent_children(np_object, np_object.children, span_to_object,
                                                             dict_object_to_global_label,
                                                             global_dict_label_to_object, topic_object_lst,
                                                             span_to_vector, visited)


def combine_equivalent_nodes_by_semantic_DL_model(np_object_lst, span_to_object, dict_object_to_global_label,
                                                  global_dict_label_to_object, span_to_vector, visited=set()):
    for np_object in np_object_lst:
        if np_object in visited:
            continue
        visited.add(np_object)
        combine_equivalent_nodes(np_object.children, span_to_object, dict_object_to_global_label,
                                 global_dict_label_to_object)
        combine_equivalent_nodes_by_semantic_DL_model(np_object.children, span_to_object, dict_object_to_global_label,
                                                      global_dict_label_to_object, span_to_vector, visited)
