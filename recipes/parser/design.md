# Parser Recipe Design

## Architecture Overview
The Parser component reads markdown and JSON recipe files and converts them into structured Recipe objects using regex-based section extraction and JSON parsing.

## Technology Choices
- **Python 3.11+**: Built-in regex and json modules
- **Pydantic v2**: Data validation and serialization
- **Python-Markdown**: Optional enhanced markdown parsing
- **YAML**: Optional YAML front matter support

## Component Design

### Component: Markdown Parser (`markdown_parser.py`)
Parses markdown files into structured sections and content.

**Classes to implement:**
- `MarkdownSection(BaseModel)`: level, title, content, subsections, line_number
- `MarkdownParser`: Main parser class
- `SectionExtractor`: Extract sections by headers
- `ListParser`: Parse bullet and numbered lists
- `CodeBlockExtractor`: Extract code blocks with metadata

**Key methods:**
- `MarkdownParser.parse_file(path)`: Parse markdown file into sections
- `MarkdownParser.extract_sections()`: Extract all sections hierarchically
- `SectionExtractor.find_section(title)`: Find section by title/pattern
- `ListParser.parse_requirements_list()`: Parse requirement bullet lists
- `CodeBlockExtractor.extract_blocks()`: Get all code blocks with language

### Component: Requirements Parser (`requirements_parser.py`)
Converts requirements.md content into Requirements object.

**Classes to implement:**
- `RequirementsParser`: Parse requirements from markdown
- `RequirementExtractor`: Extract individual requirements
- `PriorityDetector`: Detect requirement priorities from text

**Key methods:**
- `RequirementsParser.parse(content)`: Parse requirements from markdown
- `RequirementExtractor.extract_functional()`: Get functional requirements
- `RequirementExtractor.extract_non_functional()`: Get non-functional requirements
- `PriorityDetector.detect_priority(text)`: Detect MUST/SHOULD/COULD

### Component: Design Parser (`design_parser.py`)
Converts design.md content into Design object.

**Classes to implement:**
- `DesignParser`: Parse design from markdown
- `ComponentExtractor`: Extract component designs
- `ArchitectureParser`: Parse architecture section

**Key methods:**
- `DesignParser.parse(content)`: Parse design from markdown
- `ComponentExtractor.extract_components()`: Get component designs
- `ArchitectureParser.parse_overview()`: Parse architecture overview

### Component: JSON Parser (`json_parser.py`)
Parses components.json and dependencies.json files.

**Classes to implement:**
- `JsonParser`: Generic JSON file parser
- `ComponentsParser`: Parse components.json
- `DependenciesParser`: Parse dependencies.json

**Key methods:**
- `JsonParser.parse_file(path)`: Parse JSON file with validation
- `ComponentsParser.parse_components()`: Parse into Components object
- `DependenciesParser.parse_dependencies()`: Parse dependency list

### Component: Recipe Builder (`recipe_builder.py`)
Assembles parsed pieces into complete Recipe object.

**Classes to implement:**
- `RecipeBuilder`: Build Recipe from parsed components
- `ValidationHelper`: Validate completeness
- `DefaultValueProvider`: Provide defaults for missing values

**Key methods:**
- `RecipeBuilder.build_recipe()`: Assemble complete Recipe
- `RecipeBuilder.validate_recipe()`: Check for required fields
- `ValidationHelper.check_completeness()`: Verify all sections present
- `DefaultValueProvider.provide_defaults()`: Fill in missing values

## Implementation Notes
- Use regex patterns for robust section detection
- Support both strict and lenient parsing modes
- Cache compiled regex patterns for performance
- Provide detailed error messages with line numbers
- Handle Windows and Unix line endings