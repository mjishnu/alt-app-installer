# convert to byte

def to_bytes(value, size_in):

    if size_in == 'KB' or size_in == 'kb':
        size = 1024 * float(value)
        return int(size)

    elif size_in == 'MB' or size_in == 'mb':
        size = (1024 * float(value), 'KB')
        return to_bytes(*size)

    elif size_in == 'GB' or size_in == 'gb':
        size = (1024 * float(value), 'MB')
        return to_bytes(*size)

    elif size_in == 'TB' or size_in == 'tb':
        size = (1024 * float(value), 'GB')
        return to_bytes(*size)

    else:
        raise Exception(
            "File not in supported Range! ==> [Not in KB,MB,GB,TB]")
