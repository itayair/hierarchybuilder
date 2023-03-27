# Hierarchy Builder package

The `Hierarchy Builder` Python package is a tool for organizing and visualizing a large collection of related textual 
strings in a hierarchical DAG structure for exploratory search. Currently, the package works especially for biomedical data, 
but in the future, it will be expanded to support other domains. 
This will be achieved by allowing users to add their own dictionaries and taxonomic relations datasets for a specific 
domain.
## Installations
To install the `Hierarchy Builder` package, please follow the steps below:
1. Install the package via pip:
```bash
pip install hierarchybuilder
```
2. Install the following dependency graph parser:
```bash
pip install https://storage.googleapis.com/en_ud_model/en_ud_model_sm-2.0.0.tar.gz
```
## Optional Tools
You can download the UMLS data, which is a valuable resource for biomedical text analysis:
* MRCONSO.RRF - synonyms dictionary
* MRREL.RRF - taxonomic relations dataset

## Usage
To use the `Hierarchy Builder` package, follow these steps:

### UMLS
You have the option to use UMLS to improve the performance for the BIO domain. 
You need to run the UMLS server first, as follows (this process takes a while until it is loaded):

```python

from hierarchybuilder.UMLS import umls_services
# The default values are:
# host="127.0.0.1", port=5000, umls_relations_file_path='../UMLS_data/MRREL.RRF', 
# umls_synonymous_file_path='../UMLS_data/MRCONSO.RRF'
umls_services.create_umls_servercreate_umls_server()
```

### Run hierarchy builder

```python
import hierarchybuilder.hierarchy_builder as hierarchy_builder
Examples = [("sentence1", "span in sentence1"), ("sentence2", "span in the sentence2"), ...]
# The default values are:
# entries_number=50, ignore_words=None, device="", umls_host="127.0.0.1", usml_port=5000, has_umls_server=False
hierarchy_builder.hierarchy_builder(examples=Examples, entries_number=50)
```
To use the `hierarchy_builder` function, provide a list of sentence and span tuples as input via the `examples` parameter. 
The `entries_number` parameter determines the number of entries that will be displayed at the top level of the resulting DAG. 
The `ignore_words` parameter is a list of words that should be excluded from the top level entries, 
usually words that appear in the query.
The `has_umls_server` parameter indicates if the user uses UMLS or not.
The `umls_host` and `usml_port` parameters are for the UMLS server port
The package will use these examples to generate a DAG structure that organizes and displays a large collection of related 
textual strings in a hierarchical form. 

## Output

The output of the hierarchy_builder function is a JSON file that represents the hierarchical structure of the input sentences and spans. 
The structure is defined as a Directed Acyclic Graph (DAG) where each node represents a concept. 
Each node in the DAG is defined by the following properties:
* Label that represent the concept of the node
* `aliases` - Aliases of the concept
* `sources_number` - number of the input spans that represented by the node
* `aliases_sources_number` - number of input spans that are fully represented by the label (the full noun phrase is one of the aliases)
* `sentences` - the sentences of the input spans that are fully represented by the node(as defined in "aliases_sources_number")
* `children` - Nodes that are defined by more specific concepts
For example, a node in the JSON file might look like this:
```json
{
    "drug": 
            {
                "aliases": ["drug", "agent", "drugs", "these agents", "the other agents", "this drug", "these drugs", "the drug"],
                "sources_number": 32,
                "aliases_sources_number": 8,
                "sentences": ["..."],
                "children": {"label_child_1":"..."}
            }
}
```
In this example, the label of the node is `drug`, the aliases of `drag` are `agent`, `drugs`, `these agents`, `the other agents` etc.
The number of sources that represented by `drug` is `32`, and the number of sources that are fully represented by one of the aliases is 8.

## Conclusion
The `Hierarchy Builder` package is a useful tool for organizing and exploring large collections of related textual strings. 
The package provides an easy-to-use interface to generate a DAG structure that organizes and displays related textual 
strings in a hierarchical structure. The package is especially useful for exploring biomedical data, 
but it can be extended to support other domains as well by allowing users to add their own dictionaries and taxonomic relations datasets


