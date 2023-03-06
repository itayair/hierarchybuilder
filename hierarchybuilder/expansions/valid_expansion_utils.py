import itertools

noun_tags_lst = ['NN', 'NNS', 'WP', 'PRP', 'NNP', 'NNPS']


def get_head_of_span(span):
    head = None
    for child in span:
        if child.head == child:
            return child
        if child.head not in span:
            head = child
    return head


def from_children_to_list(children):
    lst_children = []
    for token in children:
        lst_children.append(token)
    return lst_children


def get_token_by_dep(lst_children, dep_type):
    lst_tokens = []
    for child in lst_children:
        if child.dep_ == dep_type:
            lst_tokens.append(child)
    return lst_tokens


def powerset(iterable):
    return itertools.chain.from_iterable(itertools.combinations(iterable, r) for r in range(len(iterable) + 1))


def from_lst_to_sequence(sub_np_lst):
    sub_np_of_child_lst_final = []
    current_lst = []
    if isinstance(sub_np_lst[0], list):
        if len(sub_np_lst) == 1:
            return from_lst_to_sequence(sub_np_lst[0])
        sub_np_of_child_lst = []
        for child in sub_np_lst:
            sub_np_of_child = from_lst_to_sequence(child)
            sub_np_of_child_lst.append(sub_np_of_child)
    else:
        collect_to_lst = []
        slice_index = 0
        for item in sub_np_lst:
            if isinstance(item, list):
                break
            collect_to_lst.append(item)
            slice_index += 1
        current_lst.extend(collect_to_lst)
        if len(sub_np_lst) == 1:
            return [current_lst]
        sub_np_of_child_lst = []
        for child in sub_np_lst[slice_index:]:
            sub_np_of_child = from_lst_to_sequence(child)
            sub_np_of_child_lst.append(sub_np_of_child)
    result_list = list(powerset(sub_np_of_child_lst))
    for item in result_list:
        for element in itertools.product(*item):
            if item == ():
                continue
            lst_temp = []
            for token in element:
                lst_temp.extend(token)
            sub_np_of_child_lst_final.append(lst_temp)
    if current_lst:
        for lst in sub_np_of_child_lst_final:
            lst.extend(current_lst)
        sub_np_of_child_lst_final.append(current_lst)
    return sub_np_of_child_lst_final


def is_np_child_head(head_word, word):
    if word.head == head_word:
        return True
    if word == word.head:
        return False
    return is_np_child_head(head_word, word.head)


def get_np_boundary(head_word_index, sentence_dep_graph):
    head_word = sentence_dep_graph[head_word_index]
    if head_word.tag_ not in noun_tags_lst:
        return None, None, None
    boundary_np_to_the_left = head_word_index
    # np's boundary to the left
    for i in range(1, head_word_index + 1):
        current_index = head_word_index - i
        word = sentence_dep_graph[current_index]
        if is_np_child_head(head_word, word):
            boundary_np_to_the_left = current_index
            continue
        break
    # np's boundary to the right
    boundary_np_to_the_right = head_word_index
    for i in range(head_word_index + 1, len(sentence_dep_graph)):
        word = sentence_dep_graph[i]
        if is_np_child_head(head_word, word):
            boundary_np_to_the_right = i
            continue
        break
    while sentence_dep_graph[boundary_np_to_the_left].dep_ in ['case', 'mark'] or sentence_dep_graph[boundary_np_to_the_left].tag_ == 'IN':
        boundary_np_to_the_left += 1
    return sentence_dep_graph[
           boundary_np_to_the_left:boundary_np_to_the_right + 1], head_word_index - boundary_np_to_the_left, boundary_np_to_the_left


def get_tokens_as_span(tokens):
    span = ""
    idx = 0
    for token in tokens:
        if idx == 0 and token.tag_ in ['IN', 'TO']:
            continue
        if idx != 0 and token.text not in [',', '(', ')', '.', '/'] and not not_space:
            span += ' '
        span += token.text.lower()
        idx += 1
        if token.text in ['(''/']:
            not_space = True
            continue
        not_space = False
    return span


def write_to_file_dict_counter(sub_np_final_lst_collection, output_file):
    with open(output_file, 'w', encoding='utf-8') as f:
        counter = 0
        for sub_np_final_lst in sub_np_final_lst_collection:
            lst_to_check_duplication = []
            for tokens in sub_np_final_lst:
                span = get_tokens_as_span(tokens)
                if span in lst_to_check_duplication:
                    print(span)
                    counter += 1
                else:
                    lst_to_check_duplication.append(span)
                f.write(span)
                f.write('\n')
            f.write('\n')
        print("Num of duplication:", counter)
