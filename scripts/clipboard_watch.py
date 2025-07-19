import time
import pyperclip


def watch_clipboard() -> None:
    """Print clipboard updates until interrupted."""

    print("Watching clipboard. Press Ctrl+C to stop.")
    last = pyperclip.paste()
    try:
        while True:
            current = pyperclip.paste()
            if current != last:
                print("\n--- clipboard updated ---\n")
                print(current)
                last = current
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nClipboard watch stopped.")


if __name__ == "__main__":
    watch_clipboard()
