# def remove_b_prefix(byte_string):
#     if isinstance(byte_string, bytes):
#         return byte_string.decode("utf-8")
#     elif (
#         isinstance(byte_string, str)
#         and byte_string.startswith("b'")
#         and byte_string.endswith("'")
#     ):
#         return byte_string[2:-1]
#     return byte_string


# # Example usage:
# byte_str_example = b"DZ3hFKMTXnTHWtG8pRquCDfGBnSShfDwTKKzkoibvb3NA"
# cleaned_str = remove_b_prefix(byte_str_example)
# print(cleaned_str)

# # If the input is a string that looks like a byte string:
# str_example = "DZ3hFKMTXnTHWtG8pRquCDfGBnSShfDwTKKzkoibvb3N0"
# cleaned_str_from_str = remove_b_prefix(str_example)
# print(cleaned_str_from_str)


from decimal import Decimal, ROUND_DOWN

# Inside your loop
new_balance = 0.8860188648648649
# Ensure new_balance is a Decimal and round it down to 8 decimal places
amounts = str(Decimal(new_balance).quantize(Decimal("0.00000001"), rounding=ROUND_DOWN))

print(amounts)

amounts = str(1000)

print(amounts)
