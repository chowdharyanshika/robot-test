#!/usr/bin/env python3
"""Build check_borrowed.rq from borrowed_terms.tsv.

The query looks up every borrowed term in the downloaded ontologies and reports:
  NOT FOUND  - the term does not exist (typo or wrong ID)
  RETIRED    - the term exists but is marked obsolete (owl:deprecated true)
  ok         - the term exists and is current
"""
import csv

with open("borrowed_terms.tsv") as f:
    rows = list(csv.DictReader(f, delimiter="\t"))

iris = [r["iri"] for r in rows]  # skip the "other" ones

values = "\n    ".join(f"<{iri}>" for iri in iris)

query = f"""PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl:  <http://www.w3.org/2002/07/owl#>
PREFIX obo:  <http://purl.obolibrary.org/obo/>

SELECT ?status ?term ?label ?replaced_by WHERE {{
  VALUES ?term {{
    {values}
  }}
  OPTIONAL {{ ?term rdfs:label ?label }}
  OPTIONAL {{ ?term owl:deprecated ?dep }}
  OPTIONAL {{ ?term obo:IAO_0100001 ?replaced_by }}
  BIND(IF(!BOUND(?label), "NOT FOUND",
       IF(BOUND(?dep) && STR(?dep) = "true", "RETIRED", "ok")) AS ?status)
}}
ORDER BY ?status ?term
"""

with open("check_borrowed.rq", "w") as out:
    out.write(query)

print(f"Wrote check_borrowed.rq with {len(iris)} terms.")
