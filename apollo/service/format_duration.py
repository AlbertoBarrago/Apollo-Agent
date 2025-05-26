def format_duration_ms(total_ms):
    """
    Format a duration given in milliseconds to a human-readable string.

    Args:
        total_ms: Duration in milliseconds

    Returns:
        Formatted string in the format "X hours Y minutes Z seconds W ms"
    """
    # Convert to different units
    if not total_ms:
        return "0 ms"
    ms = total_ms % 1000
    total_seconds = total_ms // 1000

    seconds = total_seconds % 60
    total_minutes = total_seconds // 60

    minutes = total_minutes % 60
    hours = total_minutes // 60

    # Build the output string
    parts = []
    if hours > 0:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if minutes > 0:
        parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
    if seconds > 0:
        parts.append(f"{seconds} second{'s' if seconds != 1 else ''}")
    if ms > 0:
        parts.append(f"{ms} ms")

    if not parts:
        return "0 ms"

    return ", ".join(parts)
