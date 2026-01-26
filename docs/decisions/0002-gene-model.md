# Gene-based GWAS data model

Date: 2026-01-26

## Status

Proposed

## Context

We'd like to ingest gene-based GWAS analyses into the GWAS Catalog.

There are no standard schemas or recommended data formats for authors. Data are
submitted and only hosted on the GWAS Catalog FTP without any ingest processes.

In 2025-04-01 5,648 summary statistic files were identified by GWAS Catalog
curators as including gene-based analyses. A review of these files found
inconsistent data structure and field names. After checking shared fields and
common data patterns a data model was proposed.

## Decision

At a minimum, a gene-based GWAS record must include:

* [MANDATORY] A gene name encoded as a HGNC symbol or Ensembl Gene ID
* [MANDATORY] A p-value or negative log10 p-value (mutually exclusive)

The GWAS Catalog Scientific Advisory Board recommended making effect size an
optional field for gene-based analyses. Many existing studies do not include a
measure of effect size.

Optional but recommended fields include:

* [OPTIONAL] The start and end of the gene should be recorded in base pairs
  * [MANDATORY] If gene location is specified, chromosome must also be specified
* [OPTIONAL] A primary effect type should be specified. Valid effect types
  include z-score, odds ratio, or beta
  * [MANDATORY] A confidence interval must be provided for odds ratio
  * [MANDATORY] If beta is provided, standard error must be provided
  * No uncertainty measurement is required for z-score

Authors may choose to include a reasonable number of custom fields, which will
be included after mandatory and optional fields.

No changes are required to the GWAS Catalog metadata schema, except adding an
enumerated and mutually exclusive flag to indicate the type of genetic
variation being studied (e.g. gene-based, SNP, CNV). Fields like genome assembly
are defined in the metadata schema.

The canonical representation of the data model is the Pydantic model defined in
this repository. Required context will be injected during validation from the
GWAS Catalog metadata schema as needed (e.g. assembly, co-ordinate system).

## Consequences

Currently most gene-based GWAS authors share lots of data with the GWAS Catalog,
although this information is unstructured.

After integrating this model with GWAS Catalog data ingest processes, authors
may choose to only share gene names and p-values with the GWAS Catalog. This
would reduce the quality of data submissions.

However, user feedback indicates the minimum data has significant value, and
other resources collect this kind of data (e.g. OpenTargets).

We will accept and monitor the risk of lower completeness in exchange for
consistency, searchability, and interoperability.
