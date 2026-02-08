"""
Deep scientific knowledge graph for cell therapy adverse event pathophysiology.

This package encodes the mechanistic biology of cell therapy toxicities as a
queryable directed graph, linking therapy actions through signaling cascades
to clinical adverse events. Every factual assertion is backed by PubMed
references.

Modules:
    references   -- Citation database (PubMed IDs, key findings)
    cell_types   -- Cell populations and their roles in AE pathogenesis
    molecular_targets -- Druggable targets and their pathway relationships
    pathways     -- Signaling pathways as directed graphs
    mechanisms   -- AE mechanism chains (therapy -> target -> cascade -> AE)
    graph_queries -- Query API over the knowledge graph
"""
