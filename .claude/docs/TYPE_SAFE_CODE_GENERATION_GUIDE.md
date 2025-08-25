# Type-Safe Python Code Generation Guide

## Executive Summary

This guide provides comprehensive patterns, templates, and best practices for generating type-safe Python code from the start, avoiding pyright errors proactively rather than fixing them retroactively.

## Core Principles

### 1. Always Start with Full Type Annotations
**Never write untyped code.** Every function, method, class attribute, and variable should have explicit type annotations from the moment of creation.

### 2. Use Strict Type Checking from Day One
Configure pyright in strict mode and validate code as you write it, not after.

### 3. Design with Types First
Before implementing, define your type interfaces, protocols, and data structures.

## Common Type Error Patterns and Prevention

### 1. Optional/None Handling

**BAD - Creates type errors:**
```python
def process_data(data):
    return data.value  # Error if data is None

class Config:
    def __init__(self):
        self.settings = None  # Type unclear
```

**GOOD - Type-safe from start:**
```python
from typing import Optional

def process_data(data: Optional[DataClass]) -> Optional[str]:
    if data is None:
        return None
    return data.value

class Config:
    def __init__(self) -> None:
        self.settings: Optional[Dict[str, Any]] = None
```

### 2. Dataclass Field Initialization

**BAD - Mutable default arguments:**
```python
@dataclass
class TaskConfig:
    tasks: List[str] = []  # Shared mutable default!
    metadata: Dict[str, Any] = {}  # Shared mutable default!
    created_at: datetime = None  # Should be Optional
```

**GOOD - Proper field factories:**
```python
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime

@dataclass
class TaskConfig:
    tasks: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    # Or with factory for current time:
    # created_at: datetime = field(default_factory=datetime.now)
```

### 3. Import Management

**BAD - Untyped conditional imports:**
```python
try:
    from rich import Table
except ImportError:
    Table = None  # Type checker doesn't understand this
```

**GOOD - Typed conditional imports:**
```python
from typing import TYPE_CHECKING, Optional, Any

if TYPE_CHECKING:
    from rich import Table
else:
    try:
        from rich import Table
    except ImportError:
        Table = Any  # type: ignore[misc,assignment]

# Or create a proper stub:
class TableStub:
    """Stub for rich.Table when not available."""
    def add_column(self, *args: Any, **kwargs: Any) -> None: ...
    def add_row(self, *args: Any, **kwargs: Any) -> None: ...

try:
    from rich import Table
except ImportError:
    Table = TableStub  # type: ignore[misc,assignment]
```

### 4. Enum and Constants

**BAD - Undefined enums:**
```python
def process_stage(stage):
    if stage == WorkflowStage.INITIALIZATION:  # WorkflowStage not defined
        pass
```

**GOOD - Define enums upfront:**
```python
from enum import Enum, auto

class WorkflowStage(Enum):
    INITIALIZATION = auto()
    PROMPT_ANALYSIS = auto()
    TASK_PREPARATION = auto()
    ISSUE_CREATION = auto()
    BRANCH_SETUP = auto()
    RESEARCH_PLANNING = auto()
    IMPLEMENTATION_START = auto()
    IMPLEMENTATION_PROGRESS = auto()
    IMPLEMENTATION_COMPLETE = auto()
    TESTING_START = auto()
    DOCUMENTATION_UPDATE = auto()
    PR_PREPARATION = auto()
    PR_CREATION = auto()
    PR_VERIFICATION = auto()
    REVIEW_PROCESSING = auto()
    FINAL_CLEANUP = auto()

def process_stage(stage: WorkflowStage) -> None:
    if stage == WorkflowStage.INITIALIZATION:
        pass
```

### 5. Generic Types and Protocols

**BAD - Untyped generic operations:**
```python
def process_items(items):
    return [transform(item) for item in items]
```

**GOOD - Properly typed generics:**
```python
from typing import TypeVar, List, Callable, Protocol

T = TypeVar('T')
U = TypeVar('U')

class Transformable(Protocol):
    def transform(self) -> str: ...

def process_items(
    items: List[T], 
    transform: Callable[[T], U]
) -> List[U]:
    return [transform(item) for item in items]

# Or with protocol:
def process_transformables(items: List[Transformable]) -> List[str]:
    return [item.transform() for item in items]
```

## Type-Safe Code Templates

### 1. Base Class Template

```python
"""Module docstring."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
    Union,
    Protocol,
    TypeVar,
    Generic,
    Callable,
    ClassVar,
    Final,
    Literal,
    TypeAlias,
    cast,
    overload,
)

# Type aliases
ConfigDict: TypeAlias = Dict[str, Any]
ErrorCallback: TypeAlias = Callable[[Exception], None]

# Type variables
T = TypeVar('T')
T_co = TypeVar('T_co', covariant=True)
T_contra = TypeVar('T_contra', contravariant=True)

# Constants with type annotations
DEFAULT_TIMEOUT: Final[int] = 30
MAX_RETRIES: Final[int] = 3

logger: logging.Logger = logging.getLogger(__name__)


class Status(Enum):
    """Status enumeration."""
    
    PENDING = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()


@dataclass
class Configuration:
    """Configuration with proper defaults."""
    
    name: str
    timeout: int = DEFAULT_TIMEOUT
    retries: int = MAX_RETRIES
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    
    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        if self.timeout <= 0:
            raise ValueError(f"Timeout must be positive: {self.timeout}")
        if self.retries < 0:
            raise ValueError(f"Retries cannot be negative: {self.retries}")


class BaseProcessor(ABC, Generic[T]):
    """Abstract base processor with generics."""
    
    def __init__(self, config: Configuration) -> None:
        """Initialize processor.
        
        Args:
            config: Configuration object.
        """
        self.config: Configuration = config
        self.status: Status = Status.PENDING
        self._cache: Dict[str, T] = {}
    
    @abstractmethod
    def process(self, item: T) -> T:
        """Process an item.
        
        Args:
            item: Item to process.
            
        Returns:
            Processed item.
        """
        ...
    
    def process_batch(self, items: List[T]) -> List[T]:
        """Process multiple items.
        
        Args:
            items: Items to process.
            
        Returns:
            List of processed items.
        """
        results: List[T] = []
        for item in items:
            try:
                result = self.process(item)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to process item: {e}")
                self._handle_error(e, item)
        return results
    
    def _handle_error(self, error: Exception, item: T) -> None:
        """Handle processing error.
        
        Args:
            error: The exception that occurred.
            item: The item that caused the error.
        """
        self.status = Status.FAILED
        logger.error(f"Error processing {item}: {error}")
```

### 2. Service Class Template

```python
"""Service implementation with full typing."""

from __future__ import annotations

import asyncio
import json
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Dict, List, Optional, Set

import aiohttp
from aiohttp import ClientSession, ClientError


@dataclass
class ServiceConfig:
    """Service configuration."""
    
    base_url: str
    timeout: float = 30.0
    max_retries: int = 3
    headers: Dict[str, str] = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        """Validate and normalize configuration."""
        if not self.base_url:
            raise ValueError("base_url is required")
        # Ensure URL ends without slash for consistent joining
        self.base_url = self.base_url.rstrip('/')


@dataclass
class ServiceResponse:
    """Typed service response."""
    
    status_code: int
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    headers: Dict[str, str] = field(default_factory=dict)
    
    @property
    def is_success(self) -> bool:
        """Check if response indicates success."""
        return 200 <= self.status_code < 300
    
    @property
    def is_error(self) -> bool:
        """Check if response indicates error."""
        return self.status_code >= 400


class APIService:
    """Async API service with full typing."""
    
    def __init__(self, config: ServiceConfig) -> None:
        """Initialize service.
        
        Args:
            config: Service configuration.
        """
        self.config: ServiceConfig = config
        self._session: Optional[ClientSession] = None
        self._active_requests: Set[str] = set()
    
    async def __aenter__(self) -> APIService:
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[Any]
    ) -> None:
        """Async context manager exit."""
        await self.disconnect()
    
    async def connect(self) -> None:
        """Connect to the service."""
        if self._session is None:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self._session = ClientSession(
                headers=self.config.headers,
                timeout=timeout
            )
    
    async def disconnect(self) -> None:
        """Disconnect from the service."""
        if self._session:
            await self._session.close()
            self._session = None
    
    async def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None
    ) -> ServiceResponse:
        """Make GET request.
        
        Args:
            endpoint: API endpoint.
            params: Query parameters.
            
        Returns:
            Service response.
        """
        return await self._request('GET', endpoint, params=params)
    
    async def post(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None
    ) -> ServiceResponse:
        """Make POST request.
        
        Args:
            endpoint: API endpoint.
            data: Form data.
            json_data: JSON data.
            
        Returns:
            Service response.
        """
        return await self._request(
            'POST', 
            endpoint, 
            data=data, 
            json_data=json_data
        )
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None
    ) -> ServiceResponse:
        """Make HTTP request with retries.
        
        Args:
            method: HTTP method.
            endpoint: API endpoint.
            params: Query parameters.
            data: Form data.
            json_data: JSON data.
            
        Returns:
            Service response.
        """
        if not self._session:
            await self.connect()
        
        assert self._session is not None  # Type narrowing
        
        url = f"{self.config.base_url}/{endpoint.lstrip('/')}"
        request_id = f"{method}:{endpoint}"
        
        # Prevent duplicate requests
        if request_id in self._active_requests:
            return ServiceResponse(
                status_code=429,
                error="Duplicate request in progress"
            )
        
        self._active_requests.add(request_id)
        
        try:
            for attempt in range(self.config.max_retries):
                try:
                    async with self._session.request(
                        method,
                        url,
                        params=params,
                        data=data,
                        json=json_data
                    ) as response:
                        data_dict: Optional[Dict[str, Any]] = None
                        error_msg: Optional[str] = None
                        
                        try:
                            data_dict = await response.json()
                        except (json.JSONDecodeError, ContentTypeError):
                            text = await response.text()
                            if response.status >= 400:
                                error_msg = text
                        
                        return ServiceResponse(
                            status_code=response.status,
                            data=data_dict,
                            error=error_msg,
                            headers=dict(response.headers)
                        )
                        
                except ClientError as e:
                    if attempt == self.config.max_retries - 1:
                        return ServiceResponse(
                            status_code=500,
                            error=str(e)
                        )
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    
        finally:
            self._active_requests.discard(request_id)
        
        return ServiceResponse(
            status_code=500,
            error="Max retries exceeded"
        )
```

### 3. Test Template with Full Typing

```python
"""Test module with complete type annotations."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from pytest import FixtureRequest, MonkeyPatch


class TestConfiguration:
    """Test configuration with full typing."""
    
    @pytest.fixture
    def mock_config(self) -> Configuration:
        """Create mock configuration.
        
        Returns:
            Mock configuration object.
        """
        return Configuration(
            name="test",
            timeout=10,
            retries=2,
            tags=["test", "mock"],
            metadata={"test": True}
        )
    
    @pytest.fixture
    def temp_dir(self, tmp_path: Path) -> Path:
        """Create temporary directory.
        
        Args:
            tmp_path: Pytest tmp_path fixture.
            
        Returns:
            Path to temporary directory.
        """
        test_dir = tmp_path / "test_data"
        test_dir.mkdir(exist_ok=True)
        return test_dir
    
    def test_configuration_init(self) -> None:
        """Test configuration initialization."""
        config = Configuration(name="test")
        assert config.name == "test"
        assert config.timeout == DEFAULT_TIMEOUT
        assert config.retries == MAX_RETRIES
        assert isinstance(config.tags, list)
        assert len(config.tags) == 0
        assert isinstance(config.metadata, dict)
        assert len(config.metadata) == 0
        assert isinstance(config.created_at, datetime)
        assert config.updated_at is None
    
    def test_configuration_validation(self) -> None:
        """Test configuration validation."""
        with pytest.raises(ValueError, match="Timeout must be positive"):
            Configuration(name="test", timeout=0)
        
        with pytest.raises(ValueError, match="Retries cannot be negative"):
            Configuration(name="test", retries=-1)
    
    @pytest.mark.parametrize(
        "timeout,retries,expected_valid",
        [
            (10, 3, True),
            (0, 3, False),
            (10, -1, False),
            (1, 0, True),
        ]
    )
    def test_configuration_validation_parametrized(
        self,
        timeout: int,
        retries: int,
        expected_valid: bool
    ) -> None:
        """Test configuration validation with parameters.
        
        Args:
            timeout: Timeout value to test.
            retries: Retries value to test.
            expected_valid: Expected validation result.
        """
        if expected_valid:
            config = Configuration(name="test", timeout=timeout, retries=retries)
            assert config.timeout == timeout
            assert config.retries == retries
        else:
            with pytest.raises(ValueError):
                Configuration(name="test", timeout=timeout, retries=retries)


class TestAPIService:
    """Test API service with async support."""
    
    @pytest.fixture
    async def service(self) -> AsyncIterator[APIService]:
        """Create API service fixture.
        
        Yields:
            Configured API service.
        """
        config = ServiceConfig(
            base_url="https://api.example.com",
            timeout=5.0,
            max_retries=2
        )
        service = APIService(config)
        await service.connect()
        yield service
        await service.disconnect()
    
    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        """Create mock aiohttp session.
        
        Returns:
            Mock ClientSession.
        """
        session = AsyncMock(spec=ClientSession)
        session.request = AsyncMock()
        session.close = AsyncMock()
        return session
    
    @pytest.mark.asyncio
    async def test_get_request(
        self,
        service: APIService,
        mock_session: AsyncMock
    ) -> None:
        """Test GET request.
        
        Args:
            service: API service fixture.
            mock_session: Mock session fixture.
        """
        # Setup mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"result": "success"})
        mock_response.headers = {"Content-Type": "application/json"}
        
        mock_session.request.return_value.__aenter__.return_value = mock_response
        
        with patch.object(service, '_session', mock_session):
            response = await service.get("/test")
            
            assert response.status_code == 200
            assert response.data == {"result": "success"}
            assert response.is_success
            assert not response.is_error
            
            mock_session.request.assert_called_once_with(
                'GET',
                'https://api.example.com/test',
                params=None,
                data=None,
                json=None
            )
    
    @pytest.mark.asyncio
    async def test_post_request_with_json(
        self,
        service: APIService,
        mock_session: AsyncMock
    ) -> None:
        """Test POST request with JSON data.
        
        Args:
            service: API service fixture.
            mock_session: Mock session fixture.
        """
        # Setup mock response
        mock_response = AsyncMock()
        mock_response.status = 201
        mock_response.json = AsyncMock(return_value={"id": 123})
        mock_response.headers = {}
        
        mock_session.request.return_value.__aenter__.return_value = mock_response
        
        post_data = {"name": "test", "value": 42}
        
        with patch.object(service, '_session', mock_session):
            response = await service.post("/create", json_data=post_data)
            
            assert response.status_code == 201
            assert response.data == {"id": 123}
            assert response.is_success
            
            mock_session.request.assert_called_once_with(
                'POST',
                'https://api.example.com/create',
                params=None,
                data=None,
                json=post_data
            )
```

## Type-Safe Patterns by Category

### 1. Error Handling Pattern

```python
from typing import Optional, Union, Literal, TypeVar, Generic
from dataclasses import dataclass

T = TypeVar('T')

@dataclass
class Result(Generic[T]):
    """Type-safe result wrapper."""
    
    success: bool
    value: Optional[T] = None
    error: Optional[str] = None
    
    @classmethod
    def ok(cls, value: T) -> Result[T]:
        """Create success result."""
        return cls(success=True, value=value, error=None)
    
    @classmethod
    def fail(cls, error: str) -> Result[T]:
        """Create failure result."""
        return cls(success=False, value=None, error=error)
    
    def unwrap(self) -> T:
        """Unwrap value or raise."""
        if not self.success or self.value is None:
            raise ValueError(f"Cannot unwrap failed result: {self.error}")
        return self.value
    
    def unwrap_or(self, default: T) -> T:
        """Unwrap value or return default."""
        if self.success and self.value is not None:
            return self.value
        return default


def safe_divide(a: float, b: float) -> Result[float]:
    """Safe division with Result type."""
    if b == 0:
        return Result.fail("Division by zero")
    return Result.ok(a / b)
```

### 2. State Machine Pattern

```python
from enum import Enum, auto
from typing import Dict, Set, Optional, Callable, Any
from dataclasses import dataclass, field

class State(Enum):
    """State enumeration."""
    IDLE = auto()
    RUNNING = auto()
    PAUSED = auto()
    COMPLETED = auto()
    FAILED = auto()

@dataclass
class Transition:
    """State transition definition."""
    from_state: State
    to_state: State
    condition: Optional[Callable[[Any], bool]] = None
    action: Optional[Callable[[Any], None]] = None

class StateMachine:
    """Type-safe state machine."""
    
    def __init__(self, initial_state: State) -> None:
        self.current_state: State = initial_state
        self.transitions: Dict[State, Set[Transition]] = {}
        self.state_handlers: Dict[State, Callable[[Any], None]] = {}
    
    def add_transition(
        self,
        from_state: State,
        to_state: State,
        condition: Optional[Callable[[Any], bool]] = None,
        action: Optional[Callable[[Any], None]] = None
    ) -> None:
        """Add state transition."""
        if from_state not in self.transitions:
            self.transitions[from_state] = set()
        
        transition = Transition(from_state, to_state, condition, action)
        self.transitions[from_state].add(transition)
    
    def add_state_handler(
        self,
        state: State,
        handler: Callable[[Any], None]
    ) -> None:
        """Add state entry handler."""
        self.state_handlers[state] = handler
    
    def can_transition_to(self, target_state: State, context: Any = None) -> bool:
        """Check if transition is possible."""
        if self.current_state not in self.transitions:
            return False
        
        for transition in self.transitions[self.current_state]:
            if transition.to_state == target_state:
                if transition.condition is None:
                    return True
                return transition.condition(context)
        
        return False
    
    def transition_to(self, target_state: State, context: Any = None) -> bool:
        """Execute state transition."""
        if not self.can_transition_to(target_state, context):
            return False
        
        # Find and execute transition
        for transition in self.transitions[self.current_state]:
            if transition.to_state == target_state:
                if transition.condition is None or transition.condition(context):
                    # Execute transition action
                    if transition.action:
                        transition.action(context)
                    
                    # Update state
                    self.current_state = target_state
                    
                    # Execute state handler
                    if target_state in self.state_handlers:
                        self.state_handlers[target_state](context)
                    
                    return True
        
        return False
```

### 3. Builder Pattern with Types

```python
from __future__ import annotations
from typing import Optional, List, Dict, Any, TypeVar, Generic
from dataclasses import dataclass, field

T = TypeVar('T')

@dataclass
class QueryBuilder:
    """Type-safe SQL query builder."""
    
    _table: Optional[str] = None
    _select_fields: List[str] = field(default_factory=list)
    _where_conditions: List[str] = field(default_factory=list)
    _order_by: Optional[str] = None
    _limit: Optional[int] = None
    
    def table(self, name: str) -> QueryBuilder:
        """Set table name."""
        self._table = name
        return self
    
    def select(self, *fields: str) -> QueryBuilder:
        """Add select fields."""
        self._select_fields.extend(fields)
        return self
    
    def where(self, condition: str) -> QueryBuilder:
        """Add where condition."""
        self._where_conditions.append(condition)
        return self
    
    def order_by(self, field: str, direction: Literal["ASC", "DESC"] = "ASC") -> QueryBuilder:
        """Set order by."""
        self._order_by = f"{field} {direction}"
        return self
    
    def limit(self, count: int) -> QueryBuilder:
        """Set limit."""
        if count <= 0:
            raise ValueError("Limit must be positive")
        self._limit = count
        return self
    
    def build(self) -> str:
        """Build SQL query."""
        if not self._table:
            raise ValueError("Table name is required")
        
        # Build SELECT clause
        fields = ", ".join(self._select_fields) if self._select_fields else "*"
        query = f"SELECT {fields} FROM {self._table}"
        
        # Add WHERE clause
        if self._where_conditions:
            conditions = " AND ".join(self._where_conditions)
            query += f" WHERE {conditions}"
        
        # Add ORDER BY
        if self._order_by:
            query += f" ORDER BY {self._order_by}"
        
        # Add LIMIT
        if self._limit:
            query += f" LIMIT {self._limit}"
        
        return query

# Usage with full type safety
query: str = (
    QueryBuilder()
    .table("users")
    .select("id", "name", "email")
    .where("active = 1")
    .where("created_at > '2024-01-01'")
    .order_by("created_at", "DESC")
    .limit(10)
    .build()
)
```

## Tools and Libraries for Type-Safe Code Generation

### 1. Pydantic for Data Validation

```python
from pydantic import BaseModel, Field, validator, root_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class TaskModel(BaseModel):
    """Pydantic model with automatic validation."""
    
    id: int
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    priority: Priority = Priority.MEDIUM
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    completed: bool = False
    
    @validator('title')
    def title_must_be_capitalized(cls, v: str) -> str:
        """Validate title format."""
        if not v[0].isupper():
            raise ValueError('Title must start with capital letter')
        return v
    
    @root_validator
    def check_critical_priority(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Validate critical priority tasks."""
        priority = values.get('priority')
        description = values.get('description')
        
        if priority == Priority.CRITICAL and not description:
            raise ValueError('Critical tasks must have a description')
        
        return values
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
```

### 2. Attrs for Class Generation

```python
import attr
from typing import Optional, List, Dict, Any, ClassVar
from datetime import datetime

@attr.s(auto_attribs=True, frozen=True)
class ImmutableConfig:
    """Immutable configuration with attrs."""
    
    name: str
    version: str = "1.0.0"
    features: List[str] = attr.Factory(list)
    settings: Dict[str, Any] = attr.Factory(dict)
    
    @version.validator
    def check_version_format(self, attribute: attr.Attribute, value: str) -> None:
        """Validate version format."""
        parts = value.split('.')
        if len(parts) != 3:
            raise ValueError(f"Version must be X.Y.Z format: {value}")
        
        for part in parts:
            if not part.isdigit():
                raise ValueError(f"Version parts must be numeric: {value}")

@attr.s(auto_attribs=True)
class MutableService:
    """Mutable service with attrs."""
    
    config: ImmutableConfig
    _state: str = attr.ib(default="idle", init=False)
    _cache: Dict[str, Any] = attr.Factory(dict)
    
    MAX_CACHE_SIZE: ClassVar[int] = 100
    
    def __attrs_post_init__(self) -> None:
        """Post-initialization hook."""
        print(f"Service initialized with config: {self.config.name}")
    
    @property
    def state(self) -> str:
        """Get current state."""
        return self._state
    
    @state.setter
    def state(self, value: str) -> None:
        """Set state with validation."""
        valid_states = {"idle", "running", "stopped"}
        if value not in valid_states:
            raise ValueError(f"Invalid state: {value}")
        self._state = value
```

### 3. Code Generation with Jinja2

```python
from jinja2 import Template
from typing import List, Dict, Any
import black

# Type-safe code template
CLASS_TEMPLATE = Template("""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum, auto


class {{ class_name }}Status(Enum):
    \"\"\"Status enumeration for {{ class_name }}.\"\"\"
    {% for status in statuses %}
    {{ status.upper() }} = auto()
    {% endfor %}


@dataclass
class {{ class_name }}:
    \"\"\"{{ description }}\"\"\"
    
    # Required fields
    {% for field in required_fields %}
    {{ field.name }}: {{ field.type_hint }}
    {% endfor %}
    
    # Optional fields with defaults
    {% for field in optional_fields %}
    {{ field.name }}: {{ field.type_hint }} = {{ field.default }}
    {% endfor %}
    
    # Collections with factories
    {% for field in collection_fields %}
    {{ field.name }}: {{ field.type_hint }} = field(default_factory={{ field.factory }})
    {% endfor %}
    
    def __post_init__(self) -> None:
        \"\"\"Validate after initialization.\"\"\"
        {% for validation in validations %}
        {{ validation }}
        {% endfor %}
    
    {% for method in methods %}
    def {{ method.name }}(self{{ method.params }}) -> {{ method.return_type }}:
        \"\"\"{{ method.description }}\"\"\"
        {{ method.body | indent(8) }}
    {% endfor %}
""")

def generate_dataclass(
    class_name: str,
    description: str,
    fields: List[Dict[str, Any]],
    methods: List[Dict[str, Any]] = None
) -> str:
    """Generate type-safe dataclass code."""
    
    # Categorize fields
    required_fields = []
    optional_fields = []
    collection_fields = []
    
    for field in fields:
        if field.get('required', False):
            required_fields.append(field)
        elif field['type_hint'] in ['List[Any]', 'Dict[str, Any]', 'Set[str]']:
            field['factory'] = field['type_hint'].split('[')[0].lower()
            collection_fields.append(field)
        else:
            optional_fields.append(field)
    
    # Generate validations
    validations = []
    for field in required_fields:
        if 'str' in field['type_hint']:
            validations.append(
                f"if not self.{field['name']}:\n"
                f"    raise ValueError('{field['name']} cannot be empty')"
            )
    
    # Generate code
    code = CLASS_TEMPLATE.render(
        class_name=class_name,
        description=description,
        statuses=['pending', 'running', 'completed', 'failed'],
        required_fields=required_fields,
        optional_fields=optional_fields,
        collection_fields=collection_fields,
        validations=validations,
        methods=methods or []
    )
    
    # Format with black
    try:
        code = black.format_str(code, mode=black.Mode())
    except Exception:
        pass  # Return unformatted if black fails
    
    return code

# Example usage
generated_code = generate_dataclass(
    class_name="TaskProcessor",
    description="Process tasks with full type safety.",
    fields=[
        {"name": "task_id", "type_hint": "str", "required": True},
        {"name": "priority", "type_hint": "int", "default": "1"},
        {"name": "tags", "type_hint": "List[str]"},
        {"name": "metadata", "type_hint": "Dict[str, Any]"},
    ],
    methods=[
        {
            "name": "process",
            "params": "",
            "return_type": "bool",
            "description": "Process the task.",
            "body": "# Implementation here\nreturn True"
        }
    ]
)
```

## Pre-commit Hooks for Type Safety

### .pre-commit-config.yaml

```yaml
repos:
  # Type checking with pyright
  - repo: local
    hooks:
      - id: pyright
        name: pyright
        entry: pyright
        language: system
        types: [python]
        pass_filenames: false
        always_run: true
  
  # Type checking with mypy
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
        args: [--strict, --ignore-missing-imports]
  
  # Validate type stubs
  - repo: local
    hooks:
      - id: validate-stubs
        name: Validate type stubs
        entry: python scripts/validate_stubs.py
        language: system
        files: \.pyi$
  
  # Auto-generate type stubs for missing annotations
  - repo: local
    hooks:
      - id: stubgen
        name: Generate type stubs
        entry: stubgen
        language: system
        types: [python]
        pass_filenames: true
        args: [-o, stubs]
```

## Validation Script for Type Safety

```python
#!/usr/bin/env python3
"""Validate type safety before code generation."""

import ast
import sys
from pathlib import Path
from typing import List, Set, Tuple

class TypeSafetyValidator(ast.NodeVisitor):
    """Validate type safety in Python code."""
    
    def __init__(self) -> None:
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.untyped_functions: Set[str] = set()
        self.untyped_arguments: List[Tuple[str, str]] = []
    
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Check function definitions."""
        # Check return type annotation
        if node.returns is None and node.name != "__init__":
            self.untyped_functions.add(node.name)
            self.warnings.append(
                f"Function '{node.name}' lacks return type annotation"
            )
        
        # Check argument annotations
        for arg in node.args.args:
            if arg.annotation is None and arg.arg != "self":
                self.untyped_arguments.append((node.name, arg.arg))
                self.warnings.append(
                    f"Argument '{arg.arg}' in function '{node.name}' lacks type annotation"
                )
        
        self.generic_visit(node)
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Check async function definitions."""
        # Same checks as regular functions
        self.visit_FunctionDef(node)  # type: ignore
    
    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        """Check annotated assignments."""
        # Validate that annotation exists
        if node.annotation is None:
            self.warnings.append(
                f"Assignment lacks type annotation at line {node.lineno}"
            )
        self.generic_visit(node)
    
    def validate_file(self, filepath: Path) -> bool:
        """Validate a Python file.
        
        Args:
            filepath: Path to Python file.
            
        Returns:
            True if validation passes.
        """
        try:
            with open(filepath, 'r') as f:
                tree = ast.parse(f.read(), filename=str(filepath))
            
            self.visit(tree)
            
            if self.errors:
                print(f"\n❌ Errors in {filepath}:")
                for error in self.errors:
                    print(f"  - {error}")
                return False
            
            if self.warnings:
                print(f"\n⚠️  Warnings in {filepath}:")
                for warning in self.warnings:
                    print(f"  - {warning}")
            
            return len(self.errors) == 0
            
        except SyntaxError as e:
            print(f"❌ Syntax error in {filepath}: {e}")
            return False

def main() -> int:
    """Main validation function."""
    validator = TypeSafetyValidator()
    
    # Get files to validate
    files = sys.argv[1:] if len(sys.argv) > 1 else Path('.').rglob('*.py')
    
    all_valid = True
    for filepath in files:
        if isinstance(filepath, str):
            filepath = Path(filepath)
        
        if not validator.validate_file(filepath):
            all_valid = False
    
    # Summary
    if validator.untyped_functions:
        print(f"\n📊 Summary: {len(validator.untyped_functions)} untyped functions found")
    
    if validator.untyped_arguments:
        print(f"📊 Summary: {len(validator.untyped_arguments)} untyped arguments found")
    
    return 0 if all_valid else 1

if __name__ == "__main__":
    sys.exit(main())
```

## Summary and Best Practices

### Key Principles for Type-Safe Code Generation

1. **Always type from the start** - Never write untyped code
2. **Use strict mode** - Configure pyright/mypy in strict mode
3. **Validate continuously** - Run type checkers as you write
4. **Use type-safe patterns** - Follow established patterns
5. **Generate with types** - Use templates that include types
6. **Test type safety** - Include type checking in tests
7. **Document types** - Use type stubs and docstrings

### Common Pitfalls to Avoid

1. Using mutable defaults in dataclasses
2. Not handling Optional/None cases
3. Missing type annotations on class attributes
4. Untyped exception handling
5. Implicit Any types
6. Missing return type annotations
7. Untyped comprehensions and generators

### Tools to Use

1. **pyright/pylance** - Fast type checking
2. **mypy** - Comprehensive type checking
3. **pydantic** - Runtime validation with types
4. **attrs** - Class generation with validation
5. **beartype** - Runtime type checking decorator
6. **typeguard** - Runtime type enforcement

By following these patterns and using these tools, you can generate Python code that is type-safe from the start, avoiding the need for extensive post-generation fixes.