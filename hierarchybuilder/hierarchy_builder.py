from hierarchybuilder.combine_spans import combineSpans, paraphrase_detection_SAP_BERT, combine_nodes_UMLS
from hierarchybuilder import utils as ut
import hierarchybuilder.DAG.hierarchical_structure_algorithms as hierarchical_structure_algorithms
import hierarchybuilder.visualization.json_dag_visualization as json_dag_visualization
import hierarchybuilder.DAG.DAG_utils as DAG_utils
from hierarchybuilder.taxonomy import taxonomies_from_UMLS
import sys
import json

sys.setrecursionlimit(10000)


def initialize_spans_data(all_nps_example_lst):
    dict_idx_to_all_valid_expansions = {}
    dict_idx_to_longest_np = {}
    idx = 0
    for phrase in all_nps_example_lst:
        dict_idx_to_all_valid_expansions[idx] = set()
        dict_idx_to_longest_np[idx] = phrase[0][0]
        for span in phrase:
            dict_idx_to_all_valid_expansions[idx].add(span[0])
        idx += 1
    return dict_idx_to_all_valid_expansions, dict_idx_to_longest_np


def get_uncounted_examples(example_list, global_longest_np_lst, dict_global_longest_np_to_all_counted_expansions,
                           longest_NP_to_global_index, global_index_to_similar_longest_np, dict_span_to_lemma_lst,
                           dict_span_to_rank):
    dict_span_to_all_valid_expansions = {}
    longest_np_lst = []
    longest_np_total_lst = []
    all_nps_example_lst = []
    dict_uncounted_expansions = {}
    dict_counted_longest_answers = {}
    duplicate_longest_answers = set()
    for example in example_list:
        longest_np_total_lst.append(example[0])
        if example[0] in duplicate_longest_answers:
            continue
        duplicate_longest_answers.add(example[0])
        if example[0] in global_longest_np_lst:
            label = longest_NP_to_global_index[example[0]]
            dict_counted_longest_answers[label] = set()
            for longest_answer in global_index_to_similar_longest_np[label]:
                dict_counted_longest_answers[label].add(longest_answer)
            uncounted_expansions = set()
            for item in example[1]:
                if item[0] in dict_global_longest_np_to_all_counted_expansions[example[0]]:
                    continue
                dict_span_to_lemma_lst[item[0]] = item[2]
                dict_span_to_rank[item[0]] = len(item[2])
                dict_global_longest_np_to_all_counted_expansions[example[0]].add(item[0])
                uncounted_expansions.add(item[0])
            if uncounted_expansions:
                dict_uncounted_expansions[label] = uncounted_expansions
            continue
        dict_global_longest_np_to_all_counted_expansions[
            example[0]] = dict_global_longest_np_to_all_counted_expansions.get(example[0], set())
        for item in example[1]:
            dict_span_to_lemma_lst[item[0]] = item[2]
            dict_span_to_rank[item[0]] = len(item[2])
            dict_global_longest_np_to_all_counted_expansions[example[0]].add(item[0])
        global_longest_np_lst.add(example[0])
        dict_span_to_all_valid_expansions[example[0]] = [item[0] for item in example[1]]
        longest_np_lst.append(example[0])
        all_nps_example_lst.append(example[1])
    return dict_span_to_all_valid_expansions, longest_np_lst, longest_np_total_lst, all_nps_example_lst, \
           dict_uncounted_expansions, dict_counted_longest_answers


def hierarchy_builder(examples, entries_number=50, ignore_words=None, device="", umls_host="127.0.0.1", umls_port=5000,
                      has_umls_server=False):
    ut.initialize_data(examples, umls_host, umls_port, ignore_words, entries_number, device,
                       has_umls_server)
    dict_span_to_rank = {}
    dict_span_to_lemma_lst = ut.dict_span_to_lemma_lst
    global_dict_label_to_object = {}
    span_to_object = {}
    topic_object_lst = []
    dict_object_to_global_label = {}
    global_index_to_similar_longest_np = {}
    all_spans = set()
    span_to_vector = {}
    global_longest_np_lst = set()
    dict_global_longest_np_to_all_counted_expansions = {}
    global_longest_np_index = [0]
    longest_NP_to_global_index = {}
    # print("Start the detection of equivalent spans by BOW + building the DAG")
    for topic, examples_list in ut.topics_dict.items():
        topic_synonym_lst = set(ut.dict_noun_lemma_to_synonyms[topic])
        for synonym in topic_synonym_lst:
            dict_span_to_rank[synonym] = 1
        dict_span_to_all_valid_expansions, longest_np_lst, longest_np_total_lst, all_nps_example_lst, \
        dict_uncounted_expansions, dict_counted_longest_answers = \
            get_uncounted_examples(examples_list, global_longest_np_lst,
                                   dict_global_longest_np_to_all_counted_expansions, longest_NP_to_global_index,
                                   global_index_to_similar_longest_np, dict_span_to_lemma_lst, dict_span_to_rank)
        label_to_nps_collection, dict_label_to_longest_nps_group = \
            combineSpans.create_index_and_collection_for_longest_nps(longest_np_lst, all_nps_example_lst,
                                                                     global_longest_np_index,
                                                                     global_index_to_similar_longest_np,
                                                                     longest_NP_to_global_index,
                                                                     dict_uncounted_expansions,
                                                                     dict_counted_longest_answers)
        dict_score_to_collection_of_sub_groups, dict_span_to_similar_spans = \
            combineSpans.union_nps(label_to_nps_collection, dict_span_to_rank, dict_label_to_longest_nps_group)
        DAG_utils.insert_examples_of_topic_to_DAG(dict_score_to_collection_of_sub_groups, topic_synonym_lst,
                                                  dict_span_to_lemma_lst, span_to_object, dict_span_to_similar_spans,
                                                  global_dict_label_to_object, topic_object_lst, longest_np_total_lst,
                                                  longest_np_lst, longest_NP_to_global_index,
                                                  dict_object_to_global_label)
    print("End the detection of equivalent spans by BOW + building the DAG")
    ut.get_all_spans(topic_object_lst, all_spans)
    all_spans = list(all_spans)
    DAG_utils.initialize_all_spans_vectors(all_spans, span_to_vector)
    DAG_utils.initialize_nodes_weighted_average_vector(topic_object_lst, global_index_to_similar_longest_np,
                                                       span_to_vector)
    DAG_utils.update_symmetric_relation_in_DAG(topic_object_lst)
    # print("Start to detect equivalent nodes by DL model")
    paraphrase_detection_SAP_BERT.combine_equivalent_nodes_by_semantic_DL_model(topic_object_lst.copy(),
                                                                                topic_object_lst, span_to_object,
                                                                                dict_object_to_global_label,
                                                                                global_dict_label_to_object,
                                                                                span_to_vector)
    print("End to detect equivalent nodes among children of each node by DL model")
    DAG_utils.update_symmetric_relation_in_DAG(topic_object_lst)
    if has_umls_server:
        combine_nodes_UMLS.combine_nodes_by_umls_synonymous_spans(span_to_object, dict_object_to_global_label,
                                                                  global_dict_label_to_object, topic_object_lst,
                                                                  span_to_vector)
        ut.update_nodes_labels(topic_object_lst)
        DAG_utils.update_symmetric_relation_in_DAG(topic_object_lst)
    DAG_utils.initialize_nodes_weighted_average_vector(topic_object_lst, global_index_to_similar_longest_np,
                                                       span_to_vector)
    # Adding taxonomic nodes
    taxonomic_np_objects = {}
    if has_umls_server:
        taxonomic_np_objects = taxonomies_from_UMLS.add_taxonomies_to_DAG_by_UMLS(topic_object_lst, dict_span_to_rank,
                                                                                  span_to_object, span_to_vector)
        print("End to detect equivalent nodes and taxonomic relations by UMLS")
        DAG_utils.update_symmetric_relation_in_DAG(topic_object_lst)
        DAG_utils.initialize_nodes_weighted_average_vector(topic_object_lst, global_index_to_similar_longest_np,
                                                           span_to_vector)
    paraphrase_detection_SAP_BERT.combine_equivalent_parent_and_children_nodes_by_semantic_DL_model(
        topic_object_lst.copy(), span_to_object, dict_object_to_global_label, global_dict_label_to_object,
        topic_object_lst, span_to_vector)
    print("End to detect close in meaning children and parent nodes by DL model")
    DAG_utils.update_symmetric_relation_in_DAG(topic_object_lst)
    ut.update_nodes_labels(topic_object_lst)
    # DAG Pruning
    hierarchical_structure_algorithms.DAG_contraction_by_set_cover_algorithm(topic_object_lst,
                                                                             global_dict_label_to_object,
                                                                             global_index_to_similar_longest_np)
    ut.update_nodes_labels(topic_object_lst)
    print("Finish DAG contraction")
    DAG_utils.remove_redundant_nodes(topic_object_lst)
    print("Redundant nodes were removed")
    ut.update_nodes_labels(topic_object_lst)
    DAG_utils.initialize_nodes_weighted_average_vector(topic_object_lst, global_index_to_similar_longest_np,
                                                       span_to_vector)
    # Entry-point selection
    top_k_topics, already_counted_labels, all_labels = \
        hierarchical_structure_algorithms.extract_top_k_concept_nodes_greedy_algorithm(entries_number, topic_object_lst,
                                                                                       global_index_to_similar_longest_np)
    print("Finish select top k")
    json_top_k_nodes = json_dag_visualization.json_dag_visualization(top_k_topics, global_index_to_similar_longest_np,
                                                                     taxonomic_np_objects, topic_object_lst)
    return json_top_k_nodes


# def get_words_as_span(words):
#     span = ""
#     idx = 0
#     for word in words:
#         # if idx == 0 and token.tag_ in ['IN', 'TO']:
#         #     continue
#         if idx != 0 and (word != ',' and word != '.'):
#             span += ' '
#         span += word
#         idx += 1
#     return span
#
#
# def convert_to_input_format(data):
#     # f = open(file_name, 'r', encoding='utf-8')
#     # data = json.load(f)
#     example_lst = []
#     ignore_lst = set()
#     disease_name_lst = set()
#     for type in data:
#         example_data = type['sub_matches']['main']
#         sentence_as_lst = example_data['words']
#         offset_first = example_data['captures']['arg1']['first']
#         offset_last = example_data['captures']['arg1']['last']
#         span_as_lst = sentence_as_lst[offset_first: offset_last + 1]
#         example_lst.append((get_words_as_span(sentence_as_lst), get_words_as_span(span_as_lst)))
#         symptom_offset_first = example_data['captures']['arg2']['first']
#         symptom_offset_last = example_data['captures']['arg2']['last']
#         symptom_name = sentence_as_lst[symptom_offset_first: symptom_offset_last + 1]
#         ignore_lst.update(symptom_name)
#         disease_name_lst.add(get_words_as_span(symptom_name))
#     return example_lst, ignore_lst, disease_name_lst
#
#
# file_name_all = 'input_files/input_json_files/full_results.jsonl'
# # f = open(file_name_all, 'r', encoding='utf-8')
# json_data_lst = []
# counter = 0
# for line in open(file_name_all, 'r', encoding='utf-8'):
#     if counter < 51:
#         counter += 1
#         continue
#     if counter > 54:
#         break
#     symptom_data = json.loads(line)
#     example_lst, ignore_lst, disease_name_lst = convert_to_input_format(symptom_data)
#     if not ignore_lst:
#         continue
#     symptom_name = list(disease_name_lst)[0].lower()
#     ignore_lst.update(['cause', 'induced'])
#     json_top_k_nodes_output = hierarchy_builder(examples=example_lst, umls_host="127.0.0.1", umls_port=3500, entries_number=50,
#                                          ignore_words=list(ignore_lst), has_umls_server=True)
#     with open(symptom_name + '.json', 'w') as result_file:
#         result_file.write(json_top_k_nodes_output)
#     counter += 1
#     break
