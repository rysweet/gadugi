#!/usr/bin/env python3
"""
Analyze pyright errors and categorize them for systematic fixing.
"""

import re
import subprocess
from collections import defaultdict, Counter
from pathlib import Path


def run_pyright():
    """Run pyright and capture all errors."""
    try:
        result = subprocess.run(
            ["uv", "run", "pyright", "--stats"],
            capture_output=True,
            text=True,
            cwd=Path.cwd(),
        )
        # Pyright outputs to stderr
        output = result.stderr + result.stdout
        print(f"Captured {len(output)} characters of output")
        return output
    except Exception as e:
        print(f"Error running pyright: {e}")
        return ""


def categorize_errors(pyright_output):
    """Categorize pyright errors by type."""
    categories = defaultdict(list)
    lines = pyright_output.split("\n")

    for line in lines:
        if " - error:" in line or " - warning:" in line:
            # Extract error type
            if "Import" in line and "could not be resolved" in line:
                categories["missing_imports"].append(line)
            elif "is not defined" in line:
                categories["undefined_variables"].append(line)
            elif "Expected indented block" in line:
                categories["syntax_errors"].append(line)
            elif "is possibly unbound" in line:
                categories["unbound_variables"].append(line)
            elif "Arguments missing" in line:
                categories["missing_arguments"].append(line)
            elif "No parameter named" in line:
                categories["invalid_parameters"].append(line)
            elif 'Object of type "None"' in line:
                categories["none_access"].append(line)
            elif "is not accessed" in line:
                categories["unused_variables"].append(line)
            elif "not a known attribute" in line:
                categories["attribute_errors"].append(line)
            elif "not subscriptable" in line:
                categories["subscript_errors"].append(line)
            else:
                categories["other"].append(line)

    return categories


def analyze_file_patterns(categories):
    """Analyze which files have the most errors."""
    file_counts = Counter()

    for category, errors in categories.items():
        for error in errors:
            # Extract file path
            match = re.search(r"(/[^:]+):", error)
            if match:
                file_path = Path(match.group(1))
                # Get relative path for readability
                try:
                    rel_path = file_path.relative_to(Path.cwd())
                    file_counts[str(rel_path)] += 1
                except ValueError:
                    file_counts[str(file_path)] += 1

    return file_counts


def main():
    print("Analyzing pyright errors...")

    # Run pyright and get output
    output = run_pyright()
    if not output:
        print("No pyright output captured")
        return

    # Categorize errors
    categories = categorize_errors(output)

    print("\n=== ERROR CATEGORY ANALYSIS ===")
    total_issues = sum(len(errors) for errors in categories.values())

    for category, errors in sorted(
        categories.items(), key=lambda x: len(x[1]), reverse=True
    ):
        count = len(errors)
        percentage = (count / total_issues * 100) if total_issues > 0 else 0
        print(
            f"\n{category.upper().replace('_', ' ')}: {count} issues ({percentage:.1f}%)"
        )

        # Show a few examples
        for i, error in enumerate(errors[:3]):
            print(f"  Example {i + 1}: {error.strip()}")
        if len(errors) > 3:
            print(f"  ... and {len(errors) - 3} more")

    print(f"\nTOTAL ISSUES: {total_issues}")

    # Analyze file patterns
    print("\n=== FILES WITH MOST ERRORS ===")
    file_counts = analyze_file_patterns(categories)

    for file_path, count in file_counts.most_common(10):
        print(f"{file_path}: {count} errors")

    # Generate fixing strategy
    print("\n=== RECOMMENDED FIXING ORDER ===")
    print("1. Fix syntax errors first (blocks other analysis)")
    print("2. Fix missing imports (many errors cascade from these)")
    print("3. Fix undefined variables and unbound variables")
    print("4. Fix None access and optional handling")
    print("5. Fix unused variables and imports")
    print("6. Fix attribute and parameter errors")
    print("7. Address remaining issues")


if __name__ == "__main__":
    main()
