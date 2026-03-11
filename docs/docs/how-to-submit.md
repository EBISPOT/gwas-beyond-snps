---
title: "How to submit your data"
---

# How to submit gene-based and CNV GWAS to the GWAS Catalog

:::tip It's OK to fail

* Our CNV and gene-based data models are draft standards
* They have not yet been fully integrated into our submission system
* We request that submitters validate their data locally prior to submission
* This means that your submission is **expected to fail validation after you submit it**
* [Get in touch with us](mailto:gwas-subs@ebi.ac.uk) and we will manually process your submission
* See below for the expected process
:::

```mermaid
flowchart TD

    A{What kind of genetic variation do I want to submit?}
    B[SNPs]
    C[CNVs]
    D[I aggregated my variants into genes]

    A --> B
    A --> C
    A --> D

    Z[Follow standard submission guidelines at ebi.ac.uk/gwas/docs/submission]
    B --> Z

    X{How should I validate my files?}

    H[Use the web interface at ebi.ac.uk/gwas/apps/beyond-snps]
    I[Use the CLI at github.com/ebispot/gwas-pysumstats]

    C --> X
    D --> X

    X -->|Few files OR not confident with terminal| H
    X -->|Many files AND comfortable with terminal| I

    J{Data passes validation and new standardised files have been created?}

    H --> J
    I --> J

    K[Review errors, check docs, correct files, re-validate]

    J -->|No| K
    K --> J

    L[Begin standard submission: ebi.ac.uk/gwas/deposition]
    J -->|Yes| L

    M[Upload **validated files** via Globus]
    L --> M

    N{Checksum validation passes?}
    M --> N
    N -->|No| Q

    Q[Review files, recalculate checksum, update template]
    Q --> N

    O{Sumstat validation fails?}
    N -->|Yes| O

    P[Contact gwas-subs@ebi.ac.uk to complete your submission]
    O --> P
```