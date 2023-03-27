from nltk.corpus import wordnet
import requests
from hierarchybuilder.expansions import valid_expansion_utils
import json
from nltk.corpus import stopwords

# import umls_loader
stop_words = set(stopwords.words('english'))
tied_deps = ['compound', 'mwe', 'name', 'nummod']
neglect_deps = ['neg', 'case', 'mark', 'auxpass', 'aux', 'cop', 'nummod', 'quantmod', 'nmod:npmod', 'det:predet']

dict_span_to_topic_entry = {}
dict_span_to_rank = {}
dict_noun_lemma_to_counter = {}
dict_noun_lemma_to_examples = {}
dict_noun_lemma_to_noun_words = {}
dict_noun_word_to_counter = {}
dict_noun_lemma_to_span = {}


def filter_dict_by_lst(topic_lst):
    global dict_noun_lemma_to_examples, dict_noun_lemma_to_counter
    dict_noun_lemma_to_examples = {key: dict_noun_lemma_to_examples[key] for key in dict_noun_lemma_to_examples if
                                   key in topic_lst}
    dict_noun_lemma_to_counter = {key: dict_noun_lemma_to_counter[key] for key in dict_noun_lemma_to_counter if
                                  key in topic_lst}
    return dict_noun_lemma_to_examples, dict_noun_lemma_to_counter


def set_cover():
    covered = set()
    topic_lst = set()
    noun_to_spans_lst = []
    for noun, tuples_span_lst in dict_noun_lemma_to_examples.items():
        spans_lst = [tuple_span[0] for tuple_span in tuples_span_lst]
        noun_to_spans_lst.append((noun, set(spans_lst)))
    while True:
        item = max(noun_to_spans_lst, key=lambda s: len(s[1] - covered))
        if len(item[1] - covered) > 0:
            covered.update(item[1])
            topic_lst.add(item[0])
        else:
            break
    return topic_lst


def update_recurrent_span(dict_sentence_to_span_lst, sentence, span, dict_longest_span_to_counter, all_valid_nps_lst,
                          dict_span_to_counter, counter, dict_full_np_to_sentences):
    if span not in dict_sentence_to_span_lst[sentence]:
        dict_sentence_to_span_lst[sentence].append(span)
        if span in dict_longest_span_to_counter:
            dict_longest_span_to_counter[span] += 1
            dict_full_np_to_sentences[span].append(sentence)
            counter += 1
        for sub_span in all_valid_nps_lst:
            dict_span_to_counter[
                valid_expansion_utils.get_tokens_as_span(sub_span[0])] = dict_span_to_counter.get(
                valid_expansion_utils.get_tokens_as_span(sub_span[0]), 0) + 1
    return counter


def update_new_valid_example(span, dict_longest_span_to_counter, all_valid_nps_lst,
                             dict_span_to_counter, valid_expansion_utils, counter, valid_span_lst):
    dict_longest_span_to_counter[span] = 1
    # if not valid_span_lst:
    #     dict_span_to_counter[span] = dict_span_to_counter.get(span, 0) + 1
    #     print("There is longest expansion that isn't in the all_valid_nps_lst")
    for sub_span in all_valid_nps_lst:
        dict_span_to_counter[valid_expansion_utils.get_tokens_as_span(sub_span[0])] = dict_span_to_counter.get(
            valid_expansion_utils.get_tokens_as_span(sub_span[0]), 0) + 1
    valid_span_lst.add(span)
    counter += 1
    return counter


def initialize_token_expansions_information(all_valid_nps_lst, token, lemma_word, span):
    expansions_contain_word = []
    for sub_span in all_valid_nps_lst:
        if token in sub_span[0]:
            np_span = valid_expansion_utils.get_tokens_as_span(sub_span[0])
            dict_span_to_rank[np_span] = sub_span[1]
            lemma_lst = from_tokens_to_lemmas(sub_span[0])
            expansions_contain_word.append((np_span, sub_span[1], lemma_lst))
    # if lemma_word == 'null':
    #     print("something is strange")
    dict_noun_lemma_to_examples[lemma_word] = dict_noun_lemma_to_examples.get(lemma_word, [])
    dict_noun_lemma_to_examples[lemma_word].append((span, expansions_contain_word))
    dict_noun_lemma_to_counter[lemma_word] = dict_noun_lemma_to_counter.get(lemma_word, 0)
    dict_noun_lemma_to_counter[lemma_word] += 1
    dict_span_to_topic_entry[span] = dict_span_to_topic_entry.get(span, set())
    dict_span_to_topic_entry[span].add(lemma_word)


def add_word_collection_to_data_structures(word, tokens_already_counted, lemma_already_counted,
                                           all_valid_nps_lst, span, ignore_words):
    is_valid_example = False
    if word.pos_ in ['NOUN', 'ADJ', 'PROPN']:
        compound_noun = combine_tied_deps_recursively_and_combine_their_children(word)
        compound_noun.sort(key=lambda x: x.i)
        is_valid_example = False
        token = word
        # for token in compound_noun:
        if token.dep_ in ['quantmod', 'nummod'] or token.text == '-':
            return False
        lemma_token = token.lemma_.lower()
        if lemma_token in lemma_already_counted:
            return is_valid_example
        lemma_already_counted.add(lemma_token)
        if lemma_token in ignore_words:
            return is_valid_example
        if token not in tokens_already_counted:
            dict_noun_word_to_counter[lemma_token] = dict_noun_word_to_counter.get(lemma_token, 0) + 1
            dict_noun_lemma_to_noun_words[lemma_token] = dict_noun_lemma_to_noun_words.get(lemma_token,
                                                                                           set())
            tokens_already_counted.add(token)
            initialize_token_expansions_information(all_valid_nps_lst, token, lemma_token, span)
            is_valid_example = True
    return is_valid_example


def combine_dicts(dict_clustered_spans_last, dict_clustered_spans):
    new_dict_clustered_spans = {}
    for phrase_main, phrases_lst in dict_clustered_spans.items():
        new_dict_clustered_spans[phrase_main] = []
        for phrase in phrases_lst:
            new_dict_clustered_spans[phrase_main].extend(dict_clustered_spans_last[phrase])
    return new_dict_clustered_spans


def combine_tied_deps_recursively_and_combine_their_children(head):
    combined_tied_tokens = [head]
    for child in head.children:
        if child.dep_ in tied_deps:
            temp_tokens = combine_tied_deps_recursively_and_combine_their_children(child)
            combined_tied_tokens.extend(temp_tokens)
    return combined_tied_tokens


def get_words_as_span(span_lst):
    span = ""
    idx = 0
    for word in span_lst:
        if idx != 0 and word != ',':
            span += ' '
        span += word
        idx += 1
    return span


def from_tokens_to_lemmas(tokens):
    lemma_lst = []
    for token in tokens:
        if token.dep_ in neglect_deps or token.lemma_ in stop_words or token.text in \
                ['-', '/', '//', ',', '(', ')', '.', ' ']:
            continue
        lemma_lst.append(token.lemma_.lower())
    return lemma_lst


def get_dict_sorted_and_filtered(dict_noun_lemma_to_value, abbreviations_lst, dict_noun_lemma_to_counter, head_lst):
    dict_noun_lemma_to_value = {key: dict_noun_lemma_to_value[key] for key in dict_noun_lemma_to_value if
                                (key in head_lst or dict_noun_lemma_to_counter[key] > 1) and
                                ord('A') <= ord(key[:1]) <= ord('z') and len(key) > 1 and key not in abbreviations_lst}
    return dict_noun_lemma_to_value


def get_synonyms_by_word(word):
    synonyms = set()
    for syn in wordnet.synsets(word):
        for l in syn.lemmas():
            synonyms.add(l.name())
    return synonyms


def create_dict_from_wordnet_word_to_exist_synonyms(lemma_lst, dict_lemma_to_synonyms):
    for lemma in lemma_lst:
        synonyms = get_synonyms_by_word(lemma)
        synonyms = [synonym for synonym in synonyms if synonym in lemma_lst]
        synonyms.append(lemma)
        dict_lemma_to_synonyms[lemma] = set(synonyms)


def create_dicts_for_words_similarity(dict_word_to_lemma, host_and_port, has_umls_server):
    lemma_lst = set()
    for _, lemma in dict_word_to_lemma.items():
        lemma_lst.add(lemma)
    dict_lemma_to_synonyms = {}
    create_dict_from_wordnet_word_to_exist_synonyms(lemma_lst, dict_lemma_to_synonyms)
    word_lst = list(lemma_lst)
    if has_umls_server:
        update_dictionary_umls_synonyms(dict_lemma_to_synonyms, word_lst, host_and_port)
    dict_lemma_to_synonyms = {k: v for k, v in
                              sorted(dict_lemma_to_synonyms.items(), key=lambda item: len(item[1]),
                                     reverse=True)}
    return dict_lemma_to_synonyms


def remove_non_relevant_synonyms_from_dict(dict_word_to_synonyms):
    for noun, synonyms in dict_word_to_synonyms.items():
        remove_lst = set()
        for synonym in synonyms:
            if synonym not in dict_word_to_synonyms:
                remove_lst.add(synonym)
        for synonym in remove_lst:
            synonyms.remove(synonym)


def update_dictionary_umls_synonyms(dict_word_to_synonyms, word_lst, host_and_port):
    for i in range(0, len(word_lst), 100):
        chunk = word_lst[i: i + 100]
        if 'null' in chunk:
            chunk.remove('null')
        try:
            post_data = json.dumps(chunk)
            dict_response = requests.post(host_and_port + '/create_synonyms_dictionary/',
                                          params={"words": post_data})
            output = dict_response.json()["synonyms"]
            dict_word_to_synonyms.update(output)
        except:
            for word in chunk:
                try:
                    post_data = json.dumps([word])
                    dict_response = requests.post(host_and_port + '/create_synonyms_dictionary/',
                                                  params={"words": post_data})
                    output = dict_response.json()["synonyms"]
                    dict_word_to_synonyms.update(output)
                except:
                    continue
    remove_non_relevant_synonyms_from_dict(dict_word_to_synonyms)


def create_synonym_dicts(dict_noun_lemma_to_synonyms, host_and_port, has_umls_server):
    global dict_noun_lemma_to_examples, dict_noun_lemma_to_counter
    dict_noun_lemma_to_examples_new = {}
    dict_noun_lemma_to_counter_new = {}
    dict_noun_lemma_to_examples = {k: v for k, v in
                                   sorted(dict_noun_lemma_to_examples.items(), key=lambda item: len(item[1]),
                                          reverse=True)}
    word_lst = list(dict_noun_lemma_to_examples.keys())
    if has_umls_server:
        update_dictionary_umls_synonyms(dict_noun_lemma_to_synonyms, word_lst, host_and_port)
    else:
        create_dict_from_wordnet_word_to_exist_synonyms(word_lst, dict_noun_lemma_to_synonyms)
        remove_non_relevant_synonyms_from_dict(dict_noun_lemma_to_synonyms)
    for word, synonyms in dict_noun_lemma_to_synonyms.items():
        dict_noun_lemma_to_examples_new[word] = []
        dict_noun_lemma_to_examples_new[word].extend(dict_noun_lemma_to_examples[word])
        dict_noun_lemma_to_counter_new[word] = dict_noun_lemma_to_counter[word]
        for synonym in synonyms:
            if word == synonym:
                continue
            for spans in dict_noun_lemma_to_examples[synonym]:
                dict_noun_lemma_to_examples_new[word].append((spans[0], spans[1]))
            dict_noun_lemma_to_counter_new[word] += dict_noun_lemma_to_counter[synonym]
    dict_noun_lemma_to_counter_new = {k: v for k, v in
                                      sorted(dict_noun_lemma_to_counter_new.items(), key=lambda item: item[1])}
    dict_noun_lemma_to_span_new = {k: v for k, v in
                                   sorted(dict_noun_lemma_to_examples_new.items(), key=lambda item: len(item[1]),
                                          reverse=True)}
    dict_noun_lemma_to_examples = dict_noun_lemma_to_span_new
    dict_noun_lemma_to_counter = dict_noun_lemma_to_counter_new
