def format_k(val, num_digits=3):
    if val > 1000:
        return f"{val // 1000:{num_digits-1}d}k"
    return f"{val:{num_digits}d}"
