SPINNER = ["⣾","⣽","⣻","⢿","⡿","⣟","⣯","⣷"]
def spinner(i, t): return f"{SPINNER[i%len(SPINNER)]} <b>{t}</b>\nPlease wait..."
