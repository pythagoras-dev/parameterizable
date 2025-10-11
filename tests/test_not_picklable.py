import pickle

from parameterizable import NotPicklableClass

import pytest

def test_not_picklable():
    npo = NotPicklableClass()

    # Test dunder methods directly
    with pytest.raises(TypeError):
        npo.__reduce__()
    with pytest.raises(TypeError):
        _ = npo.__getstate__()
    with pytest.raises(TypeError):
        npo.__setstate__({"key": "value"})

    # Test pickling via pickle.dumps(), which calls __reduce__()
    with pytest.raises(TypeError):
        pickle.dumps(npo)

    # Test that a subclass is also not picklable
    class MyNotPicklableClass(NotPicklableClass):
        pass
    mnpo = MyNotPicklableClass()
    with pytest.raises(TypeError):
        pickle.dumps(mnpo)