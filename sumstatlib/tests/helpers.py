import pytest
from pydantic import TypeAdapter, ValidationError


# reusable type test function
def run_type_validation_test(type_to_test, input_data, expected_error):
    adapter = TypeAdapter(type_to_test)
    if expected_error is None:
        _ = adapter.validate_python(input_data)
        # exceptions will be raised by validate_python
    else:
        with pytest.raises(ValidationError) as exc_info:
            adapter.validate_python(input_data)
        assert expected_error in str(exc_info.value)
