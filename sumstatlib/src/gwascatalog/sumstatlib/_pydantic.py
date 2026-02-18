"""This is a shim for pydantic. All pydantic imports in the library should be made from here.

This shim exists because the library is distributed with pydantic optional at installation time but
required at runtime.

This choice probably strikes you as odd, but it simplifies portability across platforms.

For example, WebAssembly deployments with Pyodide struggle to handle packages that aren't pure Python.

However, Pydantic is available via Pyodide's micropip package manager.

Making pydantic optional means that consumers of the library can provide pydantic themselves on different platforms.
"""

try:
    from pydantic import (
        BaseModel,
        BeforeValidator,
        ConfigDict,
        Field,
        PositiveInt,
        PrivateAttr,
        StringConstraints,
        ValidationInfo,
        computed_field,
        model_validator,
    )
except ImportError as e:
    raise ImportError(
        "pydantic is required to use this package. Install with `pip install gwascatalog.sumstatlib[pydantic]`."
    ) from e
else:
    import pydantic

    if not pydantic.__version__.startswith("2."):
        raise ImportError("Pydantic v2 required")

__all__ = [
    "BaseModel",
    "BeforeValidator",
    "ConfigDict",
    "Field",
    "PositiveInt",
    "PrivateAttr",
    "StringConstraints",
    "ValidationInfo",
    "computed_field",
    "model_validator",
]
