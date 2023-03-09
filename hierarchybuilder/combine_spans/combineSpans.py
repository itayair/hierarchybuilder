from hierarchybuilder.combine_spans import utils as combine_spans_utils
from hierarchybuilder import utils as ut


def find_similarity_in_same_length_group(lst_spans_tuple):
    black_list = []
    dict_span_to_similar_spans = {}
    for span_tuple in lst_spans_tuple:
        if span_tuple[0] in black_list:
            continue
        dict_span_to_similar_spans[span_tuple[0]] = set()
        dict_span_to_similar_spans[span_tuple[0]].add(span_tuple[0])
        black_list.append(span_tuple[0])
        for span_tuple_to_compare in lst_spans_tuple:
            if span_tuple_to_compare[0] in black_list:
                continue
            is_similar = combine_spans_utils.is_similar_meaning_between_span(span_tuple[1], span_tuple_to_compare[1])
            if is_similar:
                black_list.append(span_tuple_to_compare[0])
                dict_span_to_similar_spans[span_tuple[0]].add(span_tuple_to_compare[0])
    return dict_span_to_similar_spans


def combine_similar_longest_np_with_common_sub_nps(common_np_to_group_members_indices,
                                                   dict_longest_span_to_his_synonyms, dict_span_to_similar_spans):
    black_lst = []
    for span, indices_group in common_np_to_group_members_indices.items():
        if span in black_lst:
            continue
        synonymous_span = dict_span_to_similar_spans[span].intersection(set(dict_longest_span_to_his_synonyms.keys()))
        for longest_span in synonymous_span:
            if longest_span != span and longest_span in common_np_to_group_members_indices.keys():
                common_np_to_group_members_indices[span].update(
                    common_np_to_group_members_indices[longest_span])
                if longest_span not in black_lst:
                    black_lst.append(longest_span)
    for span in black_lst:
        del common_np_to_group_members_indices[span]


def create_dict_from_common_np_to_group_members_indices(span_to_group_members, dict_span_to_rank,
                                                        dict_longest_span_to_his_synonyms, dict_span_to_similar_spans):
    common_np_to_group_members_indices = {k: v for k, v in
                                          sorted(span_to_group_members.items(), key=lambda item: len(item[1]),
                                                 reverse=True)}
    common_np_to_group_members_indices = {k: v for k, v in common_np_to_group_members_indices.items() if
                                          (len(v) > 1 or ut.dict_span_to_counter.get(k, 1) > 1) and
                                          dict_span_to_rank.get(k, 2) >= 2}

    combine_similar_longest_np_with_common_sub_nps(common_np_to_group_members_indices,
                                                   dict_longest_span_to_his_synonyms, dict_span_to_similar_spans)
    return common_np_to_group_members_indices


def create_data_dicts_for_combine_synonyms(label_to_nps_collection, dict_label_to_longest_nps_group):
    span_to_group_members = {}
    dict_longest_span_to_his_synonyms = {}
    for idx, spans_lst in label_to_nps_collection.items():
        for span in spans_lst:
            span_to_group_members[span] = span_to_group_members.get(span, set())
            span_to_group_members[span].add(idx)
        longest_nps_lst = dict_label_to_longest_nps_group[idx]
        for longest_np in longest_nps_lst:
            dict_longest_span_to_his_synonyms[longest_np] = longest_nps_lst
    span_to_group_members = {k: v for k, v in
                             sorted(span_to_group_members.items(), key=lambda item: len(item[1]),
                                    reverse=True)}
    dict_length_to_span = combine_spans_utils.create_dicts_length_to_span_and_span_to_list(span_to_group_members)
    return span_to_group_members, dict_longest_span_to_his_synonyms, dict_length_to_span


def create_dict_span_to_similar_spans_for_all(dict_span_to_similar_spans_partially):
    dict_span_to_similar_spans = {}
    for _, synonyms in dict_span_to_similar_spans_partially.items():
        for span in synonyms:
            dict_span_to_similar_spans[span] = synonyms
    return dict_span_to_similar_spans


def combine_similar_spans(span_to_group_members, dict_length_to_span,
                          dict_longest_span_to_his_synonyms):
    dict_span_to_similar_spans = {}
    for idx, spans in dict_length_to_span.items():
        dict_span_to_similar_spans.update(find_similarity_in_same_length_group(spans))
    span_to_group_members_new = {}
    for span, sub_set in dict_span_to_similar_spans.items():
        span_to_group_members_new[span] = set()
        for synonym in sub_set:
            span_to_group_members_new[span].update(span_to_group_members[synonym])
    for span, synonyms in dict_span_to_similar_spans.items():
        synonyms_intersect = synonyms.intersection(set(dict_longest_span_to_his_synonyms.keys()))
        for synonym in synonyms_intersect:
            synonyms.update(dict_longest_span_to_his_synonyms[synonym])
    dict_span_to_similar_spans = create_dict_span_to_similar_spans_for_all(dict_span_to_similar_spans)
    return span_to_group_members_new, dict_span_to_similar_spans


def union_common_np(label_to_nps_collection, dict_span_to_rank, dict_label_to_longest_nps_group):
    span_to_group_members, dict_longest_span_to_his_synonyms, dict_length_to_span = \
        create_data_dicts_for_combine_synonyms(label_to_nps_collection, dict_label_to_longest_nps_group)
    span_to_group_members, dict_span_to_similar_spans = combine_similar_spans(span_to_group_members,
                                                                              dict_length_to_span,
                                                                              dict_longest_span_to_his_synonyms)
    common_np_to_group_members_indices = \
        create_dict_from_common_np_to_group_members_indices(span_to_group_members,
                                                            dict_span_to_rank, dict_longest_span_to_his_synonyms,
                                                            dict_span_to_similar_spans)
    return common_np_to_group_members_indices, dict_span_to_similar_spans


def union_nps(label_to_nps_collection, dict_span_to_rank, dict_label_to_longest_nps_group):
    common_np_to_group_members_indices, dict_span_to_similar_spans = union_common_np(
        label_to_nps_collection, dict_span_to_rank, dict_label_to_longest_nps_group)
    dict_score_to_collection_of_sub_groups = combine_spans_utils.get_dict_spans_group_to_score(common_np_to_group_members_indices,
                                                                              dict_span_to_rank,
                                                                              dict_span_to_similar_spans,
                                                                              dict_label_to_longest_nps_group)
    return dict_score_to_collection_of_sub_groups, dict_span_to_similar_spans


def create_index_and_collection_for_longest_nps(longest_np_lst, all_nps_example_lst,
                                                global_longest_np_index, global_index_to_similar_longest_np,
                                                longest_NP_to_global_index, dict_uncounted_expansions,
                                                dict_counted_longest_answers):
    label_to_nps_collection = {}
    dict_label_to_longest_nps_group = {}
    if len(longest_np_lst) == 0:
        dict_label_to_longest_nps_group = {}
    elif len(longest_np_lst) == 1:
        longest_NP_to_global_index[longest_np_lst[0]] = global_longest_np_index[0]
        global_index_to_similar_longest_np[global_longest_np_index[0]] = [longest_np_lst[0]]
        dict_label_to_longest_nps_group = {global_longest_np_index[0]:
                                               [longest_np_lst[0]]}
        global_longest_np_index[0] += 1
    else:
        for phrase in all_nps_example_lst:
            longest_span = phrase[0][0]
            all_expansions = []
            for span in phrase:
                all_expansions.append(span[0])
            # longest np clustering
            global_index_to_similar_longest_np[global_longest_np_index[0]] = [longest_span]
            longest_NP_to_global_index[longest_span] = global_longest_np_index[0]
            dict_label_to_longest_nps_group[global_longest_np_index[0]] = [longest_span]
            # Collection of nps
            label_to_nps_collection[global_longest_np_index[0]] = all_expansions
            global_longest_np_index[0] += 1
    if dict_uncounted_expansions:
        label_to_nps_collection.update(dict_uncounted_expansions)
        dict_label_to_longest_nps_group.update(dict_counted_longest_answers)
    return label_to_nps_collection, dict_label_to_longest_nps_group
