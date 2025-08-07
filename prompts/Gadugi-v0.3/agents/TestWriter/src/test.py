   def create_test_class(class_name, methods_to_test):
       """Create well-structured test class."""
       test_class_template = f'''
   class Test{class_name}:
       """
       Comprehensive test suite for {class_name}.

       Tests validate:
       - Core functionality and public interface
       - Error handling and edge cases
       - Integration with dependencies
       - Performance characteristics
       """

       @pytest.fixture(autouse=True)
       def setup_and_cleanup(self):
           """Setup test environment and ensure cleanup."""
           # Setup code here
           yield
           # Cleanup code here
       '''

       return test_class_template
   