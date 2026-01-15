"""
Enums, annotated types, and Pydantic models for SNP variants.

This module defines enums and annotated types specific to SNPs, which are
used to build Pydantic models for SNP summary statistics.
"""

import warnings

# only gene-based / CNV really supported
warnings.warn(
    """
    The 'snp' package contains experimental code and is not production-ready.
    
    Please don't use this library to validate SNP summary statistics.
    
    Instead use: https://github.com/ebispot/gwas-sumstats-tools
    """,
    category=UserWarning,
    stacklevel=2,
)
