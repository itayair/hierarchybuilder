from hierarchybuilder.expansions import valid_expansion_utils
from nltk.corpus import stopwords

stop_words = set(stopwords.words('english'))
tied_deps = ['compound', 'mwe', 'case', 'mark', 'auxpass', 'name', 'aux', 'neg', 'det', 'goeswith', 'nummod',
             'quantmod', 'nmod:npmod']
tied_couples = [['auxpass', 'nsubjpass']]

dep_type_optional = ['advmod', 'dobj', 'npadvmod', 'nmod', 'conj', 'aux', 'poss', 'nmod:poss',
                     'xcomp']  # , 'conj', 'nsubj', 'appos'

acl_to_seq = ['acomp', 'dobj', 'nmod']  # acl and relcl + [[['xcomp'], ['aux']], 'dobj']
dep_to_seq = ['quantmod', 'cop']  # 'cc',
combined_with = ['acl', 'relcl', 'acl:relcl', 'ccomp', 'advcl', 'amod']  # +, 'cc'
couple_to_seq = {'quantmod': ['amod'], 'cop': ['nsubjpass']}  # 'nsubjpass': ['amod'] ,'cc': ['conj', 'nmod']

low_val_dep = ['neg', 'nmod:poss', 'case', 'mark', 'auxpass', 'aux', 'nummod', 'quantmod', 'cop']
med_val_dep = ['nsubjpass', 'advmod', 'npadvmod', 'conj', 'poss', 'nmod:poss', 'xcomp', 'nmod:npmod', 'dobj', 'nmod',
               'amod', 'nsubj', 'acl', 'relcl', 'acl:relcl', 'ccomp', 'advcl']
max_val_dep = ['compound', 'mwe', 'name']
neglect_deps = ['neg', 'case', 'mark', 'auxpass', 'aux', 'cop']


def get_tied_couple_by_deps(first_dep, second_dep, children):
    first_token = None
    second_token = None
    for child in children:
        if child.dep_ == first_dep:
            first_token = child
        if child.dep_ == second_dep:
            second_token = child
    return first_token, second_token


def get_tied_couples(children):
    tied_couples_to_add = []
    for dep_couples in tied_couples:
        first_token, second_token = get_tied_couple_by_deps(dep_couples[0], dep_couples[1], children)
        if not first_token or not second_token:
            continue
        tied_couples_to_add.append(first_token)
        tied_couples_to_add.append(second_token)
    return tied_couples_to_add


tied_compound = ['compound', 'mwe', 'name']


def is_dep_tied_by_tied_preposition(token):
    for child in token.children:
        if child.dep_ in ['case', 'mark']:
            if child.text.lower() == 'of':
                return True
        if child.dep_ in tied_compound:
            is_dep_tied = is_dep_tied_by_tied_preposition(child)
            if is_dep_tied:
                return True
    return False


def combine_tied_deps_recursively_and_combine_their_children(head, boundary_np_to_the_left):
    combined_children_lst = []
    combined_tied_tokens = [head]
    tied_couples_to_add = get_tied_couples(head.children)
    for child in head.children:
        if boundary_np_to_the_left > child.i:
            continue
        if child.dep_ in tied_deps or child in tied_couples_to_add:
            temp_tokens, temp_children = combine_tied_deps_recursively_and_combine_their_children(
                child, boundary_np_to_the_left)
            combined_tied_tokens.extend(temp_tokens)
            combined_children_lst.extend(temp_children)
        else:
            if is_dep_tied_by_tied_preposition(child):
                temp_tokens, temp_children = combine_tied_deps_recursively_and_combine_their_children(
                    child, boundary_np_to_the_left)
                combined_tied_tokens.extend(temp_tokens)
                combined_children_lst.extend(temp_children)
            else:
                combined_children_lst.append(child)
    return combined_tied_tokens, combined_children_lst


def get_if_has_preposition_child_between(token, head):
    prep_lst = []
    for child in token.children:
        if child.dep_ == 'case' and child.tag_ == 'IN':
            prep_lst.append(child)
    if prep_lst:
        first_prep_child_index = 100
        prep_child = None
        for child in prep_lst:
            if child.i < first_prep_child_index:
                prep_child = child
        if token.i > head.i:
            first_val = head.i
            second_val = token.i
        else:
            first_val = token.i
            second_val = head.i
        if first_val < prep_child.i < second_val:
            return prep_child
        else:
            return None
    return None


def initialize_couple_lst(others, couple_lst, lst_children):
    for other in others:
        dep_type = couple_to_seq[other.dep_]
        for token in lst_children:
            if token.dep_ in dep_type:
                couple_lst.append([other, token])


def get_couple_seq_if_exist(lst_children):
    dep_to_seq_lst = []
    for child in lst_children:
        if child.dep_ in dep_to_seq:
            dep_to_seq_lst.append(child)
    remove_lst = []
    couple_seq_lst = []
    for dep_child in dep_to_seq_lst:
        dep_type = couple_to_seq[dep_child.dep_]
        remove_lst_temp = []
        for token in lst_children:
            if token.dep_ in dep_type:
                couple_seq_lst.append([dep_child, token])
                remove_lst_temp = [dep_child, token]
                break
        if remove_lst_temp:
            for token in remove_lst_temp:
                lst_children.remove(token)
            remove_lst.extend(remove_lst_temp)
    return couple_seq_lst


def get_appos_if_exist(lst_children):
    appos_child_lst = []
    for child in lst_children:
        if child.dep_ == 'appos':
            appos_child_lst.append(child)
    if appos_child_lst:
        for child in lst_children:
            if child.dep_ == 'dep':
                appos_child_lst.append(child)
        lst_children_copy = lst_children.copy()
        for child in lst_children_copy:
            if child in appos_child_lst:
                lst_children.remove(child)
        if len(appos_child_lst) == 1:
            if appos_child_lst[0].pos_ == 'PROPN':
                return []
    return appos_child_lst


def get_conj_if_cc_exist(lst_children):
    cc_is_exist = False
    cc_child_lst = []
    for child in lst_children:
        if child.dep_ == 'cc' or child.dep_ == 'punct' and child.text == ',':
            cc_child_lst.append(child)
            cc_is_exist = True
    if cc_is_exist:
        children_dep = valid_expansion_utils.get_token_by_dep(lst_children, 'conj')
        if children_dep is []:
            children_dep = valid_expansion_utils.get_token_by_dep(lst_children, 'nmod')
        children_dep.sort(key=lambda x: x.i)
        cc_child_lst.sort(key=lambda x: x.i)
        tokens_to_skip = cc_child_lst.copy()
        conj_tokens_lst = []
        for cc_child in cc_child_lst:
            for child in children_dep:
                if child.i > cc_child.i:
                    tokens_to_skip.append(child)
                    conj_tokens_lst.append([cc_child, child])
                    children_dep.remove(child)
                    break
        for token in tokens_to_skip:
            lst_children.remove(token)
        return conj_tokens_lst
    return []


def get_seq_deps(lst_children):
    seq_dict = {}
    conj_tokens_lst = get_conj_if_cc_exist(lst_children)
    if conj_tokens_lst:
        seq_dict['conj'] = conj_tokens_lst
    couple_seq_lst = get_couple_seq_if_exist(lst_children)
    if couple_seq_lst:
        seq_dict['couple_seq'] = couple_seq_lst
    appos_child_lst = get_appos_if_exist(lst_children)
    if appos_child_lst:
        seq_dict['appos'] = appos_child_lst
    return seq_dict


def get_all_dominated_deps_from_lst(token, deps_collection):
    deps_collection.append(token)
    for child_token in token.children:
        get_all_dominated_deps_from_lst(child_token, deps_collection)


def set_couple_deps(seq_dict, boundary_np_to_the_left, sub_np_lst, head):
    for seq_type, seq_lst in seq_dict.items():
        if seq_type == 'appos':
            deps_collection = []
            for token in seq_lst:
                get_all_dominated_deps_from_lst(token, deps_collection)
            sub_np_lst.append(deps_collection)
            continue
        for seq in seq_lst:
            sub_np_lst_seq = []
            all_sub_of_sub = []
            for token in seq:
                sub_np_lst_token, lst_children = \
                    combine_tied_deps_recursively_and_combine_their_children(token, boundary_np_to_the_left)
                sub_np_lst_seq.extend(sub_np_lst_token)
                get_children_expansion(all_sub_of_sub, lst_children, boundary_np_to_the_left, head)
            if all_sub_of_sub:
                sub_np_lst_seq.append(all_sub_of_sub)
            sub_np_lst.append(sub_np_lst_seq)


def get_all_valid_sub_special(token, boundary_np_to_the_left):
    sub_np_lst, lst_children = combine_tied_deps_recursively_and_combine_their_children(token, boundary_np_to_the_left)
    complete_children = []
    seq_dict = get_seq_deps(lst_children)
    complete_occurrences = 0
    for child in lst_children:
        if child.text in stop_words:
            continue
        if child.dep_ in ['dobj', 'advcl', 'nmod']:  # 'cc', 'conj', 'aux', 'auxpass', 'cop', 'nsubjpass'
            all_sub_of_sub = get_all_valid_sub_np(child, boundary_np_to_the_left)
            if complete_occurrences > 0 and child.dep_ in ['nmod', 'advcl'] and len(all_sub_of_sub) > 1:
                new_sub_np_lst = []
                optional_lst = []
                for item in all_sub_of_sub:
                    if isinstance(item, list):
                        optional_lst.append(item)
                    else:
                        new_sub_np_lst.append(item)
                new_sub_np_lst.sort(key=lambda x: x.i)
                new_sub_np_lst = new_sub_np_lst + optional_lst
                if new_sub_np_lst[0].dep_ in ['case', 'mark']:
                    sub_np_lst = sub_np_lst + [new_sub_np_lst]
                    complete_occurrences += 1
                    continue
            sub_np_lst = sub_np_lst + all_sub_of_sub
            complete_occurrences += 1
        else:
            complete_children.append(child)
    if complete_occurrences > 1:
        new_sub_np_lst = []
        optional_lst = []
        for item in sub_np_lst:
            if isinstance(item, list):
                optional_lst.append(item)
            else:
                new_sub_np_lst.append(item)
        sub_np_lst = new_sub_np_lst + optional_lst
    sub_np_lst_couples = []
    set_couple_deps(seq_dict, boundary_np_to_the_left, sub_np_lst_couples, [])
    if sub_np_lst_couples:
        sub_np_lst.append(sub_np_lst_couples)
    for child in complete_children:
        all_sub_of_sub = get_all_valid_sub_np(child, boundary_np_to_the_left)
        sub_np_lst.append(all_sub_of_sub)
    if not sub_np_lst:
        return []
    return sub_np_lst


def get_follow_token(lst_children, token):
    for child in lst_children:
        if child.i == token.i + 1:
            return child
    return None


def get_children_expansion(sub_np_lst, lst_children, boundary_np_to_the_left, head):
    seq_dict = get_seq_deps(lst_children)
    tokens_to_skip = []
    for child in lst_children:
        if child in tokens_to_skip:
            continue
        if child.text in stop_words:
            continue
        is_follow_by_conj_token = False
        if child.i < len(child.doc) - 3 and child.doc[child.i + 1] in lst_children:
            if child.doc[child.i + 1].text in ['/', '-', ',']:
                is_follow_by_conj_token = True
        if child.text.endswith("-") or child.text.endswith("/") or is_follow_by_conj_token:
            follow_token = get_follow_token(lst_children, child)
            if not follow_token:
                print("follow token not found")
            else:
                seq_tokens = [child, follow_token]
                if is_follow_by_conj_token:
                    follow_conj_token = get_follow_token(lst_children, follow_token)
                    if follow_conj_token:
                        seq_tokens.append(follow_conj_token)
                        tokens_to_skip.append(follow_conj_token)
                seq_dict['couple_seq'] = seq_dict.get('couple_seq', [])
                seq_dict['couple_seq'].append(seq_tokens)
                tokens_to_skip.append(follow_token)
                continue
        sub_np = []
        if child.dep_ in dep_type_optional:
            all_sub_of_sub = get_all_valid_sub_np(child, boundary_np_to_the_left)
            sub_np.append(all_sub_of_sub)
            if sub_np:
                sub_np_lst.extend(sub_np)
        elif child.dep_ in combined_with:
            all_sub_of_sub = get_all_valid_sub_special(child, boundary_np_to_the_left)
            if all_sub_of_sub:
                sub_np.append(all_sub_of_sub)
            if sub_np:
                sub_np_lst.extend(sub_np)
        else:
            if child.dep_ not in ['nsubj']:
                print(child.dep_)
    set_couple_deps(seq_dict, boundary_np_to_the_left, sub_np_lst, head)


def get_all_valid_sub_np(head, boundary_np_to_the_left):
    sub_np_lst, lst_children = combine_tied_deps_recursively_and_combine_their_children(head, boundary_np_to_the_left)
    get_children_expansion(sub_np_lst, lst_children, boundary_np_to_the_left, head)
    return sub_np_lst


def get_score(np, head_word):
    val = 0
    for token in np:
        if token == head_word:
            val += 1
            continue
        if token.dep_ in neglect_deps or token.lemma_ in stop_words or token.text == '-':
            continue
        val += 1
    return val


def check_span_validity(np):
    hyphen_lst = []
    idx_lst = []
    for token in np:
        if token.text == '-':
            hyphen_lst.append(token)
            continue
        idx_lst.append(token.i)
    if hyphen_lst:
        for hyphen in hyphen_lst:
            if hyphen.i + 1 in idx_lst and hyphen.i - 1 in idx_lst:
                continue
            else:
                return False
        return True
    return True


def get_all_expansions_of_span_from_lst(span_lst):
    sub_np_final_lst_collection = []
    for head_word, sentence_dep_graph, sentence in span_lst:
        noun_phrase, head_word_in_np_index, boundary_np_to_the_left = valid_expansion_utils.get_np_boundary(
            head_word.i,
            sentence_dep_graph)
        if noun_phrase is None:
            continue
        if len(noun_phrase) > 15:
            continue
        all_valid_sub_np = get_all_valid_sub_np(noun_phrase[head_word_in_np_index],
                                                boundary_np_to_the_left)
        sub_np_final_lst = valid_expansion_utils.from_lst_to_sequence(all_valid_sub_np)
        sub_np_final_spans = []
        for np in sub_np_final_lst:
            np.sort(key=lambda x: x.i)
            is_valid_np = check_span_validity(np)
            if not is_valid_np:
                continue
            val = get_score(np, head_word)
            sub_np_final_spans.append((np, val))
        sub_np_final_spans.sort(key=lambda x: len(x[0]), reverse=True)
        if not sub_np_final_spans:
            continue
        sub_np_final_lst_collection.append((sub_np_final_spans[0][0], head_word, sub_np_final_spans, sentence))
    return sub_np_final_lst_collection
