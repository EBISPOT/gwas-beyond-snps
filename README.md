# gwas-pysumstats

> [!TIP]
>  If you've stumbled upon this repository you should almost certainly look at [`gwas-sumstats-tools`](https://github.com/ebispot/gwas-sumstats-tools) instead
 
This repository contains Python packages designed to help you prepare your GWAS summary statistics for submission to the [GWAS Catalog](https://ebi.ac.uk). This tool streamlines the process of preparing your data in the required format.

> [!WARNING]
> This is a **work in progress**. The current version of the package is under active development and may undergo significant changes. The API and functionality are not yet stable, and breaking changes are expected.

## What kind of data are supported?

| Type of genetic variant              | Supported                                                                     |
|--------------------------------------|-------------------------------------------------------------------------------|
| Single nucleotide polymorphism (SNP) | ❌, see [`gwas-sumstats-tools`](https://github.com/ebispot/gwas-sumstats-tools) |
| Copy number variant (CNV)            | ✅                                                                            |
| Gene                                 | ✅                                                                            |


## Developer notes 

This repository is a uv workspace containing:

- sumstatlib: shared validation models
- sumstatapp: a data validation application which uses sumstatlib internally

The workspace root is not a Python package.