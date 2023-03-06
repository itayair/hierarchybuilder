from quantulum3 import parser
from hierarchybuilder.combine_spans import utils as combine_spans_utils


def from_quantity_to_range(quantity_lst):
    quantity_lst.sort()
    if len(quantity_lst) == 1:
        return str(quantity_lst[0])
    max_val = max(quantity_lst)
    min_val = min(quantity_lst)
    range_number = str(min_val) + "-" + str(max_val)
    return range_number


def normalized_quantity_node(node):
    unit_to_quantity_dict = {}
    span_to_surface_dict = {}
    surface_to_unit = {}
    valid_span_lst = set()
    for span in node.span_lst:
        try:
            quants = parser.parse(span)
        except:
            continue
        for quant in quants:
            if quant.unit.name and quant.unit.name != 'dimensionless':
                valid_span_lst.add(span)
                span_to_surface_dict[span] = span_to_surface_dict.get(span, set())
                span_to_surface_dict[span].add(quant.surface)
                surface_to_unit[quant.surface] = quant.unit.name
                unit_to_quantity_dict[quant.unit.name] = unit_to_quantity_dict.get(quant.unit.name, set())
                unit_to_quantity_dict[quant.unit.name].add(quant.value)
    is_valid_normalized = False
    for explicit_, quantity in unit_to_quantity_dict.items():
        if len(quantity) > 0.5 * len(node.span_lst) and len(quantity) > 1:
            is_valid_normalized = True
            break
    if is_valid_normalized:
        most_frequent_span = combine_spans_utils.get_most_frequent_span(valid_span_lst)
        surface_lst = span_to_surface_dict[most_frequent_span]
        for surface in surface_lst:
            unit = surface_to_unit[surface]
            quantity_lst = unit_to_quantity_dict[unit]
            range_number = from_quantity_to_range(list(quantity_lst))
            normalized_quantity = range_number + " " + unit
            most_frequent_span = most_frequent_span.replace(surface, normalized_quantity)
    else:
        most_frequent_span = combine_spans_utils.get_most_frequent_span(node.span_lst)
    return most_frequent_span


def get_quantity_for_nodes(object_lst, visited=set()):
    for node in object_lst:
        if node in visited:
            continue
        normalized_quantity_node(node)
        visited.add(node)
        get_quantity_for_nodes(node.children, visited)
