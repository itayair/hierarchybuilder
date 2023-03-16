# Hierarchy Builder package

The 'Hierarchy Builder' Python package is a tool for organizing and visualizing a large collection of related textual strings in a hierarchical DAG structure for exploratory search. Currently, the package works with biomedical data, but in the near future, it will be expanded to support other domains. This will be achieved by allowing users to add their own dictionaries and taxonomic relations datasets for a specific domain or alternatively, by supporting redundant usage of UMLS for different domains.
## Installations
To install the 'Hierarchy Builder' package, please follow the steps below:
1. Install the package via pip:
```bash
pip install hierarchybuilder
```
2. Install the following dependency graph parser:
```bash
pip install https://storage.googleapis.com/en_ud_model/en_ud_model_sm-2.0.0.tar.gz
```
## Additional requirements
Download the UMLS data:
* MRCONSO.RRF - synonyms dictionary
* MRREL.RRF - taxonomic relations dataset

## Usage
To use the 'Hierarchy Builder' package, you need to run the UMLS server as follows:

```python

from hierarchybuilder.UMLS import umls_services
# The default values are:
# host="127.0.0.1", port=5000, umls_relations_file_path='../UMLS_data/MRREL.RRF', 
# umls_synonymous_file_path='../UMLS_data/MRCONSO.RRF'
umls_services.create_umls_servercreate_umls_server()
```
Then, from another file, you can use the 'Hierarchy Builder' as follows:
```python
import hierarchybuilder.hierarchy_builder as hierarchy_builder
# The default values are:
# output_file_name='output', entries_number=50, ignore_words=None, device="", 
# host="127.0.0.1", port=5000
Examples = [("sentence1", "span in sentence1"), ("sentence2", "span in the sentence2"), ...]
hierarchy_builder.hierarchy_builder(examples=Examples)
```
To use the `hierarchy_builder` function, provide a list of sentence and span tuples as input via the `examples` parameter. 
The `entries_number` parameter determines the number of entries that will be displayed at the top level of the resulting DAG. 
The `ignore_words` parameter is a list of words that should be excluded from the top level entries, 
usually words that appear in the query.
The package will use these examples to generate a DAG structure that organizes and displays a large collection of related 
textual strings in a hierarchical form.
The output of the 'Hierarchy Builder' package is a JSON file that organizes the data in the following way:
* Each node in the DAG is represented by a list of all the sub-spans that are found in the input as synonyms sorted by their frequencies in the input and concatenated with '|' separator between them.
* At the end of the string, there is also information about the number of input examples that appear in that form as the full noun phrase, and the number of the input examples that cover by them.
For example, a node in the JSON file might look like this:
```css
"common bile duct cancer | a malignancy in the common bile duct (2/ 5)"
```
This means that the concatenated spans appeared in the input 5 times, but in this form only 2 times (the other options are more specific forms).

Overall, the 'Hierarchy Builder' package is a powerful tool for organizing and exploring large collections of related textual strings.


