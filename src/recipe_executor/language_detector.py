"""Language detection for Recipe Executor - determines target language from recipe."""

import re
from enum import Enum
from pathlib import Path


class Language(Enum):
    """Supported programming languages."""

    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    GO = "go"
    RUST = "rust"
    JAVA = "java"
    CSHARP = "csharp"
    CPP = "cpp"
    RUBY = "ruby"
    PHP = "php"
    SWIFT = "swift"
    KOTLIN = "kotlin"
    UNKNOWN = "unknown"


class LanguageDetector:
    """Detects the target programming language from recipe design document."""

    def detect_language(self, recipe_path: Path) -> Language:
        """Detect the target language for a recipe from design.md.

        Looks for explicit "Language: <language>" specification in design.md.
        Falls back to analyzing code blocks if no explicit specification.

        Args:
            recipe_path: Path to the recipe directory

        Returns:
            Detected Language enum value
        """
        # Check design.md for explicit language specification
        design_file = recipe_path / "design.md"
        if design_file.exists():
            content = design_file.read_text()

            # Look for explicit "Language: <language>" specification
            lang_match = re.search(r"^Language:\s*(\w+)", content, re.MULTILINE | re.IGNORECASE)
            if lang_match:
                return self._parse_language(lang_match.group(1))

            # Look for "Target Language: <language>" as alternative
            lang_match = re.search(
                r"^Target Language:\s*(\w+)", content, re.MULTILINE | re.IGNORECASE
            )
            if lang_match:
                return self._parse_language(lang_match.group(1))

            # Fall back to analyzing code blocks as last resort
            content_lower = content.lower()
            language_counts = {
                Language.PYTHON: content_lower.count("```python") + content_lower.count("```py"),
                Language.JAVASCRIPT: content_lower.count("```javascript")
                + content_lower.count("```js"),
                Language.TYPESCRIPT: content_lower.count("```typescript")
                + content_lower.count("```ts"),
                Language.GO: content_lower.count("```go"),
                Language.RUST: content_lower.count("```rust") + content_lower.count("```rs"),
                Language.JAVA: content_lower.count("```java"),
                Language.CSHARP: content_lower.count("```csharp") + content_lower.count("```cs"),
                Language.CPP: content_lower.count("```cpp") + content_lower.count("```c++"),
                Language.RUBY: content_lower.count("```ruby") + content_lower.count("```rb"),
                Language.PHP: content_lower.count("```php"),
                Language.SWIFT: content_lower.count("```swift"),
                Language.KOTLIN: content_lower.count("```kotlin") + content_lower.count("```kt"),
            }

            # Return the most common language in code blocks
            max_count = max(language_counts.values())
            if max_count > 0:
                for lang, count in language_counts.items():
                    if count == max_count:
                        return lang

        # Default to Python if no clear indication
        return Language.PYTHON

    def _parse_language(self, language_str: str) -> Language:
        """Parse a language string to Language enum.

        Args:
            language_str: String representation of language

        Returns:
            Corresponding Language enum value
        """
        language_lower = language_str.lower()

        # Direct matches
        for lang in Language:
            if lang.value == language_lower:
                return lang

        # Common aliases
        aliases = {
            "py": Language.PYTHON,
            "js": Language.JAVASCRIPT,
            "ts": Language.TYPESCRIPT,
            "rs": Language.RUST,
            "cs": Language.CSHARP,
            "c#": Language.CSHARP,
            "c++": Language.CPP,
            "rb": Language.RUBY,
            "kt": Language.KOTLIN,
        }

        if language_lower in aliases:
            return aliases[language_lower]

        return Language.UNKNOWN

    def get_file_extensions(self, language: Language) -> list[str]:
        """Get typical file extensions for a language.

        Args:
            language: Language enum value

        Returns:
            List of file extensions (with dots)
        """
        extensions = {
            Language.PYTHON: [".py", ".pyi", ".pyx"],
            Language.JAVASCRIPT: [".js", ".mjs", ".cjs"],
            Language.TYPESCRIPT: [".ts", ".tsx", ".d.ts"],
            Language.GO: [".go"],
            Language.RUST: [".rs"],
            Language.JAVA: [".java"],
            Language.CSHARP: [".cs"],
            Language.CPP: [".cpp", ".cc", ".cxx", ".h", ".hpp"],
            Language.RUBY: [".rb"],
            Language.PHP: [".php"],
            Language.SWIFT: [".swift"],
            Language.KOTLIN: [".kt", ".kts"],
        }

        return extensions.get(language, [])
