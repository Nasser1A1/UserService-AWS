# core/dependencies.py
from core.logger import LoggingService

# Initialize a shared logging service instance (like a singleton)
logging_service = LoggingService()

def get_logger():
    """
    Dependency provider for FastAPI or other DI-based systems.
    Returns the logger instance.
    """
    return logging_service.get_logger()
