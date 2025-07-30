import os
import gc
import psutil
import logging
from typing import Optional

logger = logging.getLogger(__name__)

def load_prompt(prompt_path: str) -> str:
    """Load a prompt template from a file."""
    try:
        with open(prompt_path, 'r', encoding='utf-8') as file:
            return file.read().strip()
    except FileNotFoundError:
        logger.error(f"Prompt file not found: {prompt_path}")
        return ""
    except Exception as e:
        logger.error(f"Error loading prompt from {prompt_path}: {str(e)}")
        return ""

def get_memory_usage() -> dict:
    """Get current memory usage information."""
    try:
        process = psutil.Process()
        memory_info = process.memory_info()
        memory_percent = process.memory_percent()
        
        return {
            'rss_mb': memory_info.rss / 1024 / 1024,  # Resident Set Size in MB
            'vms_mb': memory_info.vms / 1024 / 1024,  # Virtual Memory Size in MB
            'percent': memory_percent,
            'available_mb': psutil.virtual_memory().available / 1024 / 1024
        }
    except Exception as e:
        logger.warning(f"Could not get memory usage: {str(e)}")
        return {'rss_mb': 0, 'vms_mb': 0, 'percent': 0, 'available_mb': 0}

def check_memory_pressure() -> bool:
    """Check if system is under memory pressure."""
    try:
        memory_usage = get_memory_usage()
        
        # Check if memory usage is high
        if memory_usage['percent'] > 80:
            logger.warning(f"High memory usage detected: {memory_usage['percent']:.1f}%")
            return True
            
        # Check if available memory is low
        if memory_usage['available_mb'] < 500:  # Less than 500MB available
            logger.warning(f"Low available memory: {memory_usage['available_mb']:.1f}MB")
            return True
            
        return False
    except Exception as e:
        logger.warning(f"Could not check memory pressure: {str(e)}")
        return False

def force_memory_cleanup():
    """Force garbage collection and memory cleanup."""
    try:
        # Force garbage collection
        collected = gc.collect()
        logger.info(f"Garbage collection freed {collected} objects")
        
        # Get memory usage before and after
        before = get_memory_usage()
        
        # Force another collection cycle
        gc.collect()
        
        after = get_memory_usage()
        
        memory_freed = before['rss_mb'] - after['rss_mb']
        if memory_freed > 0:
            logger.info(f"Memory cleanup freed {memory_freed:.1f}MB")
        
        return memory_freed
    except Exception as e:
        logger.warning(f"Error during memory cleanup: {str(e)}")
        return 0

def memory_safe_execute(func, *args, **kwargs):
    """Execute a function with memory safety checks."""
    try:
        # Check memory pressure before execution
        if check_memory_pressure():
            logger.info("Memory pressure detected, forcing cleanup before execution")
            force_memory_cleanup()
        
        # Execute the function
        result = func(*args, **kwargs)
        
        # Check memory pressure after execution
        if check_memory_pressure():
            logger.info("Memory pressure detected after execution, forcing cleanup")
            force_memory_cleanup()
        
        return result
    except MemoryError as e:
        logger.error(f"Memory error during execution: {str(e)}")
        force_memory_cleanup()
        raise
    except Exception as e:
        logger.error(f"Error during execution: {str(e)}")
        raise

def setup_memory_monitoring():
    """Setup memory monitoring and periodic cleanup."""
    try:
        # Set garbage collection thresholds
        gc.set_threshold(700, 10, 10)  # More aggressive collection
        
        # Log initial memory state
        memory_info = get_memory_usage()
        logger.info(f"Initial memory state: {memory_info['rss_mb']:.1f}MB RSS, "
                   f"{memory_info['percent']:.1f}% usage")
        
    except Exception as e:
        logger.warning(f"Could not setup memory monitoring: {str(e)}")

def log_memory_usage(stage: str = "Unknown"):
    """Log current memory usage for debugging."""
    try:
        memory_info = get_memory_usage()
        logger.info(f"Memory usage at {stage}: {memory_info['rss_mb']:.1f}MB RSS, "
                   f"{memory_info['percent']:.1f}% usage, "
                   f"{memory_info['available_mb']:.1f}MB available")
    except Exception as e:
        logger.warning(f"Could not log memory usage: {str(e)}")
