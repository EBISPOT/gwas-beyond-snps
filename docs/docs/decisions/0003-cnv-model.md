# Define Copy Number Variant GWAS data model

Date: 2026-01-26

## Status

Proposed

## Context

We'd like to ingest copy number variant (CNV) GWAS analyses into the GWAS
Catalog.

There are no standard schemas or recommended data formats for authors. Data are
submitted and only hosted on the GWAS Catalog FTP without any ingest processes,
e.g. https://www.ebi.ac.uk/gwas/publications/36779085

CNV submissions are becoming more common from 2025, and we need a way to model
and ingest this data so it can be queried, validated, and integrated alongside
SNP-based GWAS.

## Decision

### Mandatory fields

| Field             | Validation notes                                                                         |
|-------------------|------------------------------------------------------------------------------------------|
| chromosome        | Integer; must match GWAS-SSF standard (1-22, X = 23, Y = 24, MT = 25)                    |
| base_pair_start   | Positive integer; genomic start co-ordinate (co-ordinate system set in metadata)         |
| base_pair_end     | Positive integer; genomic end co-ordinate; must satisfy `end ≥ start`                    |
| p_value           | Float in (0,1]; mutually exclusive with `neg_log10_p_value`                              |
| neg_log10_p_value | Float ≥ 0; mutually exclusive with `p_value`                                             |
| model_type        | Controlled vocabulary for association model; distinguishes multiple models within a file |

### Optional fields

| Field | Validation notes                                                                     |
|-------|--------------------------------------------------------------------------------------|
| n     | Optional positive integer; number of samples contributing to this association record |

### Conditional fields

| Field                     | Validation notes                               |
|---------------------------|------------------------------------------------|
| beta                      | A primary effect size must be indicated; float |
| odds_ratio                | A primary effect size must be indicated; float |
| z_score                   | A primary effect size must be indicated; float |
| standard_error            | Required if `beta` is provided; float          |
| confidence_interval_lower | Required if `odds_ratio` is provided; float    |
| confidence_interval_upper | Required if `odds_ratio` is provided; float    |

A primary effect size must be indicated (e.g. beta, z-score, odds ratio) if multiple effect size types are specified. At least one effect size is mandatory.

Z-score doesn't require a measure of uncertainty (standard error / ci_upper / ci_lower).

### Custom fields

Authors may choose to include a reasonable number of custom fields, which will
be included after mandatory and optional fields.

### Computed fields

* CNV identifier `${chromosome}:${start}:${end}:${assembly}`

### Metadata

No structural changes are required to the GWAS Catalog metadata schema, except
adding an enumerated and mutually exclusive flag to indicate the type of genetic
variation being studied (e.g. gene-based, SNP, CNV). Fields like genome assembly
are defined in the metadata schema.

Files are expected to contain at least 10,000 rows pre-QC; smaller files may be
rejected or flagged for review. The first proposed limit was 100,000 but this has
been revised down in response to submitter feedback (estimated ~20,000 CNVs present in
human genomes, many rare variants will be excluded from any GWAS tests). Our aim is to
identify a heuristic to indicate that a genome-wide analysis has taken place and this
number may evolve over time.

### Source of truth

The canonical representation of the data model is the Pydantic model defined in
this repository.

Required context will be injected during validation from the
GWAS Catalog metadata schema as needed (e.g. assembly, co-ordinate system).

Documentation will be generated from the annotated Pydantic model.

### Output format

The model is responsible for defining output fields in a standardised way,
like gwas-ssf. Custom fields are appended after the standard fields.

If `chromosome` and `base_pair_start` are provided, output must be sorted
by these fields.

## Consequences

This data model intentionally introduces a divergence from SNP-based summary
statistics: multiple genetic association models are permitted in a single
summary statistics file. Traditionally, authors of SNP-based GWAS may run
multiple models but typically submit results from a single “best” model.

We discussed changing SNP-based summary statistics to support a model type
field, but this would break existing consumers of SNP-based data. We therefore
decided to introduce this field only for CNVs. This approach enables ingestion
and harmonisation of CNV GWAS data while avoiding impact on existing SNP-based
summary statistics consumers.

In the future the GWAS Catalog may choose to enforce one model per CNV summary
statistics file.

The data model is designed to allow additional fields in the future to respond
to evolving community requirements. However, some future additions may not be
backwards-compatible. Consumers of the data should account for potential schema
evolution when designing pipelines.
