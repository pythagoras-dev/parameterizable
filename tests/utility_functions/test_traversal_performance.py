import time
from mixinforge.utility_functions import find_instances_inside_composite_object

class MockKwArgs(dict):
    """A mock class behaving like KwArgs from Pythagoras for testing purposes.
    
    It is a dict subclass with no __slots__ and (by default) empty __dict__.
    """
    pass

def test_many_kwargs_traversal_performance():
    """Verify that traversing many dict subclasses (like KwArgs) is efficient.
    
    This acts as a regression test for the 'hang' issue caused by generic
    traversal of dict subclasses in mixinforge.
    """
    count = 2000
    # Construct a list containing many MockKwArgs objects
    root = [MockKwArgs(i=i) for i in range(count)]
    
    start_time = time.time()
    # Search for MockKwArgs instances inside the list
    found = list(find_instances_inside_composite_object(root, MockKwArgs))
    end_time = time.time()
    
    duration = end_time - start_time
    
    print(f"Traversal of {count} MockKwArgs items took {duration:.4f}s")
    
    # It should be very fast (< 0.1s typically, but allowing < 2.0s for safety)
    assert duration < 2.0, f"Traversal took too long: {duration}s. Performance regression detected."
    
    # Verify we found everything
    assert len(found) == count

def test_kwargs_traversal_correctness():
    """Verify that we actually look inside dict subclasses."""
    target_int = 999
    
    # Put target in a list inside MockKwArgs
    root = MockKwArgs(a=1, b=[target_int])
    
    # Search for int inside
    found = list(find_instances_inside_composite_object(root, int))
    
    assert 1 in found
    assert target_int in found
