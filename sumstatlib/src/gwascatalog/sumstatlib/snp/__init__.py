"""
IMPORTANT: This package is a stub/placeholder and is not intended for production use.

It contains experimental code that may be incomplete or subject to change.

Please do not use this library for validating SNP summary statistics. Instead use:

https://github.com/ebispot/gwas-sumstats-tools
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
