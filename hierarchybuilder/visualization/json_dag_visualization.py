import hierarchybuilder.DAG.DAG_utils as DAG_utils
import hierarchybuilder.utils as ut
import json
from json import JSONEncoder


def print_flat_list_to_file(concept_to_occurrences):
    concept_to_occurrences = {k: v for k, v in
                              sorted(concept_to_occurrences.items(), key=lambda item: item[1], reverse=True)}
    file_name = "flat_list_for_UI_chest_pain.txt"
    concept_lst = []
    with open(file_name, 'w', encoding='utf-8') as f:
        idx = 0
        for longest_span, number in concept_to_occurrences.items():
            concept = longest_span + ': ' + str(number)
            concept_lst.append(concept)
            concept = str(idx) + ") " + concept
            f.write(concept)
            idx += 1
            f.write('\n')
    with open('flat_list_for_UI_as_json_chest_pain.txt', 'w') as result_file:
        result_file.write(json.dumps(concept_lst))


def get_all_labels(nodes, labels, visited=set()):
    for node in nodes:
        if node in visited:
            continue
        visited.add(node)
        labels.update(node.label_lst)
        get_all_labels(node.children, labels, visited)


class json_top_k_object:
    def __init__(self, json_top_k):
        self.json_top_k = json_top_k

    # def to_json(self):
    #     to_return = self.json_top_k
    #
    #     return to_return
    def to_json(self):
        to_return = {}
        for node in self.json_top_k:
            to_return.update(node.to_json())

        return to_return


def json_dag_visualization(top_k_topics, global_index_to_similar_longest_np, taxonomic_np_objects, topic_object_lst):
    different_concepts = set()
    concept_to_occurrences = {}
    top_k_topics_as_json = DAG_utils.from_DAG_to_JSON(top_k_topics, global_index_to_similar_longest_np,
                                                      taxonomic_np_objects, different_concepts,
                                                      concept_to_occurrences)
    np_object_to_json_node = {}
    DAG_utils.from_DAG_to_json_nested_objects(top_k_topics, global_index_to_similar_longest_np,
                                              np_object_to_json_node)
    json_top_k_nodes = []
    for np_object in top_k_topics:
        json_top_k_nodes.append(np_object_to_json_node[hash(np_object)])
    json_entry_list = json.dumps(json_top_k_object(json_top_k_nodes), default=DAG_utils.default)

    # root = json_top_k_object(json_top_k_nodes)
    top_k_labels = set()
    get_all_labels(top_k_topics, top_k_labels, visited=set())
    covered_labels = DAG_utils.get_frequency_from_labels_lst(global_index_to_similar_longest_np,
                                                             top_k_labels)
    labels_of_topics = set()
    get_all_labels(topic_object_lst, labels_of_topics, visited=set())
    total_labels_of_topics = DAG_utils.get_frequency_from_labels_lst(global_index_to_similar_longest_np,
                                                                     labels_of_topics)
    print("total labels of topics:", total_labels_of_topics)
    print("Covered labels by selected nodes:", covered_labels)
    print("Done")
    return json_entry_list
