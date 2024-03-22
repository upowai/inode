def remove_b_prefix(byte_string):
    if isinstance(byte_string, bytes):
        return byte_string.decode("utf-8")
    elif (
        isinstance(byte_string, str)
        and byte_string.startswith("b'")
        and byte_string.endswith("'")
    ):
        return byte_string[2:-1]
    return byte_string


# Example usage:
byte_str_example = b"DZ3hFKMTXnTHWtG8pRquCDfGBnSShfDwTKKzkoibvb3NA"
cleaned_str = remove_b_prefix(byte_str_example)
print(cleaned_str)

# If the input is a string that looks like a byte string:
str_example = "DZ3hFKMTXnTHWtG8pRquCDfGBnSShfDwTKKzkoibvb3N0"
cleaned_str_from_str = remove_b_prefix(str_example)
print(cleaned_str_from_str)
