import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict

class LoggingConfig:
    """
    Centralized logging configuration that creates date-time based folders
    and sets up loggers for different modules.
    """
    
    _loggers: Dict[str, logging.Logger] = {}
    _log_dir: Path = None
    
    @classmethod
    def setup_logging(cls) -> Path:
        """
        Set up the logging directory structure and return the log directory path.
        
        Returns:
            Path: The current session's log directory
        """
        if cls._log_dir is not None:
            return cls._log_dir
            
        # Create logs directory in root
        root_dir = Path(__file__).parent.parent.parent  # Go up to CloneMe root
        logs_dir = root_dir / "logs"
        logs_dir.mkdir(exist_ok=True)
        
        # Create date-time specific folder
        current_time = datetime.now()
        date_time_folder = current_time.strftime("%Y-%m-%d_%H-%M-%S")
        session_log_dir = logs_dir / date_time_folder
        session_log_dir.mkdir(exist_ok=True)
        
        cls._log_dir = session_log_dir
        return session_log_dir
    
    @classmethod
    def get_logger(cls, module_name: str) -> logging.Logger:
        """
        Get or create a logger for a specific module.
        
        Args:
            module_name: Name of the module (e.g., 'decisions', 'dcord')
            
        Returns:
            logging.Logger: Configured logger for the module
        """
        if module_name in cls._loggers:
            return cls._loggers[module_name]
        
        # Ensure log directory is set up
        log_dir = cls.setup_logging()
        
        # Create logger
        logger = logging.getLogger(module_name)
        logger.setLevel(logging.DEBUG)
        
        # Remove any existing handlers to avoid duplicates
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # Create file handler
        log_file = log_dir / f"{module_name}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(file_handler)
        
        # Prevent propagation to root logger to avoid console output
        logger.propagate = False
        
        cls._loggers[module_name] = logger
        return logger
    
    @classmethod
    def get_current_log_dir(cls) -> Path:
        """Get the current session's log directory."""
        if cls._log_dir is None:
            return cls.setup_logging()
        return cls._log_dir

    @classmethod
    def initialize_all_loggers(cls) -> None:
        """
        Initialize all expected loggers for the application.
        This ensures all log files are created at startup.
        """
        expected_loggers = [
            'response_generator',
            'ai_router',
            'settings_manager',
            'platform_manager',
            'decisions',
            'discordplatform',
            'settings.file_handler'
        ]

        for logger_name in expected_loggers:
            cls.get_logger(logger_name)

    @classmethod
    def list_active_loggers(cls) -> Dict[str, str]:
        """
        Get a list of all active loggers and their log file paths.

        Returns:
            Dict mapping logger names to their log file paths
        """
        log_dir = cls.get_current_log_dir()
        return {
            name: str(log_dir / f"{name}.log")
            for name in cls._loggers.keys()
        }