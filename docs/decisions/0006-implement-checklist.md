# Implement checklist on web interface

Date: 2026-02-26

## Status

Accepted

## Context

We need to describe data requirements to users which are complex and different for
each type of genetic variation. Some fields are conditional, becoming mandatory 
depending on the state of other fields. This complexity increases cognitive load on users
and increases the burden of submitting data to the GWAS Catalog.

For example, including beta as a measure of effect size will always require standard
error to be included. Beta with confidence intervals is invalid, while including odds 
ratio will require both confidence interval fields. Confusing!

This problem is mostly about communicating with users. The Pydantic models are already 
quite capable of flexibly parsing data. Only three types of validation context are 
required:

* assembly
* allow zero p values
* the primary effect size (if multiple effect sizes are present)

As a reminder, the user persona for the web application is:

* A senior researcher or clinician who is a specialist in their disease/trait
* They understand the data well, but have limited CLI skills and no time or motivation 
  to learn - they had a bioinformatician do the analysis for them
* They now want to share the data, but the bioinformatician is unavailable to help make 
  the submission

Given this user persona, an intuitive but comprehensive interface is needed to guide the 
user through the data requirements.

## Decision

The UI will implement a checklist-based form. 

JavaScript will provide guidance-only validation (for user training and communication).

Pydantic models (via Pyodide) remain the sole source of truth for structural validation.

No server-side API will be introduced.

Error feedback will be surfaced in the UI.

The validated artifact will be locally generated and can be submitted using standard
GWAS Catalog submission mechanisms.

## Alternatives considered 

Rejected alternatives include serving Pydantic models via an API and using a Python 
library to generate the checklist. 

The application is implemented as a static site, consisting of a single HTML page with 
a Pyodide backend. Relying on standard HTML and vanilla JavaScript is simpler and more 
portable.

We also considered porting the authoritative validation library to JavaScript. This is 
not feasible because the validation logic is complex and we need for a single source of 
truth across multiple platforms. The domain experts (GWAS Catalog bioinformaticians) 
know Python.

## Consequences

The checklist will:

- Reduce cognitive load for users
- Makes conditional dependencies explicit
- Serve as living validation documentation

The JavaScript validation is intentionally not used programmatically outside of the web 
interface. It is responsible for user guidance only. 

All structural data validation is delegated to the Python library to maximise code 
reuse and provide a single source of truth across multiple platforms (e.g. CLI). The 
Python library is responsible for enforcing GWAS Catalog data standards.

The aim of the JavaScript validation is to guide users and provide a visual 
representation of the data requirements.

However, this can introduce rule drift and edge cases between the checklist implemented 
in JS and the validation implemented in Python.

We will need to monitor user feedback to ensure that the checklist is accurate and up 
to date.