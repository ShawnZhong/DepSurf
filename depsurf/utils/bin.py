def get_cstr(data, off):
    end = data.find(b"\x00", off)
    return data[off:end].decode()
