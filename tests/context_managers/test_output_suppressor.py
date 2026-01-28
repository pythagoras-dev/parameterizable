import sys
from mixinforge import OutputSuppressor


def test_output_is_suppressed(capsys):
    """Verify that output to stdout and stderr is suppressed within the context."""
    with OutputSuppressor():
        print("This should not appear")
        print("This should also not appear", file=sys.stderr)
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""


def test_output_is_restored(capsys):
    """Verify that stdout and stderr are restored after exiting the context."""
    print("Before suppression")
    with OutputSuppressor():
        print("This is suppressed")
    print("After suppression")

    captured = capsys.readouterr()
    assert "Before suppression\n" in captured.out
    assert "After suppression\n" in captured.out
    assert "This is suppressed" not in captured.out


def test_no_output_with_suppressor(capsys):
    """Ensure no output is captured with the suppressor active."""
    with OutputSuppressor():
        print("This should not appear")
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
