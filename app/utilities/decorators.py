from app.worker.logging_format import init_logger

logger = init_logger("Retry Decorator")


def handle_reconnect(func):
    def wrapper(self, *args, **kwargs):
        retries = 3
        for _ in range(retries):
            try:
                return func(self, *args, **kwargs)
            except Exception as e:
                print(f"Error in {func.__name__}: {e}")
                self.reconnect()
        logger.magic_signon(f"Failed to execute {func.__name__} after {retries} retries.")
    return wrapper
