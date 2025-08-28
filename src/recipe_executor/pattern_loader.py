"""Design pattern loading and management for Recipe Executor."""

import json
import logging
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from dataclasses import asdict

from .recipe_model import DesignPattern, ComponentType

logger = logging.getLogger(__name__)


class PatternLoader:
    """Loads and manages design patterns for recipes."""
    
    def __init__(self, patterns_dir: Optional[Path] = None):
        """Initialize the pattern loader.
        
        Args:
            patterns_dir: Directory containing pattern definitions
        """
        self.patterns_dir = patterns_dir or Path("patterns")
        self.loaded_patterns: Dict[str, DesignPattern] = {}
        self.pattern_cache: Dict[str, str] = {}  # name -> content cache
        
        # Load built-in patterns
        self._load_builtin_patterns()
    
    def _load_builtin_patterns(self) -> None:
        """Load built-in design patterns."""
        # Factory pattern
        factory_pattern = DesignPattern(
            name="factory",
            template="",  # Template loaded from file
            category="creational",
            description="Factory pattern for creating objects",
            template_path=Path("patterns/factory.json"),
            applicable_to=[ComponentType.SERVICE, ComponentType.LIBRARY],
            required_components=["Factory", "AbstractProduct", "ConcreteProduct"],
            design_decisions={
                "creation": "Use factory methods for object creation",
                "abstraction": "Define product interfaces",
                "flexibility": "Allow runtime type selection"
            },
            code_templates={
                "factory_class": """
class {name}Factory:
    '''Factory for creating {name} instances.'''
    
    @staticmethod
    def create(type_name: str) -> {name}:
        '''Create instance based on type.'''
        if type_name == 'type1':
            return ConcreteType1()
        elif type_name == 'type2':
            return ConcreteType2()
        else:
            raise ValueError(f'Unknown type: {type_name}')
""",
                "abstract_product": """
from abc import ABC, abstractmethod

class Abstract{name}(ABC):
    '''Abstract base for {name} products.'''
    
    @abstractmethod
    def operation(self) -> str:
        '''Perform the operation.'''
        pass
"""
            }
        )
        self.loaded_patterns["factory"] = factory_pattern
        
        # Singleton pattern
        singleton_pattern = DesignPattern(
            name="singleton",
            template="",  # Template loaded from file
            category="creational",
            description="Ensure single instance of a class",
            template_path=Path("patterns/singleton.json"),
            applicable_to=[ComponentType.SERVICE, ComponentType.CORE],
            required_components=["SingletonClass"],
            design_decisions={
                "instance_management": "Use class variable for single instance",
                "thread_safety": "Include thread lock for multi-threaded access",
                "lazy_init": "Create instance on first access"
            },
            code_templates={
                "singleton_class": """
import threading

class {name}Singleton:
    '''Singleton implementation for {name}.'''
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        '''Initialize the singleton instance.'''
        # Initialization code here
        pass
"""
            }
        )
        self.loaded_patterns["singleton"] = singleton_pattern
        
        # Observer pattern
        observer_pattern = DesignPattern(
            name="observer",
            template="",  # Template loaded from file
            category="behavioral",
            description="Define one-to-many dependency between objects",
            template_path=Path("patterns/observer.json"),
            applicable_to=[ComponentType.SERVICE, ComponentType.AGENT],
            required_components=["Subject", "Observer", "ConcreteObserver"],
            design_decisions={
                "notification": "Push model for state changes",
                "registration": "Dynamic observer registration",
                "decoupling": "Loose coupling via interfaces"
            },
            code_templates={
                "subject": """
from typing import List

class {name}Subject:
    '''Subject that notifies observers.'''
    
    def __init__(self):
        self._observers: List[Observer] = []
        self._state = None
    
    def attach(self, observer: Observer) -> None:
        '''Attach an observer.'''
        self._observers.append(observer)
    
    def detach(self, observer: Observer) -> None:
        '''Detach an observer.'''
        self._observers.remove(observer)
    
    def notify(self) -> None:
        '''Notify all observers.'''
        for observer in self._observers:
            observer.update(self._state)
""",
                "observer_interface": """
from abc import ABC, abstractmethod

class Observer(ABC):
    '''Observer interface.'''
    
    @abstractmethod
    def update(self, state: Any) -> None:
        '''Receive update from subject.'''
        pass
"""
            }
        )
        self.loaded_patterns["observer"] = observer_pattern
    
    def load_pattern(self, pattern_name: str) -> Optional[DesignPattern]:
        """Load a design pattern by name.
        
        Args:
            pattern_name: Name of the pattern to load
            
        Returns:
            The loaded DesignPattern or None if not found
        """
        # Check if already loaded
        if pattern_name in self.loaded_patterns:
            logger.debug(f"Pattern '{pattern_name}' already loaded from cache")
            return self.loaded_patterns[pattern_name]
        
        # Try to load from file
        pattern_file = self.patterns_dir / f"{pattern_name}.json"
        if pattern_file.exists():
            try:
                with open(pattern_file, 'r') as f:
                    pattern_data = json.load(f)
                
                # Convert applicable_to strings to ComponentType enums
                if "applicable_to" in pattern_data:
                    pattern_data["applicable_to"] = [
                        ComponentType(ct) for ct in pattern_data["applicable_to"]
                    ]
                
                # Create DesignPattern instance
                pattern = DesignPattern(
                    name=pattern_data["name"],
                    template=pattern_data.get("template", ""),  # Template from JSON or empty
                    category=pattern_data["category"],
                    description=pattern_data["description"],
                    template_path=Path(pattern_data.get("template_path", f"patterns/{pattern_name}.json")),
                    applicable_to=pattern_data.get("applicable_to", []),
                    required_components=pattern_data.get("required_components", []),
                    design_decisions=pattern_data.get("design_decisions", {}),
                    code_templates=pattern_data.get("code_templates", {})
                )
                
                self.loaded_patterns[pattern_name] = pattern
                logger.info(f"Loaded pattern '{pattern_name}' from {pattern_file}")
                return pattern
                
            except Exception as e:
                logger.error(f"Failed to load pattern from {pattern_file}: {e}")
                return None
        
        logger.warning(f"Pattern '{pattern_name}' not found")
        return None
    
    def list_available_patterns(self) -> List[str]:
        """List all available pattern names.
        
        Returns:
            List of available pattern names
        """
        patterns = list(self.loaded_patterns.keys())
        
        # Add patterns from files
        if self.patterns_dir.exists():
            for pattern_file in self.patterns_dir.glob("*.json"):
                pattern_name = pattern_file.stem
                if pattern_name not in patterns:
                    patterns.append(pattern_name)
        
        return sorted(patterns)
    
    def get_patterns_for_type(self, component_type: ComponentType) -> List[DesignPattern]:
        """Get all patterns applicable to a component type.
        
        Args:
            component_type: The component type to filter by
            
        Returns:
            List of applicable patterns
        """
        applicable: List[DesignPattern] = []
        
        # Check loaded patterns
        for pattern in self.loaded_patterns.values():
            if pattern.is_applicable(component_type):
                applicable.append(pattern)
        
        # Load and check file patterns
        for pattern_name in self.list_available_patterns():
            if pattern_name not in self.loaded_patterns:
                pattern = self.load_pattern(pattern_name)
                if pattern and pattern.is_applicable(component_type):
                    applicable.append(pattern)
        
        return applicable
    
    def save_pattern(self, pattern: DesignPattern, overwrite: bool = False) -> bool:
        """Save a pattern to file.
        
        Args:
            pattern: The pattern to save
            overwrite: Whether to overwrite existing file
            
        Returns:
            True if saved successfully
        """
        pattern_file = self.patterns_dir / f"{pattern.name}.json"
        
        if pattern_file.exists() and not overwrite:
            logger.warning(f"Pattern file {pattern_file} already exists")
            return False
        
        try:
            # Ensure directory exists
            self.patterns_dir.mkdir(parents=True, exist_ok=True)
            
            # Convert pattern to dict
            pattern_dict = asdict(pattern)
            
            # Convert ComponentType enums to strings
            if "applicable_to" in pattern_dict:
                pattern_dict["applicable_to"] = [
                    ct.value for ct in pattern.applicable_to
                ]
            
            # Convert Path to string
            pattern_dict["template_path"] = str(pattern.template_path)
            
            # Save to file
            with open(pattern_file, 'w') as f:
                json.dump(pattern_dict, f, indent=2)
            
            # Add to loaded patterns
            self.loaded_patterns[pattern.name] = pattern
            
            logger.info(f"Saved pattern '{pattern.name}' to {pattern_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save pattern to {pattern_file}: {e}")
            return False
    
    def apply_pattern_template(self, pattern: DesignPattern, context: Dict[str, str]) -> Dict[str, str]:
        """Apply pattern templates with context substitution.
        
        Args:
            pattern: The pattern to apply
            context: Variable substitutions for templates
            
        Returns:
            Dictionary of template_name -> generated_code
        """
        generated: Dict[str, str] = {}
        
        for template_name, template_code in pattern.code_templates.items():
            # Substitute context variables
            code = template_code
            for key, value in context.items():
                code = code.replace(f"{{{key}}}", value)
            
            generated[template_name] = code
            logger.debug(f"Applied template '{template_name}' with context")
        
        return generated
    
    def validate_pattern_requirements(self, pattern: DesignPattern, existing_components: List[str]) -> Tuple[bool, List[str]]:
        """Validate that pattern requirements are met.
        
        Args:
            pattern: The pattern to validate
            existing_components: List of existing component names
            
        Returns:
            Tuple of (is_valid, missing_components)
        """
        missing: List[str] = []
        
        for required in pattern.required_components:
            if required not in existing_components:
                missing.append(required)
        
        is_valid = len(missing) == 0
        
        if not is_valid:
            logger.warning(f"Pattern '{pattern.name}' missing components: {missing}")
        
        return is_valid, missing