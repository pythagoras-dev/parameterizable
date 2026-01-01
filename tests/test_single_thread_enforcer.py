import threading
import pytest
import mixinforge.single_thread_enforcer as ste
from mixinforge.single_thread_enforcer import (
    _enforce_single_thread_access,
    _reset_thread_ownership,
)

def setup_function():
    """Reset the enforcer before each test."""
    _reset_thread_ownership()

def teardown_function():
    """Reset the enforcer after each test."""
    _reset_thread_ownership()

def test_single_thread_success():
    """Test that the first thread to access can access repeatedly."""
    # First access
    _enforce_single_thread_access()
    assert ste._owner_thread_native_id == threading.get_native_id()

    # Second access from same thread
    _enforce_single_thread_access()
    assert ste._owner_thread_native_id == threading.get_native_id()

def test_multi_thread_failure():
    """Test that a second thread raises RuntimeError."""
    # Main thread claims ownership
    _enforce_single_thread_access()
    
    exception_caught = False
    
    def intruder_thread():
        nonlocal exception_caught
        try:
            _enforce_single_thread_access()
        except RuntimeError as e:
            if "Pythagoras portals are single-threaded by design" in str(e):
                exception_caught = True

    t = threading.Thread(target=intruder_thread, name="Intruder")
    t.start()
    t.join()
    
    assert exception_caught, "Secondary thread should have raised RuntimeError"

def test_reset_allows_new_owner():
    """Test that resetting allows a new thread to become the owner."""
    # Main thread claims ownership
    _enforce_single_thread_access()

    # Reset
    _reset_thread_ownership()
    assert ste._owner_thread_native_id is None
    
    # New thread attempts to claim ownership
    exception_caught = False
    
    def new_owner_thread():
        nonlocal exception_caught
        try:
            _enforce_single_thread_access()
        except Exception:
            exception_caught = True

    t = threading.Thread(target=new_owner_thread, name="NewOwner")
    t.start()
    t.join()
    
    assert not exception_caught, "New thread should succeed after reset"
    
    # Now main thread should fail because "NewOwner" claimed it
    # Note: "NewOwner" thread finished, but the enforcer remembers the ID.
    # The ID might be reused by OS, but likely not immediately. 
    # Even if "NewOwner" is dead, the enforcer still holds its ID.
    
    # However, if threading.get_native_id() of the main thread is different 
    # from the stored ID (which was NewOwner's ID), it should raise RuntimeError.
    
    with pytest.raises(RuntimeError) as excinfo:
        _enforce_single_thread_access()
    
    assert "Pythagoras portals are single-threaded by design" in str(excinfo.value)

def test_pid_change_resets_ownership():
    """Test that PID change (simulating fork) resets ownership."""
    import os

    # Main thread claims ownership
    _enforce_single_thread_access()
    original_native_id = ste._owner_thread_native_id
    original_pid = ste._owner_process_id

    assert original_native_id == threading.get_native_id()
    assert original_pid == os.getpid()

    # Simulate a PID change (as would happen after fork)
    # We can't actually fork in pytest easily, so we manually change the PID
    fake_new_pid = original_pid + 99999
    ste._owner_process_id = fake_new_pid

    # Now when we call _enforce_single_thread_access, it should detect PID mismatch
    # and reset ownership, allowing the current thread to claim it
    _enforce_single_thread_access()

    # Ownership should be reset to current thread and PID
    assert ste._owner_thread_native_id == threading.get_native_id()
    assert ste._owner_process_id == os.getpid()
    assert ste._owner_process_id != fake_new_pid
