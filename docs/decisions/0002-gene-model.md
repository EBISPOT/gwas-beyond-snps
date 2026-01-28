# Define gene-based GWAS summary statistics data model

Date: 2026-01-26

## Status

Proposed

## Context

We'd like to ingest gene-based GWAS analyses into the GWAS Catalog.

There are no standard schemas or recommended data formats for authors. Data are
submitted and only hosted on the GWAS Catalog FTP without any ingest processes.
This prevents consistent validation, indexing, and downstream reuse.

As of 2025-04-01, 5,648 summary statistics files were identified by GWAS Catalog
curators as including gene-based analyses. A review of these files found
inconsistent data structure and field names. After checking shared fields and
common data patterns a data model was proposed.

## Decision

| Field             | Required?   | Validation notes                                                                     |
|-------------------|-------------|--------------------------------------------------------------------------------------|
| ensembl_gene_id   | Conditional | At least one gene identifier MUST be provided; preferred ID format `ENSG00000000000` |
| hgnc_symbol       | Conditional | Required if `ensembl_gene_id` is not provided; string, official HGNC symbol          |
| p_value           | Conditional | Float in (0,1]; mutually exclusive with `neg_log10_p_value`                          |
| neg_log10_p_value | Conditional | Float ≥ 0; mutually exclusive with `p_value`                                         |
| beta              | Conditional | At most one of `beta`, `odds_ratio`, or `z_score` may be provided; float             |
| standard_error    | Conditional | Required if `beta` is provided; float                                                |
| odds_ratio        | Conditional | At most one of `beta`, `odds_ratio`, or `z_score` may be provided; float             |
| ci_lower          | Conditional | Required if `odds_ratio` is provided; float                                          |
| ci_upper          | Conditional | Required if `odds_ratio` is provided; float                                          |
| z_score           | Conditional | At most one of `beta`, `odds_ratio`, or `z_score` may be provided; float             |
| chromosome        | Conditional | Integer; must match GWAS-SSF standard (1-22, X = 23, Y = 24, MT = 25)                |
| start             | Conditional | Positive integer; required if `chromosome` is provided                               |
| end               | Conditional | Positive integer; required if `chromosome` is provided                               |
| sample_size       | Optional    | Positive integer; number of samples contributing to this association record          |

The GWAS Catalog Scientific Advisory Board recommended making effect size an
optional field for gene-based analyses. Many existing studies do not include a
measure of effect size.

Authors may choose to include a reasonable number of custom fields, which will
be included after mandatory and optional fields.

No changes are required to the GWAS Catalog metadata schema, except adding an
enumerated and mutually exclusive flag to indicate the type of genetic
variation being studied (e.g. gene-based, SNP, CNV). Fields like genome assembly
are defined in the metadata schema.

The canonical representation of the data model is the Pydantic model defined in
this repository. Required context will be injected during validation from the
GWAS Catalog metadata schema as needed (e.g. assembly, co-ordinate system).

Files are expected to contain at least 10,000 rows; smaller files may be
rejected or flagged for review. This heuristic is based on a survey of existing
submissions which found a minimum of 13,674 and a maximum of 15,578,185 rows.
Given that there are roughly 20,000 protein-coding genes in the human genome,
and that the GWAS Catalog accepts only genome-wide (not targeted) analyses,
substantially smaller files are unlikely to represent valid gene-based GWAS
results.

## Consequences

Currently most gene-based GWAS authors share lots of data with the GWAS Catalog,
although this information is unstructured.

After integrating this model with GWAS Catalog data ingest processes, authors
may choose to only share gene names and p-values with the GWAS Catalog. This may
reduce per-record completeness.

However, user feedback indicates the minimum data has significant value, and
other resources collect this kind of data (e.g. OpenTargets).

We will accept and monitor the risk of lower completeness in exchange for
consistency, searchability, and interoperability.
