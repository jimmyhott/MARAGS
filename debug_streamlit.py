#!/usr/bin/env python3
"""
Debug script for MARAGS Streamlit app
Run this to test individual components and troubleshoot issues
"""

import sys
import os
import logging
import traceback
from datetime import datetime

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def setup_debug_logging():
    """Setup comprehensive debug logging"""
    log_filename = f"debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def test_imports():
    """Test if all required modules can be imported"""
    logger = setup_debug_logging()
    logger.info("Testing imports...")
    
    try:
        import streamlit as st
        logger.info("✅ Streamlit imported successfully")
        logger.info(f"Streamlit version: {st.__version__}")
    except ImportError as e:
        logger.error(f"❌ Failed to import Streamlit: {e}")
        return False
    
    try:
        from workflows.main_graph import main_workflow, WorkflowConfig
        logger.info("✅ Main workflow imported successfully")
    except ImportError as e:
        logger.error(f"❌ Failed to import main workflow: {e}")
        return False
    
    try:
        from agents.researcher import ResearcherAgent
        from agents.writer import WriterAgent
        from agents.editor import EditorAgent
        logger.info("✅ All agents imported successfully")
    except ImportError as e:
        logger.error(f"❌ Failed to import agents: {e}")
        return False
    
    try:
        from llm.azure_llm_client import get_azure_llm
        from llm.local_llm_client import get_local_llm
        logger.info("✅ LLM clients imported successfully")
    except ImportError as e:
        logger.error(f"❌ Failed to import LLM clients: {e}")
        return False
    
    return True

def test_llm_connections():
    """Test LLM connections"""
    logger = setup_debug_logging()
    logger.info("Testing LLM connections...")
    
    try:
        from llm.azure_llm_client import get_azure_llm
        azure_llm = get_azure_llm()
        logger.info("✅ Azure LLM client created successfully")
        
        # Test a simple call
        try:
            response = azure_llm.chat.completions.create(
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10,
                model="gpt-4o-mini"
            )
            logger.info("✅ Azure LLM test call successful")
        except Exception as e:
            logger.warning(f"⚠️ Azure LLM test call failed: {e}")
            
    except Exception as e:
        logger.error(f"❌ Failed to create Azure LLM client: {e}")
    
    try:
        from llm.local_llm_client import get_local_llm
        local_llm = get_local_llm()
        logger.info("✅ Local LLM client created successfully")
    except Exception as e:
        logger.error(f"❌ Failed to create Local LLM client: {e}")

def test_workflow_components():
    """Test individual workflow components"""
    logger = setup_debug_logging()
    logger.info("Testing workflow components...")
    
    try:
        from workflows.main_graph import build_workflow
        graph = build_workflow()
        logger.info("✅ Workflow graph built successfully")
        logger.info(f"Graph type: {type(graph)}")
    except Exception as e:
        logger.error(f"❌ Failed to build workflow: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False
    
    return True

def test_agent_creation():
    """Test agent creation"""
    logger = setup_debug_logging()
    logger.info("Testing agent creation...")
    
    try:
        from llm.azure_llm_client import get_azure_llm
        from agents.researcher import ResearcherAgent
        from agents.writer import WriterAgent
        from agents.editor import EditorAgent
        
        llm = get_azure_llm()
        researcher = ResearcherAgent(llm)
        writer = WriterAgent(llm)
        editor = EditorAgent(llm)
        
        logger.info("✅ All agents created successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to create agents: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def test_environment():
    """Test environment variables and configuration"""
    logger = setup_debug_logging()
    logger.info("Testing environment...")
    
    # Check Python version
    logger.info(f"Python version: {sys.version}")
    
    # Check current working directory
    logger.info(f"Working directory: {os.getcwd()}")
    
    # Check if we're in a virtual environment
    logger.info(f"Virtual environment: {sys.prefix}")
    
    # Check environment variables
    env_vars = [
        'AZURE_OPENAI_API_KEY',
        'AZURE_OPENAI_ENDPOINT',
        'OPENAI_API_KEY'
    ]
    
    for var in env_vars:
        value = os.getenv(var)
        if value:
            logger.info(f"✅ {var} is set")
        else:
            logger.warning(f"⚠️ {var} is not set")

def run_comprehensive_test():
    """Run all tests"""
    logger = setup_debug_logging()
    logger.info("=" * 50)
    logger.info("Starting comprehensive debug test")
    logger.info("=" * 50)
    
    tests = [
        ("Environment Test", test_environment),
        ("Import Test", test_imports),
        ("LLM Connection Test", test_llm_connections),
        ("Agent Creation Test", test_agent_creation),
        ("Workflow Component Test", test_workflow_components),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results[test_name] = result
            if result:
                logger.info(f"✅ {test_name} PASSED")
            else:
                logger.error(f"❌ {test_name} FAILED")
        except Exception as e:
            logger.error(f"❌ {test_name} FAILED with exception: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            results[test_name] = False
    
    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("TEST SUMMARY")
    logger.info("=" * 50)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! Your setup looks good.")
    else:
        logger.warning("⚠️ Some tests failed. Check the logs above for details.")
    
    return passed == total

if __name__ == "__main__":
    print("🐛 MARAGS Debug Script")
    print("=" * 30)
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "imports":
            test_imports()
        elif command == "llm":
            test_llm_connections()
        elif command == "workflow":
            test_workflow_components()
        elif command == "agents":
            test_agent_creation()
        elif command == "env":
            test_environment()
        else:
            print(f"Unknown command: {command}")
            print("Available commands: imports, llm, workflow, agents, env, all")
    else:
        # Run comprehensive test by default
        run_comprehensive_test() 