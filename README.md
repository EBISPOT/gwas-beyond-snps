# GWAS Catalog: Beyond SNPs

> [!TIP]
>  If you've stumbled upon this repository you should almost certainly look at [`gwas-sumstats-tools`](https://github.com/ebispot/gwas-sumstats-tools) instead
 
This Python monorepo contains packages and documentation designed to help users prepare non-SNP GWAS summary statistics for submission to the [GWAS Catalog](https://ebi.ac.uk).

> [!WARNING]
> This is a **work in progress**. The current version of the package is under active development and may undergo significant changes. The API and functionality are not yet stable, and breaking changes are expected.

## What kind of data are supported?

| Type of genetic variant              | Supported                                                                     |
|--------------------------------------|-------------------------------------------------------------------------------|
| Single nucleotide polymorphism (SNP) | ❌, see [`gwas-sumstats-tools`](https://github.com/ebispot/gwas-sumstats-tools) |
| Copy number variant (CNV)            | ✅                                                                            |
| Gene                                 | ✅                                                                            |


## Developer notes 

This repository is a [`uv`](https://docs.astral.sh/uv/) workspace containing two Python packages:

- `sumstatlib`: [Pydantic models and validation public interfaces](sumstatlib)
- `sumstatapp`: data validation applications which uses sumstatlib internally, containing two deployment approaches:
  - A [Pyodide](https://github.com/pyodide/pyodide) web application, [responsible for browser-based data validation](src/gwascatalog/sumstatapp/web)
  - A [standard CLI for bulk data processing](src/gwascatalog/sumstatapp/cli) and eventual integration with the GWAS Catalog backend

### User facing website

* The `docs` directory contains a [docusaurus](https://docusaurus.io/) website
* This is the landing page for non-SNP GWAS Catalog submissions, and the compiled static site will be deployed to https://ebi.ac.uk/gwas/apps/beyond-snps
* A [custom docusaurus build process](docs/package.json#L11) is responsible for building the sumstatlib wheel and bundling the sumstatapp web directory as static content

### Building the beyond SNPs static site

Development build (assumes deployed to `/` on `localhost:8000`):

```
$ cd docs
$ npm run build:dev
$ npm run serve 
```

Production build (assumes deployed to a base URL: `gwas/apps/beyond-snps`)

```
$ cd docs
$ npm run build
$ npm run serve 
```

