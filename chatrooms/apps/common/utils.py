

def base36_to_int(string: str) -> int:
    """
    Convert a base 36 string to an int. Raise ValueError if the input won't fit
    into an int.
    """
    # To prevent overconsumption of server resources, reject any
    # base36 string that is longer than 13 base36 digits (13 digits
    # is sufficient to base36-encode any 64-bit integer)
    if len(string) > 13:
        raise ValueError("Base36 input too large")
    return int(string, 36)


def int_to_base36(integer: int) -> str:
    """Convert an integer to a base36 string."""
    char_set = "0123456789abcdefghijklmnopqrstuvwxyz"
    if integer < 0:
        raise ValueError("Negative base36 conversion input.")
    if integer < 36:
        return char_set[integer]
    b36 = ""
    while integer != 0:
        integer, index = divmod(integer, 36)
        b36 = char_set[index] + b36
    return b36
