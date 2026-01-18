SPINNER = ["⣾", "⣽", "⣻", "⢿", "⡿", "⣟", "⣯", "⣷"]

def spinner(step: int, title: str) -> str:
    ch = SPINNER[step % len(SPINNER)]
    return f"{ch} <b>{title}</b>\n\nPlease wait..."
