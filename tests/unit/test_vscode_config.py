"""The packages role merges its VS Code settings over the editor's own file."""

import pathlib

import yaml

ROLE = pathlib.Path(__file__).resolve().parents[2] / "roles/packages"
CONFIG = yaml.safe_load((ROLE / "tasks/config.yml").read_text(encoding="utf-8"))
VSCODE = next(task for task in CONFIG if task["name"] == "config | visual studio code")
DEFAULTS = yaml.safe_load((ROLE / "defaults/main.yml").read_text(encoding="utf-8"))


def _task(name):
    return next(task for task in VSCODE["block"] if task["name"] == f"config | {name}")


def test_settings_variable_defaults_to_empty():
    assert DEFAULTS["packages_vscode_settings"] == {}


def test_live_file_is_the_base_and_managed_keys_win():
    merged = _task("merge vscode config")["ansible.builtin.set_fact"]["packages_vscode_config_merged"]
    base = merged.index("from_json")
    template = merged.index("'vscode.j2') | from_json, recursive=True")
    variable = merged.index("combine(packages_vscode_settings, recursive=True)")
    assert base < template < variable


def test_write_is_skipped_when_content_already_matches():
    write = _task("create vscode config")
    assert "ansible.builtin.template" not in write
    assert write["when"] == ["packages_vscode_config_merged != packages_vscode_config_existing"]


def test_nanorc_has_no_extra_include():
    assert "/extra/" not in (ROLE / "templates/nanorc.j2").read_text(encoding="utf-8")
