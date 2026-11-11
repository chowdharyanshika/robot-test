#!/usr/bin/env python3
"""List the borrowed ontology terms used in the project's Turtle files.

Run from the root of lod-pathways-community:
    python3 list_borrowed_terms.py

Writes borrowed_terms.tsv (one row per term, with the files that use it)
and prints a summary per ontology.
"""
import collections
import pathlib

from rdflib import Graph, URIRef
from rdflib.namespace import RDF

ROOT = pathlib.Path(".")
FILES = sorted((ROOT / "lod-pathways-community" /
"shape_constraints").rglob("*.ttl"))

OWN = "https://example.org/lod-pathways/"          # the project's own terms (lodp)
SKIP = ("http://www.w3.org/",                        # RDF, RDFS, OWL, XSD, SHACL, PROV
        "http://purl.org/dc/")                       # Dublin Core
# Namespaces whose terms count as borrowed even when they appear as plain values
ONTOLOGY_NS = ("http://purl.obolibrary.org/obo/",   # ECO, MS (PSI-MS), STATO, SWO, IAO, OBI, ...
               "http://semanticscience.org/resource/",  # SIO
               "http://edamontology.org/")           # EDAM


def to_curie(iri: str) -> str:
    """http://purl.obolibrary.org/obo/MS_1002955 -> MS:1002955"""
    if iri.startswith("http://purl.obolibrary.org/obo/"):
        local = iri.rsplit("/", 1)[1]
        if "_" in local:
            prefix, num = local.split("_", 1)
            return f"{prefix}:{num}"
    if iri.startswith("http://semanticscience.org/resource/"):
        return "sio:" + iri.rsplit("/", 1)[1]
    if iri.startswith("http://edamontology.org/"):
        return "edam:" + iri.rsplit("/", 1)[1]
    return iri


def ontology_of(curie: str) -> str:
    return curie.split(":", 1)[0] if ":" in curie and not curie.startswith("http") else "other"


def borrowed(node, is_shapes_file: bool) -> bool:
    if not isinstance(node, URIRef):
        return False
    s = str(node)
    if s.startswith(OWN) or s.startswith(SKIP):
        return False
    return is_shapes_file or s.startswith(ONTOLOGY_NS)


uses = collections.defaultdict(set)
for f in FILES:
    g = Graph()
    g.parse(f, format="turtle")
    rel = f.relative_to(ROOT).as_posix()
    is_shapes = "/shapes/" in rel or "/vocab/" in rel
    for s, p, o in g:
        candidates = [p, o] if p == RDF.type else [p, o, s]
        for node in candidates:
            if borrowed(node, is_shapes):
                uses[str(node)].add(rel)

rows = sorted((to_curie(iri), iri, sorted(files)) for iri, files in uses.items())

with open("borrowed_terms.tsv", "w") as out:
    out.write("curie\tiri\tused_in\n")
    for curie, iri, files in rows:
        out.write(f"{curie}\t{iri}\t{', '.join(files)}\n")

per_ontology = collections.Counter(ontology_of(c) for c, _, _ in rows)
print(f"Scanned {len(FILES)} Turtle files, found {len(rows)} borrowed terms.\n")
for ont, n in per_ontology.most_common():
    print(f"  {ont:10s} {n}")
print("\nFull list written to borrowed_terms.tsv")
