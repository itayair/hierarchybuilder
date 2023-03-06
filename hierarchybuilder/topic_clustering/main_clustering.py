from hierarchybuilder.topic_clustering import utils_clustering
from hierarchybuilder.expansions import valid_expansion_utils
import json
import requests


def filter_and_sort_dicts():
    topic_lst = utils_clustering.set_cover()
    utils_clustering.filter_dict_by_lst(topic_lst)


def combine_word_in_upper_case_to_word_in_lower_if_exist(dict_noun_lemma_to_counter, dict_noun_lemma_to_examples,
                                                         upper_case_noun_lst):
    entries_to_remove = set()
    for upper_case_noun_entry in upper_case_noun_lst:
        lower_case_noun_entry = upper_case_noun_entry.lower()
        if lower_case_noun_entry in dict_noun_lemma_to_examples and upper_case_noun_entry in dict_noun_lemma_to_examples:
            entries_to_remove.add(upper_case_noun_entry)
            upper_case_noun_entry_examples = dict_noun_lemma_to_examples[upper_case_noun_entry]
            dict_noun_lemma_to_examples[lower_case_noun_entry].extend(upper_case_noun_entry_examples)
            if lower_case_noun_entry in dict_noun_lemma_to_counter and \
                    upper_case_noun_entry in dict_noun_lemma_to_counter:
                dict_noun_lemma_to_counter[lower_case_noun_entry] += dict_noun_lemma_to_counter[upper_case_noun_entry]
    for entry in entries_to_remove:
        dict_noun_lemma_to_examples.pop(entry, None)
        dict_noun_lemma_to_counter.pop(entry, None)


def create_dictionary_for_abbreviation(examples):
    abbreviation_lst = set()
    noun_words = set()
    dict_compound_noun_to_lst = {}
    for biggest_noun_phrase, head_span, all_valid_nps_lst, sentence in examples:
        compound_noun = utils_clustering.combine_tied_deps_recursively_and_combine_their_children(head_span)
        compound_noun.sort(key=lambda x: x.i)
        compound_as_lemma_lst = []
        for token in compound_noun:
            compound_as_lemma_lst.append(token.text.lower())
        compound_noun_as_span = valid_expansion_utils.get_tokens_as_span(compound_noun)
        dict_compound_noun_to_lst[compound_noun_as_span] = compound_as_lemma_lst
        for token in biggest_noun_phrase:
            if token.pos_ in "NOUN":
                compound_noun = utils_clustering.combine_tied_deps_recursively_and_combine_their_children(token)
                for token in compound_noun:
                    if token.text.isupper():
                        abbreviation_lst.add(token.text)
                        continue
                    noun_words.add(token.lemma_.lower())
    remove_lst = set()
    dict_abbreviation_to_elaboration = {}
    for abbreviation in abbreviation_lst:
        if abbreviation.lower() in noun_words:
            dict_abbreviation_to_elaboration[abbreviation] = abbreviation.lower()
            remove_lst.add(abbreviation)
    abbreviation_lst = abbreviation_lst - remove_lst
    return abbreviation_lst, dict_compound_noun_to_lst, dict_abbreviation_to_elaboration


def replace_abbreviation_with_elaboration(dict_abbreviation_to_elaboration, dict_noun_lemma_to_examples,
                                          dict_elaboration_to_lst, dict_noun_word_to_counter):
    for abbreviation, elaboration in dict_abbreviation_to_elaboration.items():
        for word in elaboration:
            example_lst = dict_noun_lemma_to_examples.get(word, [])
            if not example_lst:
                continue
            example_lst_abbreviation = dict_noun_lemma_to_examples[abbreviation]
            dict_noun_word_to_counter[word.lemma_lower()] += dict_noun_word_to_counter[abbreviation]
            dict_noun_word_to_counter.pop(abbreviation, None)
            dict_noun_lemma_to_examples.pop(abbreviation, None)
            example_lst_abbreviation_new = []
            for example in example_lst_abbreviation:
                np = example[0].replace(abbreviation, elaboration)
                score = example[1] + len(dict_elaboration_to_lst[elaboration]) - 1
                np_lemmas_lst = set()
                for lemma_word in example[2]:
                    if lemma_word == abbreviation:
                        for token in dict_elaboration_to_lst[elaboration]:
                            np_lemmas_lst.add(token)
                        continue
                    np_lemmas_lst.add(lemma_word)
                example_lst_abbreviation_new.append(np, score, np_lemmas_lst)
            dict_noun_lemma_to_examples[word.lemma_lower()].extend(example_lst_abbreviation_new)


def find_match_for_abbreviation(abbreviation_lst, dict_noun_compound_to_lst, dict_abbreviation_to_elaboration):
    abbreviation_lst_as_json = json.dumps(list(abbreviation_lst))
    compound_lst_as_json = json.dumps(list(dict_noun_compound_to_lst.keys()))
    dict_response = requests.post('http://127.0.0.1:5000/create_abbreviation_dict/',
                                  params={"abbreviations": abbreviation_lst_as_json,
                                          "compound_lst": compound_lst_as_json})
    dict_abbreviation_to_compound = dict_response.json()["dict_abbreviation_to_compound"]
    dict_abbreviation_to_elaboration.update(dict_abbreviation_to_compound)


def convert_examples_to_clustered_data(examples, ignore_words):
    dict_noun_lemma_to_synonyms = {}
    span_lst = set()
    dict_span_to_counter = {}
    dict_longest_span_to_counter = {}
    dict_word_to_lemma = {}
    counter = 0
    dict_sentence_to_span_lst = {}
    valid_span_lst = set()
    for biggest_noun_phrase, head_span, all_valid_nps_lst, sentence in examples:
        span = valid_expansion_utils.get_tokens_as_span(biggest_noun_phrase)
        dict_sentence_to_span_lst[sentence] = dict_sentence_to_span_lst.get(sentence, [])
        if span in span_lst:
            counter = utils_clustering.update_recurrent_span(dict_sentence_to_span_lst, sentence, span,
                                                             dict_longest_span_to_counter, all_valid_nps_lst,
                                                             dict_span_to_counter, counter)
            continue
        dict_sentence_to_span_lst[sentence].append(span)
        span_lst.add(span)
        tokens_already_counted = set()
        lemma_already_counted = set()
        is_valid_example = False
        for word in biggest_noun_phrase:
            if word in tokens_already_counted:
                continue
            lemma_word = word.lemma_.lower()
            dict_word_to_lemma[word.text.lower()] = lemma_word
            is_valid_example |= utils_clustering.add_word_collection_to_data_structures(word, tokens_already_counted,
                                                                                        lemma_already_counted,
                                                                                        all_valid_nps_lst, span,
                                                                                        ignore_words)
        if is_valid_example:
            counter = utils_clustering.update_new_valid_example(span, dict_longest_span_to_counter, all_valid_nps_lst,
                                                                dict_span_to_counter,
                                                                valid_expansion_utils, counter, valid_span_lst)
    print(counter)
    utils_clustering.synonyms_consolidation(dict_noun_lemma_to_synonyms)
    filter_and_sort_dicts()
    dict_lemma_to_synonyms = utils_clustering.create_dicts_for_words_similarity(dict_word_to_lemma)
    dict_lemma_to_synonyms.update(dict_noun_lemma_to_synonyms)
    topics_dict = {k: v for k, v in
                   sorted(utils_clustering.dict_noun_lemma_to_examples.items(), key=lambda item: len(item[1]),
                          reverse=True)}
    return topics_dict, dict_span_to_counter, dict_word_to_lemma, dict_lemma_to_synonyms, \
           dict_longest_span_to_counter, dict_noun_lemma_to_synonyms, utils_clustering.dict_noun_lemma_to_noun_words, \
           utils_clustering.dict_noun_lemma_to_counter, utils_clustering.dict_noun_word_to_counter
