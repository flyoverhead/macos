"""When the claude role runs the native installer."""

import pathlib

import pytest
import yaml
from ansible.plugins.filter.core import FilterModule
from ansible.plugins.test.core import TestModule as AnsibleTests
from jinja2 import Environment

ROLE = pathlib.Path(__file__).resolve().parents[2] / "roles/claude"
DETECT = yaml.safe_load((ROLE / "tasks/detect.yml").read_text(encoding="utf-8"))
INSTALL = yaml.safe_load((ROLE / "tasks/install.yml").read_text(encoding="utf-8"))
MAIN = yaml.safe_load((ROLE / "tasks/main.yml").read_text(encoding="utf-8"))
DEFAULTS = yaml.safe_load((ROLE / "defaults/main.yml").read_text(encoding="utf-8"))

ENV = Environment()
ENV.filters.update({k: v for k, v in FilterModule().filters().items() if k not in ("default", "d")})
ENV.tests.update(AnsibleTests().tests())


def _fact(name, key):
    for task in DETECT:
        if task["name"] == name:
            return task["ansible.builtin.set_fact"][key]
    raise AssertionError(name)


def _render(expression, **context):
    return ENV.from_string(expression).render(**context).strip()


def _installed(stdout):
    output = {"stdout": stdout} if stdout is not None else {}
    return _render(_fact("detect | claude installed facts", "claude_installed_version"), claude_version_output=output)


def _needed(installed, wanted):
    return _render(
        _fact("detect | claude install needed", "claude_install_needed"),
        claude_installed_version=installed,
        claude_version=wanted,
    )


def test_installed_version_is_parsed_from_the_cli():
    assert _installed("2.1.292 (Claude Code)") == "2.1.292"
    assert _installed(None) == ""
    assert _installed("") == ""


@pytest.mark.parametrize(
    ("installed", "wanted", "needed"),
    [
        ("", "stable", "True"),
        ("", "2.1.292", "True"),
        ("2.1.292", "stable", "False"),
        ("2.1.292", "latest", "False"),
        ("2.1.292", "2.1.292", "False"),
        ("2.1.200", "2.1.292", "True"),
    ],
)
def test_install_runs_only_when_missing_or_off_pin(installed, wanted, needed):
    assert _needed(installed, wanted) == needed


def test_install_is_opt_in():
    assert DEFAULTS["claude_install"] is False
    install = next(task for task in MAIN if task["name"] == "install")
    assert install["when"] == ["claude_install", "claude_install_needed | bool"]


def test_installer_runs_as_the_user_with_the_version():
    task = next(t for t in INSTALL if "ansible.builtin.command" in t)
    assert task["become_user"] == "{{ claude_user_name }}"
    assert task["ansible.builtin.command"]["cmd"].endswith("'{{ claude_version }}'")


def test_version_probe_never_fails_the_play():
    probe = next(t for t in DETECT if "ansible.builtin.command" in t)
    assert probe["failed_when"] is False
    assert probe["check_mode"] is False
    assert probe["changed_when"] is False
