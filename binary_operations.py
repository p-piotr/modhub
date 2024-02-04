from ctypes import c_uint8, c_uint16, c_uint32, c_uint64

def binary_not(val, bit_size=32):
    if bit_size == 8:
        return c_uint8(~val).value
    elif bit_size == 16:
        return c_uint16(~val).value
    elif bit_size == 32:
        return c_uint32(~val).value
    elif bit_size == 64:
        return c_uint64(~val).value
    return None

def binary_and(val1, val2, bit_size=32):
    if bit_size == 8:
        return c_uint8(val1 & val2).value
    elif bit_size == 16:
        return c_uint16(val1 & val2).value
    elif bit_size == 32:
        return c_uint32(val1 & val2).value
    elif bit_size == 64:
        return c_uint64(val1 & val2).value
    return None