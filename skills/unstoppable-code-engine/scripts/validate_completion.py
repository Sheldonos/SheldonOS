#!/usr/bin/env python3
"""
Project Completion Validation Script

This script performs automated checks to validate whether a development project
meets the minimum standards for completion. It checks for common issues and
provides a completion score.

Usage:
    python3 validate_completion.py <project_directory>

Example:
    python3 validate_completion.py /home/ubuntu/my-project

The script will output a report with:
- Completion score (0-100)
- List of passed checks
- List of failed checks
- Recommendations for improvement
"""

import os
import sys
import json
import re
from pathlib import Path
from typing import List, Dict, Tuple

class ValidationCheck:
    """Represents a single validation check."""
    
    def __init__(self, name: str, description: str, weight: int = 1):
        self.name = name
        self.description = description
        self.weight = weight
        self.passed = False
        self.message = ""

class ProjectValidator:
    """Validates a development project for completion."""
    
    def __init__(self, project_dir: str):
        self.project_dir = Path(project_dir)
        self.checks: List[ValidationCheck] = []
        
        if not self.project_dir.exists():
            raise ValueError(f"Project directory does not exist: {project_dir}")
    
    def add_check(self, name: str, description: str, weight: int = 1) -> ValidationCheck:
        """Add a validation check."""
        check = ValidationCheck(name, description, weight)
        self.checks.append(check)
        return check
    
    def run_all_checks(self) -> Dict:
        """Run all validation checks and return results."""
        
        # Documentation checks
        self._check_readme_exists()
        self._check_documentation_quality()
        
        # Code quality checks
        self._check_no_todos()
        self._check_no_hardcoded_credentials()
        self._check_error_handling()
        
        # Structure checks
        self._check_dependencies_documented()
        self._check_gitignore_exists()
        
        # Testing checks
        self._check_tests_exist()
        
        # Calculate score
        total_weight = sum(check.weight for check in self.checks)
        passed_weight = sum(check.weight for check in self.checks if check.passed)
        score = int((passed_weight / total_weight) * 100) if total_weight > 0 else 0
        
        return {
            "score": score,
            "total_checks": len(self.checks),
            "passed_checks": sum(1 for check in self.checks if check.passed),
            "failed_checks": sum(1 for check in self.checks if not check.passed),
            "checks": [
                {
                    "name": check.name,
                    "description": check.description,
                    "passed": check.passed,
                    "message": check.message,
                    "weight": check.weight
                }
                for check in self.checks
            ]
        }
    
    def _check_readme_exists(self):
        """Check if README file exists."""
        check = self.add_check("README exists", "Project has a README file", weight=2)
        
        readme_files = ["README.md", "README.txt", "README", "readme.md"]
        for filename in readme_files:
            if (self.project_dir / filename).exists():
                check.passed = True
                check.message = f"Found {filename}"
                return
        
        check.message = "No README file found"
    
    def _check_documentation_quality(self):
        """Check if documentation is comprehensive."""
        check = self.add_check("Documentation quality", "README contains setup instructions", weight=2)
        
        readme_files = ["README.md", "README.txt", "README"]
        for filename in readme_files:
            readme_path = self.project_dir / filename
            if readme_path.exists():
                content = readme_path.read_text().lower()
                
                # Check for key sections
                has_setup = any(keyword in content for keyword in ["setup", "installation", "getting started", "how to run"])
                has_usage = any(keyword in content for keyword in ["usage", "example", "how to use"])
                
                if has_setup and has_usage:
                    check.passed = True
                    check.message = "README contains setup and usage instructions"
                elif has_setup:
                    check.message = "README has setup instructions but missing usage examples"
                else:
                    check.message = "README is missing setup instructions"
                return
        
        check.message = "No README file to check"
    
    def _check_no_todos(self):
        """Check for TODO comments in code."""
        check = self.add_check("No TODOs", "No TODO or FIXME comments in code", weight=1)
        
        code_extensions = [".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".cpp", ".c", ".go", ".rs"]
        todo_pattern = re.compile(r"(TODO|FIXME|XXX|HACK)", re.IGNORECASE)
        
        todo_files = []
        for ext in code_extensions:
            for file_path in self.project_dir.rglob(f"*{ext}"):
                # Skip node_modules and other common dependency directories
                if any(part in file_path.parts for part in ["node_modules", "venv", ".venv", "dist", "build"]):
                    continue
                
                try:
                    content = file_path.read_text()
                    if todo_pattern.search(content):
                        todo_files.append(file_path.relative_to(self.project_dir))
                except:
                    pass
        
        if not todo_files:
            check.passed = True
            check.message = "No TODO comments found"
        else:
            check.message = f"Found TODO comments in {len(todo_files)} file(s): {', '.join(str(f) for f in todo_files[:3])}"
    
    def _check_no_hardcoded_credentials(self):
        """Check for hardcoded credentials or API keys."""
        check = self.add_check("No hardcoded credentials", "No hardcoded passwords or API keys", weight=3)
        
        code_extensions = [".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".cpp", ".c", ".go", ".rs", ".env"]
        credential_patterns = [
            re.compile(r"password\s*=\s*['\"][^'\"]{3,}['\"]", re.IGNORECASE),
            re.compile(r"api[_-]?key\s*=\s*['\"][^'\"]{10,}['\"]", re.IGNORECASE),
            re.compile(r"secret\s*=\s*['\"][^'\"]{10,}['\"]", re.IGNORECASE),
            re.compile(r"token\s*=\s*['\"][^'\"]{10,}['\"]", re.IGNORECASE),
        ]
        
        suspicious_files = []
        for ext in code_extensions:
            for file_path in self.project_dir.rglob(f"*{ext}"):
                if any(part in file_path.parts for part in ["node_modules", "venv", ".venv", "dist", "build"]):
                    continue
                
                try:
                    content = file_path.read_text()
                    for pattern in credential_patterns:
                        if pattern.search(content):
                            suspicious_files.append(file_path.relative_to(self.project_dir))
                            break
                except:
                    pass
        
        if not suspicious_files:
            check.passed = True
            check.message = "No hardcoded credentials detected"
        else:
            check.message = f"Potential hardcoded credentials in: {', '.join(str(f) for f in suspicious_files[:3])}"
    
    def _check_error_handling(self):
        """Check if error handling is implemented."""
        check = self.add_check("Error handling", "Code includes error handling", weight=2)
        
        code_extensions = [".py", ".js", ".ts", ".jsx", ".tsx"]
        error_keywords = ["try", "catch", "except", "error", "throw"]
        
        files_with_error_handling = 0
        total_code_files = 0
        
        for ext in code_extensions:
            for file_path in self.project_dir.rglob(f"*{ext}"):
                if any(part in file_path.parts for part in ["node_modules", "venv", ".venv", "dist", "build", "test"]):
                    continue
                
                try:
                    content = file_path.read_text().lower()
                    total_code_files += 1
                    
                    if any(keyword in content for keyword in error_keywords):
                        files_with_error_handling += 1
                except:
                    pass
        
        if total_code_files == 0:
            check.message = "No code files found"
        elif files_with_error_handling / total_code_files >= 0.5:
            check.passed = True
            check.message = f"Error handling found in {files_with_error_handling}/{total_code_files} files"
        else:
            check.message = f"Limited error handling: only {files_with_error_handling}/{total_code_files} files"
    
    def _check_dependencies_documented(self):
        """Check if dependencies are documented."""
        check = self.add_check("Dependencies documented", "Dependencies are documented in manifest file", weight=2)
        
        manifest_files = [
            "package.json",
            "requirements.txt",
            "Pipfile",
            "pyproject.toml",
            "Cargo.toml",
            "go.mod",
            "pom.xml",
            "build.gradle"
        ]
        
        for filename in manifest_files:
            if (self.project_dir / filename).exists():
                check.passed = True
                check.message = f"Found {filename}"
                return
        
        check.message = "No dependency manifest file found"
    
    def _check_gitignore_exists(self):
        """Check if .gitignore exists."""
        check = self.add_check(".gitignore exists", "Project has .gitignore file", weight=1)
        
        if (self.project_dir / ".gitignore").exists():
            check.passed = True
            check.message = "Found .gitignore"
        else:
            check.message = "No .gitignore file found"
    
    def _check_tests_exist(self):
        """Check if test files exist."""
        check = self.add_check("Tests exist", "Project includes test files", weight=2)
        
        test_patterns = ["*test*.py", "*test*.js", "*test*.ts", "*.test.*", "*.spec.*"]
        test_dirs = ["tests", "test", "__tests__", "spec"]
        
        # Check for test directories
        for test_dir in test_dirs:
            if (self.project_dir / test_dir).exists():
                check.passed = True
                check.message = f"Found test directory: {test_dir}"
                return
        
        # Check for test files
        test_files = []
        for pattern in test_patterns:
            test_files.extend(self.project_dir.rglob(pattern))
        
        if test_files:
            check.passed = True
            check.message = f"Found {len(test_files)} test file(s)"
        else:
            check.message = "No test files found"

def print_report(results: Dict):
    """Print a formatted validation report."""
    
    score = results["score"]
    
    print("\n" + "="*60)
    print("PROJECT COMPLETION VALIDATION REPORT")
    print("="*60)
    print(f"\nCompletion Score: {score}/100")
    print(f"Checks Passed: {results['passed_checks']}/{results['total_checks']}")
    print(f"Checks Failed: {results['failed_checks']}/{results['total_checks']}")
    
    # Determine status
    if score >= 90:
        status = "✅ EXCELLENT - Project meets high quality standards"
    elif score >= 75:
        status = "✓ GOOD - Project is mostly complete with minor issues"
    elif score >= 60:
        status = "⚠ ACCEPTABLE - Project is functional but needs improvement"
    else:
        status = "❌ INCOMPLETE - Project has significant gaps"
    
    print(f"\nStatus: {status}\n")
    
    # Print passed checks
    passed_checks = [c for c in results["checks"] if c["passed"]]
    if passed_checks:
        print("✅ PASSED CHECKS:")
        for check in passed_checks:
            print(f"  • {check['name']}: {check['message']}")
    
    # Print failed checks
    failed_checks = [c for c in results["checks"] if not c["passed"]]
    if failed_checks:
        print("\n❌ FAILED CHECKS:")
        for check in failed_checks:
            print(f"  • {check['name']}: {check['message']}")
    
    # Recommendations
    if score < 90:
        print("\n📋 RECOMMENDATIONS:")
        if any(c["name"] == "README exists" and not c["passed"] for c in results["checks"]):
            print("  • Add a comprehensive README.md with setup and usage instructions")
        if any(c["name"] == "Tests exist" and not c["passed"] for c in results["checks"]):
            print("  • Add test files to validate functionality")
        if any(c["name"] == "No TODOs" and not c["passed"] for c in results["checks"]):
            print("  • Remove or resolve all TODO comments before declaring completion")
        if any(c["name"] == "No hardcoded credentials" and not c["passed"] for c in results["checks"]):
            print("  • Move credentials to environment variables or configuration files")
        if any(c["name"] == "Error handling" and not c["passed"] for c in results["checks"]):
            print("  • Add try-catch blocks and error handling throughout the code")
    
    print("\n" + "="*60 + "\n")

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    project_dir = sys.argv[1]
    
    try:
        validator = ProjectValidator(project_dir)
        results = validator.run_all_checks()
        print_report(results)
        
        # Exit with non-zero code if score is below 75
        if results["score"] < 75:
            sys.exit(1)
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
