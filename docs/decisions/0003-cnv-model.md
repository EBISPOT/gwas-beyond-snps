# Copy number variant (CNV) GWAS data model

Date: 2026-01-26

## Status

Proposed

## Context

We'd like to ingest copy number variant (CNV) GWAS analyses into the GWAS
Catalog.

There are no standard schemas or recommended data formats for authors. Data are
submitted and only hosted on the GWAS Catalog FTP without any ingest processes,
e.g. <https://www.ebi.ac.uk/gwas/publications/36779085>

CNV submissions are becoming more common from 2025, and we need a way to model
and ingest this data so it can be queried, validated, and integrated alongside
SNP-based GWAS.

## Decision

At a minimum, a CNV GWAS record must include:

* [MANDATORY] Chromosome
* [MANDATORY] Start position (metadata defines coordinate system)
* [MANDATORY] End position (metadata defines coordinate system)
* [MANDATORY] p-value or negative log10 p-value
* [MANDATORY] Direction in which the CNV affects a trait (e.g., positive,
  negative, ambiguous)
* [MANDATORY] Effect allele, which can be used to define copy number state
  * Default value is "CNV" like [Ensembl VEP annotations](https://ensembl.org/info/docs/tools/vep/vep_formats.html#sv))
  * Copy numbers are defined as CN3, CN=3, etc (see VEP annotations)
* [MANDATORY] Genetic association model type (e.g., additive, dominant,
  recessive, dosage-sensitive)

Optional but recommended fields include:

* [OPTIONAL] per-CNV sample size

Authors may choose to include a reasonable number of custom fields, which will
be included after mandatory and optional fields.

Some additional fields will be computed, including:

* CNV identifiers `${chromosome}:${start}:${end}:${assembly}`
* CNV length (end - start) in bases

No changes are required to the GWAS Catalog metadata schema, except adding an
enumerated and mutually exclusive flag to indicate the type of genetic
variation being studied (e.g. gene-based, SNP, CNV). Fields like genome assembly
are defined in the metadata schema.

The canonical representation of the data model is the Pydantic model defined in
this repository. Required context will be injected during validation from the
GWAS Catalog metadata schema as needed (e.g. assembly, co-ordinate system).

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
