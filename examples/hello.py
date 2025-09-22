"""Simple example that logs 'Hello' and 'World!' with delays."""
import logging
import time

print("Running examples/hello.py")


class Hello:
    """Just say hello."""
    def __init__(self):
        logging.warning("Hello from class!")

class Work:
    """Just wait a bit."""
    def __init__(self):
        time.sleep(1)

class World:
    """Just say world."""
    def __init__(self):
        logging.error("World from class!")


def main():
    """Main function to log messages."""
    for _ in range(3):
        Hello()
        Work()
        World()


if __name__ == "__main__":
    main()
