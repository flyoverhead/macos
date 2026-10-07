"""vscode_extension ignores Node deprecation warnings but not real errors."""

import importlib.util
import pathlib

MODULE = pathlib.Path(__file__).resolve().parents[2] / "plugins/modules/vscode_extension.py"
SPEC = importlib.util.spec_from_file_location("vscode_extension", MODULE)
vscode_extension = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(vscode_extension)

DEP0169 = (
    "(node:64120) [DEP0169] DeprecationWarning: `url.parse()` behavior is not standardized "
    "and prone to errors that have security implications. Use the WHATWG URL API instead.\n"
    "(Use `VSCodium --trace-deprecation ...` to show where the warning was created)\n"
)
DEP0005 = (
    "(node:1234) [DEP0005] DeprecationWarning: Buffer() is deprecated due to security and usability issues.\n"
    "(Use `Code Helper --trace-deprecation ...` to show where the warning was created)\n"
)


def test_clean_run_passes():
    assert not vscode_extension._failed(0, "")


def test_node_deprecation_warnings_are_ignored():
    assert not vscode_extension._failed(0, DEP0169)
    assert not vscode_extension._failed(0, DEP0005 + "\n" + DEP0169)


def test_nonzero_rc_fails():
    assert vscode_extension._failed(1, DEP0169)


def test_other_stderr_fails_even_next_to_a_warning():
    assert vscode_extension._failed(0, "Failed Installing Extensions: foo.bar\n")
    assert vscode_extension._failed(0, DEP0005 + "Extension 'foo.bar' not found.\n")
