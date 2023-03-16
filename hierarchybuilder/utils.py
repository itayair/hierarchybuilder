from hierarchybuilder.topic_clustering import main_clustering as main_clustering
from hierarchybuilder.expansions import parse_medical_data
import torch
import os
import sys
from transformers import AutoTokenizer, AutoModel
import statistics

cos = torch.nn.CosineSimilarity(dim=0, eps=1e-08)
nlp = parse_medical_data.nlp
device = torch.device("cpu")
# device = torch.device("cuda:1" if torch.cuda.is_available() else "cpu")
sapBert_tokenizer = AutoTokenizer.from_pretrained('cambridgeltl/SapBERT-from-PubMedBERT-fulltext')
sapBert_model = AutoModel.from_pretrained('cambridgeltl/SapBERT-from-PubMedBERT-fulltext')
model = sapBert_model
model = model.eval()

dict_span_to_lemma_lst = {}
topics_dict = {}
dict_span_to_counter = {}
dict_word_to_lemma = {}
dict_lemma_to_synonyms = {}
dict_longest_span_to_counter = {}
dict_noun_lemma_to_synonyms = {}
dict_noun_lemma_to_noun_words = {}
dict_noun_lemma_to_counter = {}
dict_noun_word_to_counter = {}
etiology = 'output'
entries_number_limit = 50
host_and_port = "127.0.0.1:5000"


def initialize_data(examples, host_val, port_val, ignore_words=None, output_file_name='', entries_number=50,
                    device_type=""):
    global topics_dict, dict_span_to_counter, dict_word_to_lemma, dict_lemma_to_synonyms, \
        dict_longest_span_to_counter, dict_noun_lemma_to_synonyms, dict_noun_lemma_to_noun_words, \
        dict_noun_lemma_to_counter, dict_noun_word_to_counter, etiology, entries_number_limit, device, model, \
        host_and_port
    host_and_port = "http://" + host_val + ":" + str(port_val)
    if device_type:
        device = device_type
        model = model.to(device)
        model = model.eval()
    entries_number_limit = entries_number
    if ignore_words is None:
        ignore_words = set('cause')
    if output_file_name:
        etiology = output_file_name
    collection_format_examples = parse_medical_data.get_examples_as_all_optional_answers_format(examples)
    topics_dict, dict_span_to_counter, dict_word_to_lemma, dict_lemma_to_synonyms, \
    dict_longest_span_to_counter, dict_noun_lemma_to_synonyms, dict_noun_lemma_to_noun_words, dict_noun_lemma_to_counter, \
    dict_noun_word_to_counter = main_clustering.convert_examples_to_clustered_data(collection_format_examples,
                                                                                   ignore_words, host_and_port)
    dict_span_to_counter.update(dict_noun_word_to_counter)
    dict_span_to_counter.update(dict_noun_lemma_to_counter)


def dfs_for_cyclic(visited, helper, node):
    visited.append(node)
    helper.append(node)
    children = node.children
    for child in children:
        if child not in visited:
            ans = dfs_for_cyclic(visited, helper, child)
            if ans == True:
                print(child.span_lst)
                return True
        elif child in helper:
            print(child.span_lst)
            return True
    helper.remove(node)
    return False


def isCyclic(nodes_lst):
    visited = []
    helper = []
    for i in nodes_lst:
        if i not in visited:
            ans = dfs_for_cyclic(visited, helper, i)
            if ans == True:
                print(i.span_lst)
                return True
    return False


def update_nodes_labels(nodes_lst, visited=set()):
    labels_lst = set()
    for node in nodes_lst:
        if node in visited:
            continue
        visited.add(node)
        desc_labels = update_nodes_labels(node.children, visited)
        node.label_lst.update(desc_labels)
        labels_lst.update(node.label_lst)
    return labels_lst


def get_all_spans(np_object_lst, all_spans, visited=set()):
    for np_object in np_object_lst:
        if np_object in visited:
            continue
        visited.add(np_object)
        all_spans.update(np_object.span_lst)
        get_all_spans(np_object.children, all_spans, visited)


def dfs(visited, node):
    if node not in visited:
        visited.append(node)
        for neighbour in node.children:
            dfs(visited, neighbour)


def depth_dag(node, counter=0, visited=set()):
    max_depth = counter
    for child in node.children:
        current_max_depth = depth_dag(child, counter + 1, visited)
        if current_max_depth > max_depth:
            max_depth = current_max_depth
    return max_depth


def get_leaves(node, leaves, visited=set()):
    if node in visited:
        return
    visited.add(node)
    if not node.children:
        leaves.add(node)
        return
    for child in node.children:
        get_leaves(child, leaves, visited)


def get_all_nodes(nodes_lst, visited):
    for node in nodes_lst:
        if node in visited:
            continue
        visited.add(node)
        get_all_nodes(node.children, visited)


def calculation_for_paper(topic_object_lst, top_k_topics):
    visited = set()
    get_all_nodes(topic_object_lst, visited)
    all_dag_nodes = list(visited)
    print("number of nodes is " + str(len(all_dag_nodes)))
    max_depth = 0
    for topic in topic_object_lst:
        depth = depth_dag(topic)
        if depth > max_depth:
            max_depth = depth
    print("the depth of the entire DAG is " + str(max_depth))
    min_leaves = 10000
    max_leaves = 0
    total_leaves = 0
    max_depth = 0
    min_depth = 1000
    total_depth = 0
    all_leaves = set()
    for entry in top_k_topics:
        leaves = set()
        get_leaves(entry, leaves)
        all_leaves.update(leaves)
        leaves_number = len(leaves)
        total_leaves += leaves_number
        if leaves_number < min_leaves:
            min_leaves = leaves_number
        if leaves_number > max_leaves:
            max_leaves = leaves_number
        depth = depth_dag(entry)
        total_depth += depth
        if depth > max_depth:
            max_depth = depth
        if depth < min_depth:
            min_depth = depth
    # top k leaves
    print("average number of leaves is ")
    print(total_leaves / len(top_k_topics))
    print("minimal leaves for top k entry is " + str(min_leaves))
    print("maximal leaves for top k entry is " + str(max_leaves))
    # top k depth
    print("average number of depth is ")
    print(total_depth / len(top_k_topics))
    print("minimal depth for top k entry is " + str(min_depth))
    print("maximal depth for top k entry is " + str(max_depth))
    all_dag_nodes_in_top_k = set()
    get_all_nodes(top_k_topics, all_dag_nodes_in_top_k)
    number_of_children_array = []
    for node in all_dag_nodes_in_top_k:
        if node in top_k_topics:
            continue
        if node in all_leaves:
            continue
        number_of_children_array.append(len(node.children))
    # internal nodes
    print("minimal val of internal nodes is " + str(min(number_of_children_array)))
    print("maximal val of internal nodes is " + str(max(number_of_children_array)))
    print("average number of internal nodes ")
    print(len(number_of_children_array) / len(top_k_topics))
    ans = statistics.variance(number_of_children_array)
    print("The variance of list is : ")
    print(ans)
