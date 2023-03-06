import spacy
from hierarchybuilder.expansions import valid_expansion, valid_expansion_utils
import json

nlp = spacy.load("en_ud_model_sm")


def find_sub_list(sub_lst, lst):
    sll = len(sub_lst)
    for ind in (i for i, e in enumerate(lst) if e == sub_lst[0]):
        if lst[ind:ind + sll] == sub_lst:
            return ind, ind + sll - 1
    return -1, -1


def from_tokens_to_string_list(spacy_doc):
    tokens_lst = []
    for token in spacy_doc:
        tokens_lst.append(token.text)
    return tokens_lst


def get_tokens_from_list_by_indices(start_idx_span, end_idx_span, spacy_doc):
    tokens_lst = []
    for token in spacy_doc:
        tokens_lst.append(token)
    return tokens_lst[start_idx_span:end_idx_span + 1]


def find_spacy_span_in_spacy_sentence(span, sentence):
    span_lst = from_tokens_to_string_list(span)
    sent_lst = from_tokens_to_string_list(sentence)
    return find_sub_list(span_lst, sent_lst)


def get_example_from_txt_format(line):
    temp = line.replace("<e1>", "")
    sentence = temp.replace("</e1>", "")
    span = line[line.find("<e1>") + 4: line.find("</e1>")]
    return sentence, span


def get_sentence_ans_span_from_format(sentence, span):
    sent_as_doc = nlp(sentence)
    span_as_doc = nlp(span)
    start_idx_span, end_idx_span = find_spacy_span_in_spacy_sentence(span_as_doc, sent_as_doc)
    if start_idx_span == -1:
        sentence, span, None, None
    span_as_doc = get_tokens_from_list_by_indices(start_idx_span, end_idx_span, sent_as_doc)
    return sentence, span, sent_as_doc, span_as_doc


def get_tokens_as_span(words):
    span = ""
    idx = 0
    for word in words:
        if idx != 0 and (word != ',' and word != '.'):
            span += ' '
        span += word
        idx += 1
    return span


def get_examples_from_input_file(file_name, is_txt_format):
    examples = []
    if is_txt_format:
        with open(file_name, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for line in lines:
                sentence, span = get_example_from_txt_format(line)
                examples.append((sentence, span))
    else:
        f = open(file_name, 'r', encoding='utf-8')
        data = json.load(f)
        for type in data:
            for mention in type['mentions']:
                span_as_lst = mention['words'][mention['offsets']['first']: mention['offsets']['last'] + 1]
                examples.append((get_tokens_as_span(mention['words']), get_tokens_as_span(span_as_lst)))
        f.close()
    return examples


def get_examples_in_all_valid_answers_format(examples):
    collection_format_examples = []
    for example in examples:
        sentence, span = example
        sentence, span, sent_as_doc, span_as_doc = get_sentence_ans_span_from_format(sentence, span)
        if sent_as_doc is None:
            print(sentence)
            print(span)
            continue
        head_of_span = valid_expansion_utils.get_head_of_span(span_as_doc)
        if head_of_span is None:
            continue
        collection_format_examples.append((head_of_span, sent_as_doc, sentence))
    collection_format_examples = valid_expansion.get_all_expansions_of_span_from_lst(collection_format_examples)
    return collection_format_examples


def get_examples_from_special_format(file_name='input_files/text_files/chest_pain_causes.txt', is_txt_format=False):
    examples = get_examples_from_input_file(file_name, is_txt_format)
    collection_format_examples = get_examples_in_all_valid_answers_format(examples)
    return collection_format_examples

