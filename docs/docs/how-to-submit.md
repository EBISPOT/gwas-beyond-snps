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

    variation_type{What kind of genetic variation do I want to submit?}
    snps[SNPs]
    cnvs[CNVs]
    gene_agg[I aggregated my variants into genes]

    variation_type --> snps
    variation_type --> cnvs
    variation_type --> gene_agg

    snp_guidelines[Follow standard submission guidelines at ebi.ac.uk/gwas/docs/submission]
    snps --> snp_guidelines

    validation_choice{How should I validate my files?}

    web_validator[Use the web interface at ebi.ac.uk/gwas/apps/beyond-snps]
    cli_validator[Use the CLI at github.com/ebispot/gwas-pysumstats]

    cnvs --> validation_choice
    gene_agg --> validation_choice

    validation_choice -->|Few files OR not confident with terminal| web_validator
    validation_choice -->|Many files AND comfortable with terminal| cli_validator

    validation_result{Data passes validation and new standardised files have been created?}

    web_validator --> validation_result
    cli_validator --> validation_result

    fix_errors[Review errors, check docs, correct files, re-validate]

    validation_result -->|No| fix_errors
    fix_errors --> validation_result

    start_submission[Begin standard submission: ebi.ac.uk/gwas/deposition]
    validation_result -->|Yes| start_submission

    complete_metadata[Fill and submit metadata template]
    start_submission --> complete_metadata

    upload_globus[Upload **validated files** via Globus]
    complete_metadata --> upload_globus

    checksum_check{Checksum validation passes?}
    upload_globus --> checksum_check
    checksum_check -->|No| checksum_fix

    checksum_fix[Review files, recalculate checksum, update template]
    checksum_fix --> checksum_check

    sumstat_check{Sumstat validation fails?}
    checksum_check -->|Yes| sumstat_check

    contact_support[That's expected, contact gwas-subs@ebi.ac.uk]
    sumstat_check --> contact_support
```