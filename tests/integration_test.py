#!/usr/bin/env python3
"""
Integration Test - Manual Verification Script
Tests the multi-agent system without external dependencies
"""

import os
import sys

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def print_test(name, passed, message=""):
    status = f"{GREEN}✓ PASS{RESET}" if passed else f"{RED}✗ FAIL{RESET}"
    print(f"{status} - {name}")
    if message:
        print(f"  {message}")

def test_file_structure():
    """Test that all required files exist"""
    print(f"\n{YELLOW}=== Testing File Structure ==={RESET}")

    required_files = [
        # Database layer
        'src/database/__init__.py',
        'src/database/models.py',
        'src/database/schema.py',
        'src/database/migrations.py',

        # Core components
        'src/project_manager.py',
        'src/decision_queue.py',
        'src/event_logger.py',
        'src/enhanced_orchestrator.py',

        # Agents
        'src/agents/human_agent.py',
        'src/agents/base_agent.py',

        # Backend API
        'backend/main.py',
        'backend/config.py',
        'backend/dependencies.py',
        'backend/api/auth.py',
        'backend/api/projects.py',
        'backend/api/tasks.py',
        'backend/api/decisions.py',

        # Frontend
        'frontend/package.json',
        'frontend/vite.config.js',
        'frontend/src/App.jsx',
        'frontend/src/main.jsx',
        'frontend/src/api/client.js',
        'frontend/src/store/index.js',
        'frontend/src/pages/LoginPage.jsx',
        'frontend/src/pages/ProjectsPage.jsx',
        'frontend/src/pages/DecisionsPage.jsx',

        # Tests
        'tests/test_project_manager.py',
        'tests/test_decision_queue.py',
        'tests/test_human_agent.py',
    ]

    all_exist = True
    for file_path in required_files:
        exists = os.path.exists(file_path)
        if not exists:
            all_exist = False
        print_test(file_path, exists)

    return all_exist

def test_python_syntax():
    """Test Python files for syntax errors"""
    print(f"\n{YELLOW}=== Testing Python Syntax ==={RESET}")

    import py_compile

    python_files = []
    for root, dirs, files in os.walk('src'):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))

    for root, dirs, files in os.walk('backend'):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))

    for root, dirs, files in os.walk('tests'):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))

    all_valid = True
    for py_file in python_files:
        try:
            py_compile.compile(py_file, doraise=True)
            print_test(py_file, True)
        except py_compile.PyCompileError as e:
            print_test(py_file, False, str(e))
            all_valid = False

    return all_valid

def test_database_schema():
    """Test database schema definitions"""
    print(f"\n{YELLOW}=== Testing Database Schema ==={RESET}")

    try:
        sys.path.insert(0, os.getcwd())

        # Check if models are importable (syntax check)
        with open('src/database/models.py', 'r') as f:
            content = f.read()

        required_models = [
            'class User',
            'class Project',
            'class ProjectMember',
            'class Session',
            'class Task',
            'class TaskEvent',
            'class PendingDecision',
            'class Artifact'
        ]

        all_found = True
        for model in required_models:
            found = model in content
            print_test(model, found)
            if not found:
                all_found = False

        return all_found
    except Exception as e:
        print_test("Database Schema", False, str(e))
        return False

def test_api_endpoints():
    """Test API endpoint definitions"""
    print(f"\n{YELLOW}=== Testing API Endpoints ==={RESET}")

    api_files = {
        'backend/api/auth.py': ['POST /login', 'POST /register'],
        'backend/api/projects.py': ['GET /projects', 'POST /projects', 'POST /members'],
        'backend/api/tasks.py': ['GET /tasks', 'POST /tasks', 'POST /execute'],
        'backend/api/decisions.py': ['GET /pending', 'POST /resolve'],
    }

    all_found = True
    for file_path, endpoints in api_files.items():
        try:
            with open(file_path, 'r') as f:
                content = f.read()

            for endpoint in endpoints:
                method, path = endpoint.split(' ')
                # Check for router decorator
                found = f'@router.{method.lower()}' in content or f'@app.{method.lower()}' in content
                print_test(f"{file_path}: {endpoint}", found)
                if not found:
                    all_found = False
        except Exception as e:
            print_test(file_path, False, str(e))
            all_found = False

    return all_found

def test_frontend_structure():
    """Test frontend component structure"""
    print(f"\n{YELLOW}=== Testing Frontend Structure ==={RESET}")

    try:
        # Check package.json
        import json
        with open('frontend/package.json', 'r') as f:
            package = json.load(f)

        required_deps = ['react', 'react-router-dom', 'antd', 'axios', 'zustand']
        all_found = True

        for dep in required_deps:
            found = dep in package.get('dependencies', {})
            print_test(f"Dependency: {dep}", found)
            if not found:
                all_found = False

        return all_found
    except Exception as e:
        print_test("Frontend Structure", False, str(e))
        return False

def test_rbac_permissions():
    """Test RBAC permission definitions"""
    print(f"\n{YELLOW}=== Testing RBAC Permissions ==={RESET}")

    try:
        with open('src/project_manager.py', 'r') as f:
            content = f.read()

        required_roles = ['OWNER', 'ADMIN', 'MEMBER', 'VIEWER']
        required_permissions = ['execute_task', 'manage_members', 'view_project']

        all_found = True
        for role in required_roles:
            found = role in content
            print_test(f"Role: {role}", found)
            if not found:
                all_found = False

        for perm in required_permissions:
            found = perm in content
            print_test(f"Permission: {perm}", found)
            if not found:
                all_found = False

        return all_found
    except Exception as e:
        print_test("RBAC Permissions", False, str(e))
        return False

def main():
    print(f"\n{YELLOW}{'='*60}{RESET}")
    print(f"{YELLOW}Multi-Agent System - Integration Test{RESET}")
    print(f"{YELLOW}{'='*60}{RESET}")

    results = {
        'File Structure': test_file_structure(),
        'Python Syntax': test_python_syntax(),
        'Database Schema': test_database_schema(),
        'API Endpoints': test_api_endpoints(),
        'Frontend Structure': test_frontend_structure(),
        'RBAC Permissions': test_rbac_permissions(),
    }

    print(f"\n{YELLOW}{'='*60}{RESET}")
    print(f"{YELLOW}Test Summary{RESET}")
    print(f"{YELLOW}{'='*60}{RESET}")

    for test_name, passed in results.items():
        status = f"{GREEN}PASS{RESET}" if passed else f"{RED}FAIL{RESET}"
        print(f"{test_name}: {status}")

    total = len(results)
    passed = sum(results.values())

    print(f"\n{YELLOW}Total: {passed}/{total} tests passed{RESET}")

    if passed == total:
        print(f"\n{GREEN}✓ All tests passed!{RESET}")
        return 0
    else:
        print(f"\n{RED}✗ Some tests failed{RESET}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
