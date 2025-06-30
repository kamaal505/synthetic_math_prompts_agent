import time


def get_input(prompt, default=None):
    val = input(f"{prompt} [{default}]: ") if default else input(f"{prompt}: ")
    return val.strip() or None


def format_duration(seconds):
    """Convert duration in seconds to human-readable format (e.g., '2h 34m 43.25s')."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    remaining_seconds = seconds % 60

    if hours > 0:
        return f"{hours}h {minutes}m {remaining_seconds:.2f}s"
    elif minutes > 0:
        return f"{minutes}m {remaining_seconds:.2f}s"
    else:
        return f"{remaining_seconds:.2f}s"
