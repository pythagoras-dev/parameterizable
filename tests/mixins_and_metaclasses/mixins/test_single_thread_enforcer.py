import threading
import pytest
import mixinforge.mixins_and_metaclasses.single_thread_enforcer_mixin as ste
from mixinforge.mixins_and_metaclasses.single_thread_enforcer_mixin import (
    _restrict_to_single_thread,
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
    _restrict_to_single_thread()
    assert ste._owner_thread_native_id == threading.get_native_id()

    # Second access from same thread
    _restrict_to_single_thread()
    assert ste._owner_thread_native_id == threading.get_native_id()

def test_multi_thread_failure():
    """Test that a second thread raises RuntimeError."""
    # Main thread claims ownership
    _restrict_to_single_thread()

    exception_caught = False

    def intruder_thread():
        nonlocal exception_caught
        try:
            _restrict_to_single_thread()
        except RuntimeError as e:
            if "This object is restricted to single-threaded execution" in str(e):
                exception_caught = True

    t = threading.Thread(target=intruder_thread, name="Intruder")
    t.start()
    t.join()

    assert exception_caught, "Secondary thread should have raised RuntimeError"

def test_reset_allows_new_owner():
    """Test that resetting allows a new thread to become the owner."""
    # Main thread claims ownership
    _restrict_to_single_thread()

    # Reset
    _reset_thread_ownership()
    assert ste._owner_thread_native_id is None

    # New thread attempts to claim ownership
    exception_caught = False

    def new_owner_thread():
        nonlocal exception_caught
        try:
            _restrict_to_single_thread()
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
        _restrict_to_single_thread()

    assert "This object is restricted to single-threaded execution" in str(excinfo.value)

def test_pid_change_resets_ownership():
    """Test that PID change (simulating fork) resets ownership."""
    import os

    # Main thread claims ownership
    _restrict_to_single_thread()
    original_native_id = ste._owner_thread_native_id
    original_pid = ste._owner_process_id

    assert original_native_id == threading.get_native_id()
    assert original_pid == os.getpid()

    # Simulate a PID change (as would happen after fork)
    # We can't actually fork in pytest easily, so we manually change the PID
    fake_new_pid = original_pid + 99999
    ste._owner_process_id = fake_new_pid

    # Now when we call _restrict_to_single_thread, it should detect PID mismatch
    # and reset ownership, allowing the current thread to claim it
    _restrict_to_single_thread()

    # Ownership should be reset to current thread and PID
    assert ste._owner_thread_native_id == threading.get_native_id()
    assert ste._owner_process_id == os.getpid()
    assert ste._owner_process_id != fake_new_pid


def test_mixin_init_thread_restriction():
    """Test that SingleThreadEnforcerMixin.__init__ enforces thread restriction."""
    from mixinforge.mixins_and_metaclasses.single_thread_enforcer_mixin import SingleThreadEnforcerMixin

    # Reset to ensure clean state
    _reset_thread_ownership()

    class MyClass(SingleThreadEnforcerMixin):
        def __init__(self):
            super().__init__()
            self.value = 42

    # Main thread creates instance successfully
    obj = MyClass()
    assert obj.value == 42

    # New thread should fail to create instance
    exception_caught = False

    def thread_init():
        nonlocal exception_caught
        try:
            MyClass()
        except RuntimeError:
            exception_caught = True

    t = threading.Thread(target=thread_init)
    t.start()
    t.join()

    assert exception_caught


def test_mixin_method_thread_restriction():
    """Test that SingleThreadEnforcerMixin._restrict_to_single_thread method works."""
    from mixinforge.mixins_and_metaclasses.single_thread_enforcer_mixin import SingleThreadEnforcerMixin

    # Reset to ensure clean state
    _reset_thread_ownership()

    class MyClass(SingleThreadEnforcerMixin):
        def __init__(self):
            super().__init__()
            self.value = 42

        def check_thread(self):
            self._restrict_to_single_thread()
            return self.value

    # Main thread creates instance and calls method
    obj = MyClass()
    assert obj.check_thread() == 42

    # New thread should fail to call the method
    exception_caught = False

    def thread_call_method():
        nonlocal exception_caught
        try:
            obj.check_thread()
        except RuntimeError:
            exception_caught = True

    t = threading.Thread(target=thread_call_method)
    t.start()
    t.join()

    assert exception_caught


def test_mixin_init_forwards_args_and_kwargs():
    """SingleThreadEnforcerMixin.__init__ should forward positional and keyword args."""
    from mixinforge import SingleThreadEnforcerMixin

    _reset_thread_ownership()

    class RequiresArgs:
        def __init__(self, a, b, *, c):
            self.received = (a, b, c)

    class MyClass(SingleThreadEnforcerMixin, RequiresArgs):
        def __init__(self, a, b, *, c):
            super().__init__(a, b, c=c)
            self.ready = True

    obj = MyClass(1, 2, c=3)

    assert obj.received == (1, 2, 3)
    assert obj.ready is True
    assert ste._owner_thread_native_id == threading.get_native_id()
