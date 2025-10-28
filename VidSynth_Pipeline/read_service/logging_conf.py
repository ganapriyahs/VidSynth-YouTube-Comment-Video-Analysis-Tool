import logging, sys

FMT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"

def configure_logging(level=logging.INFO):
    """Call this once at the start of every step."""
    root = logging.getLogger()
    root.setLevel(level)

    # Avoid duplicate handlers
    if not any(isinstance(h, logging.StreamHandler) for h in root.handlers):
        h = logging.StreamHandler(sys.stdout)
        h.setFormatter(logging.Formatter(FMT))
        root.addHandler(h)

def get_logger(step_name: str):
    """Use child loggers per step so logs are easy to find."""
    return logging.getLogger(f"vidsynth.{step_name}")
