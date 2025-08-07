#!/usr/bin/env python3
"""
Code Writer Engine - Core logic for generating source code.
This provides programmatic access to code generation capabilities.
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any


class CodeWriterEngine:
    """Engine for generating source code from task descriptions."""

    def __init__(self):
        self.language_patterns = {
            "python": {
                "extensions": [".py"],
                "import_style": "import {module}",
                "class_template": "class {name}:",
                "function_template": "def {name}({params}):",
                "comment_style": "#",
                "docstring_style": '"""',
                "type_hints": True,
            },
            "javascript": {
                "extensions": [".js", ".ts"],
                "import_style": 'import {{ {items} }} from "{module}";',
                "class_template": "class {name} {{",
                "function_template": "function {name}({params}) {{",
                "comment_style": "//",
                "docstring_style": "/**",
                "type_hints": False,
            },
            "typescript": {
                "extensions": [".ts", ".tsx"],
                "import_style": 'import {{ {items} }} from "{module}";',
                "class_template": "class {name} {{",
                "function_template": "function {name}({params}): {return_type} {{",
                "comment_style": "//",
                "docstring_style": "/**",
                "type_hints": True,
            },
        }

        # Code templates for common patterns
        self.code_templates = {
            "python": {
                "auth_class": self._get_python_auth_template(),
                "api_endpoint": self._get_python_api_template(),
                "data_model": self._get_python_model_template(),
                "test_class": self._get_python_test_template(),
            },
            "javascript": {
                "api_endpoint": self._get_js_api_template(),
                "component": self._get_js_component_template(),
                "service": self._get_js_service_template(),
            },
        }

    def generate_code(
        self, task_description: str, context: Optional[Dict] = None
    ) -> Dict:
        """
        Generate source code based on task description.

        Args:
            task_description: Description of what code to generate
            context: Optional context about project structure, language, etc.

        Returns:
            Dictionary containing generated code and metadata
        """
        context = context or {}

        # Analyze the task to determine what to generate
        analysis = self._analyze_code_task(task_description, context)

        # Generate the code
        code_result = self._generate_code_implementation(analysis)

        result = {
            "success": True,
            "task": task_description,
            "analysis": analysis,
            "files": code_result.get("files", []),
            "dependencies": code_result.get("dependencies", []),
            "integration_notes": code_result.get("integration_notes", ""),
            "usage_examples": code_result.get("usage_examples", ""),
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "language": analysis["language"],
                "code_type": analysis["code_type"],
                "complexity": analysis["complexity"],
            },
        }

        return result

    def _analyze_code_task(self, task_description: str, context: Dict) -> Dict:
        """Analyze the task to determine what code to generate."""
        description_lower = task_description.lower()

        # Determine programming language
        language = context.get("language", self._detect_language(description_lower))

        # Determine code type
        code_type = self._determine_code_type(description_lower)

        # Extract key entities and components
        entities = self._extract_entities(task_description)

        # Determine complexity
        complexity = self._estimate_code_complexity(description_lower)

        analysis = {
            "original_task": task_description,
            "language": language,
            "code_type": code_type,
            "entities": entities,
            "complexity": complexity,
            "suggested_filename": self._suggest_filename(task_description, language),
            "dependencies": self._suggest_dependencies(description_lower, language),
        }

        return analysis

    def _detect_language(self, description: str) -> str:
        """Detect programming language from task description."""
        # Look for explicit language mentions (more specific first)
        if any(word in description for word in ["typescript", "ts"]) and not any(
            word in description for word in ["rest"]
        ):
            return "typescript"
        elif any(
            word in description
            for word in ["python", "py", "flask", "django", "fastapi"]
        ):
            return "python"
        elif any(
            word in description
            for word in ["javascript", "js", "node", "express", "react"]
        ):
            return "javascript"
        elif any(word in description for word in ["angular", "vue"]):
            return "typescript"

        # Default to Python for general tasks (including REST API)
        return "python"

    def _determine_code_type(self, description: str) -> str:
        """Determine the type of code to generate."""
        # Check API first since it's more specific than auth
        if any(word in description for word in ["api", "endpoint", "rest", "route"]):
            return "api_endpoint"
        elif (
            any(word in description for word in ["auth", "login", "authentication"])
            and "api" not in description
        ):
            return "authentication"
        elif any(
            word in description for word in ["model", "database", "data", "schema"]
        ):
            return "data_model"
        elif any(word in description for word in ["test", "testing", "unit test"]):
            return "test_class"
        elif any(word in description for word in ["class", "service", "handler"]):
            return "service_class"
        elif any(word in description for word in ["component", "ui", "interface"]):
            return "component"
        else:
            return "general_class"

    def _extract_entities(self, task_description: str) -> List[str]:
        """Extract key entities (classes, functions, etc.) from description."""
        entities = []

        # Look for class names (capitalized words)
        class_matches = re.findall(r"\b[A-Z][a-z]+(?:[A-Z][a-z]+)*\b", task_description)
        entities.extend(class_matches)

        # Look for common entity words
        entity_patterns = [
            r"\b(user|admin|customer|product|order|item)\b",
            r"\b(auth|authentication|login|signup)\b",
            r"\b(api|endpoint|route|handler)\b",
            r"\b(model|schema|data)\b",
        ]

        for pattern in entity_patterns:
            matches = re.findall(pattern, task_description.lower())
            entities.extend(matches)

        # Remove duplicates and return
        return list(set(entities))

    def _estimate_code_complexity(self, description: str) -> str:
        """Estimate the complexity of the code to generate."""
        complexity_indicators = {
            "high": [
                "system",
                "architecture",
                "complex",
                "advanced",
                "integration",
                "multiple",
            ],
            "medium": ["class", "service", "api", "model", "handler", "component"],
            "low": ["function", "method", "simple", "basic", "single"],
        }

        for level, indicators in complexity_indicators.items():
            if any(indicator in description for indicator in indicators):
                return level

        return "medium"  # Default

    def _suggest_filename(self, task_description: str, language: str) -> str:
        """Suggest a filename based on the task description."""
        # Clean the description
        clean_desc = re.sub(r"[^\w\s]", "", task_description.lower())
        clean_desc = re.sub(r"\s+", "_", clean_desc.strip())

        # Limit length
        if len(clean_desc) > 40:
            clean_desc = clean_desc[:40]

        # Remove common prefixes
        clean_desc = re.sub(r"^(create|add|implement|build)\s*", "", clean_desc)

        # Get appropriate extension
        extension = self.language_patterns[language]["extensions"][0]

        return f"{clean_desc}{extension}"

    def _suggest_dependencies(self, description: str, language: str) -> List[str]:
        """Suggest dependencies based on description and language."""
        dependencies = []

        if language == "python":
            if any(word in description for word in ["auth", "password", "hash"]):
                dependencies.extend(["hashlib", "secrets"])
            if any(word in description for word in ["api", "web", "http"]):
                dependencies.extend(["fastapi", "requests"])
            if any(word in description for word in ["database", "sql", "db"]):
                dependencies.extend(["sqlalchemy", "sqlite3"])
            if any(word in description for word in ["test", "testing"]):
                dependencies.extend(["unittest", "pytest"])

        elif language in ["javascript", "typescript"]:
            if any(word in description for word in ["api", "http"]):
                dependencies.extend(["axios", "express"])
            if any(word in description for word in ["test", "testing"]):
                dependencies.extend(["jest", "mocha"])
            if any(word in description for word in ["component", "ui"]):
                dependencies.extend(["react", "vue"])

        return list(set(dependencies))

    def _generate_code_implementation(self, analysis: Dict) -> Dict:
        """Generate the actual code implementation."""
        language = analysis["language"]
        code_type = analysis["code_type"]

        if language == "python":
            return self._generate_python_code(analysis)
        elif language in ["javascript", "typescript"]:
            return self._generate_js_code(analysis)
        else:
            return self._generate_generic_code(analysis)

    def _generate_python_code(self, analysis: Dict) -> Dict:
        """Generate Python code based on analysis."""
        code_type = analysis["code_type"]
        task = analysis["original_task"]
        entities = analysis["entities"]

        if code_type == "authentication":
            return self._create_python_auth_code(analysis)
        elif code_type == "api_endpoint":
            return self._create_python_api_code(analysis)
        elif code_type == "data_model":
            return self._create_python_generic_code(analysis)  # Use generic for now
        elif code_type == "test_class":
            return self._create_python_generic_code(analysis)  # Use generic for now
        else:
            return self._create_python_generic_code(analysis)

    def _create_python_auth_code(self, analysis: Dict) -> Dict:
        """Create Python authentication code."""
        filename = analysis["suggested_filename"]

        code = '''#!/usr/bin/env python3
"""
User authentication module with secure password handling.
Generated by Gadugi v0.3 Code Writer Agent.
"""

import hashlib
import secrets
from typing import Optional, Dict
from dataclasses import dataclass


@dataclass
class User:
    """User data model for authentication."""
    id: int
    email: str
    password_hash: str
    salt: str
    is_active: bool = True


class UserAuthenticator:
    """
    Handles user authentication with secure password management.
    
    Features:
    - Secure password hashing with salt
    - Email validation
    - User session management
    """
    
    def __init__(self, user_store: Optional[Dict[str, User]] = None):
        """Initialize authenticator with optional user store."""
        self.users = user_store or {}
    
    def hash_password(self, password: str, salt: str = None) -> tuple[str, str]:
        """
        Hash password with salt for secure storage.
        
        Args:
            password: Plain text password
            salt: Optional salt (generated if not provided)
            
        Returns:
            Tuple of (password_hash, salt)
        """
        if salt is None:
            salt = secrets.token_hex(32)
        
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000  # iterations
        )
        
        return password_hash.hex(), salt
    
    def create_user(self, email: str, password: str, user_id: int = None) -> Optional[User]:
        """
        Create new user with email and password.
        
        Args:
            email: User email address
            password: Plain text password
            user_id: Optional user ID
            
        Returns:
            User object if creation successful, None otherwise
        """
        if not self._validate_email(email):
            raise ValueError("Invalid email format")
        
        if email in self.users:
            raise ValueError("User already exists")
        
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters")
        
        password_hash, salt = self.hash_password(password)
        user_id = user_id or len(self.users) + 1
        
        user = User(
            id=user_id,
            email=email,
            password_hash=password_hash,
            salt=salt
        )
        
        self.users[email] = user
        return user
    
    def authenticate(self, email: str, password: str) -> Optional[User]:
        """
        Authenticate user with email and password.
        
        Args:
            email: User email
            password: Plain text password
            
        Returns:
            User object if authentication successful, None otherwise
        """
        user = self.users.get(email)
        if not user or not user.is_active:
            return None
        
        password_hash, _ = self.hash_password(password, user.salt)
        
        if password_hash == user.password_hash:
            return user
        
        return None
    
    def _validate_email(self, email: str) -> bool:
        """Basic email validation."""
        return '@' in email and '.' in email.split('@')[1]


def main():
    """Example usage of the authentication system."""
    auth = UserAuthenticator()
    
    try:
        # Create user
        user = auth.create_user("user@example.com", "secure_password123")
        print(f"✅ Created user: {user.email}")
        
        # Authenticate
        authenticated_user = auth.authenticate("user@example.com", "secure_password123")
        if authenticated_user:
            print(f"✅ Authentication successful for {authenticated_user.email}")
        else:
            print("❌ Authentication failed")
            
    except ValueError as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
'''

        return {
            "files": [
                {
                    "filename": filename,
                    "content": code,
                    "language": "python",
                    "description": "User authentication system with secure password handling",
                }
            ],
            "dependencies": ["hashlib", "secrets", "typing", "dataclasses"],
            "integration_notes": "Can be integrated with web frameworks like Flask/FastAPI. User store can be replaced with database integration.",
            "usage_examples": "auth = UserAuthenticator(); user = auth.create_user('user@example.com', 'password')",
        }

    def _create_python_api_code(self, analysis: Dict) -> Dict:
        """Create Python API endpoint code."""
        filename = analysis["suggested_filename"]
        entities = analysis["entities"]

        # Determine what kind of API to create
        api_name = "items"
        if any(entity in entities for entity in ["user", "users"]):
            api_name = "users"
        elif any(entity in entities for entity in ["product", "products"]):
            api_name = "products"
        elif any(entity in entities for entity in ["order", "orders"]):
            api_name = "orders"

        code = f'''#!/usr/bin/env python3
"""
{api_name.title()} API endpoints using FastAPI.
Generated by Gadugi v0.3 Code Writer Agent.
"""

from fastapi import FastAPI, HTTPException, Depends
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime


# Data models
class {api_name[:-1].title()}Base(BaseModel):
    """Base model for {api_name[:-1]} data."""
    name: str
    description: Optional[str] = None


class {api_name[:-1].title()}Create({api_name[:-1].title()}Base):
    """Model for creating a new {api_name[:-1]}."""
    pass


class {api_name[:-1].title()}Response({api_name[:-1].title()}Base):
    """Model for {api_name[:-1]} API responses."""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# In-memory storage (replace with database in production)
{api_name}_store: List[{api_name[:-1].title()}Response] = []
next_id = 1


# API App
app = FastAPI(title="{api_name.title()} API", version="1.0.0")


@app.get("/", tags=["health"])
async def health_check():
    """Health check endpoint."""
    return {{"message": "{api_name.title()} API is running", "status": "healthy"}}


@app.get("/{api_name}", response_model=List[{api_name[:-1].title()}Response], tags=["{api_name}"])
async def get_{api_name}(skip: int = 0, limit: int = 100):
    """
    Get list of {api_name}.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        List of {api_name}
    """
    return {api_name}_store[skip: skip + limit]


@app.get("/{api_name}/{{item_id}}", response_model={api_name[:-1].title()}Response, tags=["{api_name}"])
async def get_{api_name[:-1]}(item_id: int):
    """
    Get a specific {api_name[:-1]} by ID.
    
    Args:
        item_id: The ID of the {api_name[:-1]} to retrieve
        
    Returns:
        The requested {api_name[:-1]}
        
    Raises:
        HTTPException: If {api_name[:-1]} not found
    """
    for item in {api_name}_store:
        if item.id == item_id:
            return item
    
    raise HTTPException(status_code=404, detail="{api_name[:-1].title()} not found")


@app.post("/{api_name}", response_model={api_name[:-1].title()}Response, tags=["{api_name}"])
async def create_{api_name[:-1]}(item: {api_name[:-1].title()}Create):
    """
    Create a new {api_name[:-1]}.
    
    Args:
        item: The {api_name[:-1]} data to create
        
    Returns:
        The created {api_name[:-1]}
    """
    global next_id
    
    now = datetime.now()
    new_item = {api_name[:-1].title()}Response(
        id=next_id,
        name=item.name,
        description=item.description,
        created_at=now,
        updated_at=now
    )
    
    {api_name}_store.append(new_item)
    next_id += 1
    
    return new_item


@app.put("/{api_name}/{{item_id}}", response_model={api_name[:-1].title()}Response, tags=["{api_name}"])
async def update_{api_name[:-1]}(item_id: int, item: {api_name[:-1].title()}Create):
    """
    Update an existing {api_name[:-1]}.
    
    Args:
        item_id: The ID of the {api_name[:-1]} to update
        item: The updated {api_name[:-1]} data
        
    Returns:
        The updated {api_name[:-1]}
        
    Raises:
        HTTPException: If {api_name[:-1]} not found
    """
    for i, existing_item in enumerate({api_name}_store):
        if existing_item.id == item_id:
            updated_item = {api_name[:-1].title()}Response(
                id=item_id,
                name=item.name,
                description=item.description,
                created_at=existing_item.created_at,
                updated_at=datetime.now()
            )
            {api_name}_store[i] = updated_item
            return updated_item
    
    raise HTTPException(status_code=404, detail="{api_name[:-1].title()} not found")


@app.delete("/{api_name}/{{item_id}}", tags=["{api_name}"])
async def delete_{api_name[:-1]}(item_id: int):
    """
    Delete a {api_name[:-1]} by ID.
    
    Args:
        item_id: The ID of the {api_name[:-1]} to delete
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If {api_name[:-1]} not found
    """
    for i, item in enumerate({api_name}_store):
        if item.id == item_id:
            deleted_item = {api_name}_store.pop(i)
            return {{"message": f"{api_name[:-1].title()} {{deleted_item.name}} deleted successfully"}}
    
    raise HTTPException(status_code=404, detail="{api_name[:-1].title()} not found")


def main():
    """Run the API server."""
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
'''

        return {
            "files": [
                {
                    "filename": filename,
                    "content": code,
                    "language": "python",
                    "description": f"REST API endpoints for {api_name} using FastAPI",
                }
            ],
            "dependencies": ["fastapi", "uvicorn", "pydantic", "python-multipart"],
            "integration_notes": "Install dependencies: pip install fastapi uvicorn. Run with: uvicorn filename:app --reload",
            "usage_examples": "GET /items, POST /items, PUT /items/{id}, DELETE /items/{id}",
        }

    def _create_python_generic_code(self, analysis: Dict) -> Dict:
        """Create generic Python code."""
        filename = analysis["suggested_filename"]
        task = analysis["original_task"]
        entities = analysis["entities"]

        # Generate a basic class structure
        class_name = "TaskHandler"
        if entities:
            # Use first entity as class name
            class_name = entities[0].title().replace("_", "")

        code = f'''#!/usr/bin/env python3
"""
{task} - Generated by Gadugi v0.3 Code Writer Agent.
"""

from typing import Optional, Dict, List, Any
from datetime import datetime


class {class_name}:
    """
    Main class for handling: {task}
    
    This class provides the core functionality for the requested task.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the {class_name}.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {{}}
        self.created_at = datetime.now()
        self._data = {{}}
    
    def process(self, input_data: Any) -> Dict[str, Any]:
        """
        Main processing method for the task.
        
        Args:
            input_data: The input data to process
            
        Returns:
            Dictionary containing the processing results
        """
        try:
            # Process the input data
            result = self._handle_input(input_data)
            
            return {{
                "success": True,
                "result": result,
                "processed_at": datetime.now().isoformat()
            }}
            
        except Exception as e:
            return {{
                "success": False,
                "error": str(e),
                "processed_at": datetime.now().isoformat()
            }}
    
    def _handle_input(self, input_data: Any) -> Any:
        """
        Internal method to handle input data processing.
        
        Args:
            input_data: The data to process
            
        Returns:
            Processed result
        """
        # Default implementation - override in subclasses
        if isinstance(input_data, str):
            return input_data.upper()
        elif isinstance(input_data, (list, tuple)):
            return len(input_data)
        elif isinstance(input_data, dict):
            return list(input_data.keys())
        else:
            return str(input_data)
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the handler.
        
        Returns:
            Dictionary containing status information
        """
        return {{
            "class_name": self.__class__.__name__,
            "created_at": self.created_at.isoformat(),
            "config": self.config,
            "data_count": len(self._data)
        }}


def main():
    """Example usage of the {class_name}."""
    handler = {class_name}()
    
    # Example processing
    test_data = "sample input data"
    result = handler.process(test_data)
    
    print(f"Processing result: {{result}}")
    print(f"Handler status: {{handler.get_status()}}")


if __name__ == "__main__":
    main()
'''

        return {
            "files": [
                {
                    "filename": filename,
                    "content": code,
                    "language": "python",
                    "description": f"Generic Python class for: {task}",
                }
            ],
            "dependencies": ["typing", "datetime"],
            "integration_notes": "This is a generic implementation. Customize the _handle_input method for specific requirements.",
            "usage_examples": f"handler = {class_name}(); result = handler.process(data); print(handler.get_status())",
        }

    def _generate_js_code(self, analysis: Dict) -> Dict:
        """Generate JavaScript/TypeScript code."""
        # Placeholder for JS/TS code generation
        return self._create_js_generic_code(analysis)

    def _create_js_generic_code(self, analysis: Dict) -> Dict:
        """Create generic JavaScript code."""
        filename = analysis["suggested_filename"]
        task = analysis["original_task"]

        code = f"""/**
 * {task} - Generated by Gadugi v0.3 Code Writer Agent
 */

class TaskHandler {{
    constructor(config = {{}}) {{
        this.config = config;
        this.createdAt = new Date();
        this._data = {{}};
    }}
    
    /**
     * Main processing method for the task
     * @param {{any}} inputData - The input data to process
     * @returns {{Promise<Object>}} Processing results
     */
    async process(inputData) {{
        try {{
            const result = await this._handleInput(inputData);
            
            return {{
                success: true,
                result,
                processedAt: new Date().toISOString()
            }};
        }} catch (error) {{
            return {{
                success: false,
                error: error.message,
                processedAt: new Date().toISOString()
            }};
        }}
    }}
    
    /**
     * Internal method to handle input processing
     * @param {{any}} inputData - The data to process
     * @returns {{Promise<any>}} Processed result
     */
    async _handleInput(inputData) {{
        // Default implementation
        if (typeof inputData === 'string') {{
            return inputData.toUpperCase();
        }} else if (Array.isArray(inputData)) {{
            return inputData.length;
        }} else if (typeof inputData === 'object' && inputData !== null) {{
            return Object.keys(inputData);
        }} else {{
            return String(inputData);
        }}
    }}
    
    /**
     * Get current status
     * @returns {{Object}} Status information
     */
    getStatus() {{
        return {{
            className: this.constructor.name,
            createdAt: this.createdAt.toISOString(),
            config: this.config,
            dataCount: Object.keys(this._data).length
        }};
    }}
}}

// Example usage
async function main() {{
    const handler = new TaskHandler();
    const result = await handler.process("sample input data");
    
    console.log("Processing result:", result);
    console.log("Handler status:", handler.getStatus());
}}

// Export for Node.js or browser usage
if (typeof module !== 'undefined' && module.exports) {{
    module.exports = TaskHandler;
}} else if (typeof window !== 'undefined') {{
    window.TaskHandler = TaskHandler;
}}

// Run example if this is the main module
if (require.main === module) {{
    main().catch(console.error);
}}
"""

        return {
            "files": [
                {
                    "filename": filename,
                    "content": code,
                    "language": "javascript",
                    "description": f"Generic JavaScript class for: {task}",
                }
            ],
            "dependencies": [],
            "integration_notes": "Can be used in Node.js or browser environments. Supports both CommonJS and ES6 modules.",
            "usage_examples": "const handler = new TaskHandler(); await handler.process(data);",
        }

    def _generate_generic_code(self, analysis: Dict) -> Dict:
        """Generate generic code for unsupported languages."""
        return {
            "files": [
                {
                    "filename": "code_output.txt",
                    "content": f"Code generation requested for: {analysis['original_task']}\nLanguage: {analysis['language']}\nType: {analysis['code_type']}",
                    "language": "text",
                    "description": "Generic code output",
                }
            ],
            "dependencies": [],
            "integration_notes": "Language not fully supported yet",
            "usage_examples": "Manual implementation required",
        }

    # Template methods
    def _get_python_auth_template(self):
        pass

    def _get_python_api_template(self):
        pass

    def _get_python_model_template(self):
        pass

    def _get_python_test_template(self):
        pass

    def _get_js_api_template(self):
        pass

    def _get_js_component_template(self):
        pass

    def _get_js_service_template(self):
        pass


def generate_code_for_task(
    task_description: str, context: Optional[Dict] = None
) -> Dict:
    """
    Main function to generate code for a given task.

    Args:
        task_description: Description of the coding task
        context: Optional context (language, project info, etc.)

    Returns:
        Dictionary containing the generated code and metadata
    """
    engine = CodeWriterEngine()

    try:
        # Handle empty or invalid task descriptions
        if not task_description or not task_description.strip():
            task_description = "Generic code task"

        result = engine.generate_code(task_description, context)
        return result

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "task": task_description,
            "files": [],
            "dependencies": [],
            "integration_notes": "Error occurred during code generation",
            "usage_examples": "",
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "language": "unknown",
                "code_type": "error",
                "complexity": "unknown",
            },
        }


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python code_writer_engine.py <task_description>")
        print(
            "Example: python code_writer_engine.py 'Create user authentication class'"
        )
        sys.exit(1)

    task_description = " ".join(sys.argv[1:])
    result = generate_code_for_task(task_description)

    if result["success"]:
        print("Generated Code:")
        print("=" * 50)

        for file_info in result["files"]:
            print(f"\n📁 File: {file_info['filename']}")
            print(f"📝 Description: {file_info['description']}")
            print(f"🔤 Language: {file_info['language']}")
            print("\n" + "─" * 40)
            print(file_info["content"])
            print("─" * 40)

        if result["dependencies"]:
            print(f"\n📦 Dependencies: {', '.join(result['dependencies'])}")

        if result["integration_notes"]:
            print(f"\n🔧 Integration Notes: {result['integration_notes']}")

        if result["usage_examples"]:
            print(f"\n💡 Usage Examples: {result['usage_examples']}")

    else:
        print(f"❌ Error generating code: {result.get('error', 'Unknown error')}")
