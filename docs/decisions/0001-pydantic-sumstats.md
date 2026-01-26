# Adopting Pydantic v2 for summary statistics data models

Date: 2026-01-23

## Status

Proposed

## Context

We'd like to ingest gene-based GWAS and Copy Number Variant (CNV) GWAS summary
statistics into the GWAS Catalog. Currently, authors can submit this data for
storage on the EMBL-EBI FTP server but no schemas or structure is requested or
enforced.

A reasonable first step is to create a client-side data validation
application and library. Users are requested to run this program on their
computer to validate and format their data before GWAS Catalog submission.

Existing GWAS Catalog validation applications use a variety of Python frameworks
to define acceptable data models and validate data, including the standard
library, pandas-schema, and Pydantic v1. Methods of validating a field are often
redefined across different frameworks (redundant code).

Ideally we should have a unified library of data models implemented in a single
modern framework.

## Decision

Summary statistics data models will now be defined in Pydantic v2 models in a new
repository. The Pydantic data model should be considered the canonical
reference. Documentation should be generated from code and annotated.

Pydantic v2 has better support for annotated types and typing, significantly
improved performance (core written in Rust), and offers long-term support and
alignment with modern Python practices.

Domain constraints are encoded
[in types rather than imperative validators](https://lexi-lambda.github.io/blog/2019/11/05/parse-don-t-validate).

Validation will be implemented using modern Python techniques, including:

* Fields (e.g. p-value) must be defined as annotated types
* Summary statistics data models are composed of custom types
* [ABCs](https://docs.python.org/3/library/abc.html) are used to define public interfaces for consumers of data models (e.g. validation CLI)
* Validation is split into a library and CLI application using
  [the uv workspace pattern](https://docs.astral.sh/uv/concepts/projects/workspaces/)

This package will initially implement data models for gene-based and CNV data only.

## Consequences

* A shared library will improve consistency and quality across validation tools
* Data models are reusable and modular, simplifying adding new submission
  formats
* The onboarding experience will be improved
* SNPs will be validated separately to gene-based and CNV data and will require
  users to run a different application
* Creating and maintaining a new Python repository is additional work and could
  confuse end users
* Migrating SNP validation into this repository will require significant work
  including updating or deprecating any applications that depend on
  gwas-sumstat-tools
