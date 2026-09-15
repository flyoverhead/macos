"""The packages role's uv tasks, asserted as data."""

import pathlib

import yaml

ROLE = pathlib.Path(__file__).resolve().parents[2] / "roles/packages"


def _load(relative):
    with open(ROLE / relative, encoding="utf-8") as handle:
        return yaml.safe_load(handle)


PIP = _load("tasks/pip.yml")
DEFAULTS = _load("defaults/main.yml")


def _by_name(tasks, needle):
    for task in tasks:
        if needle in task.get("name", ""):
            return task
    raise AssertionError(f"no task whose name contains {needle!r}")


def test_no_task_still_uses_the_pip_module():
    for task in PIP:
        assert "ansible.builtin.pip" not in task, task.get("name", "?")


def test_venv_creation_is_guarded_against_wiping_the_venv():
    task = _by_name(PIP, "create virtualenv")
    creates = task["ansible.builtin.command"]["creates"]
    assert creates == "{{ packages_venv_path }}/bin/python"


def test_venv_never_downloads_its_own_python():
    task = _by_name(PIP, "create virtualenv")
    cmd = task["ansible.builtin.command"]["cmd"]
    assert "--no-python-downloads" in cmd
    assert "{{ packages_homebrew_bin_path }}/python3" in cmd


def test_install_reports_change_from_stderr_not_stdout():
    task = _by_name(PIP, "install packages")
    assert "stderr" in task["changed_when"]
    assert "stdout" not in task["changed_when"]
    assert "Installed" in task["changed_when"]


def test_uv_comes_from_homebrew_not_the_bare_path():
    for needle in ("create virtualenv", "install packages"):
        cmd = _by_name(PIP, needle)["ansible.builtin.command"]["cmd"]
        assert "{{ packages_homebrew_bin_path }}/uv" in cmd


def test_a_missing_uv_fails_with_an_explanation():
    task = _by_name(PIP, "fail when uv is missing")
    assert "packages_brew" in task["ansible.builtin.fail"]["msg"]


def test_the_venv_tasks_run_as_the_target_user():
    for needle in ("create virtualenv", "install packages"):
        task = _by_name(PIP, needle)
        assert task["become_user"] == "{{ packages_user_name }}"


def test_pip_is_not_the_commented_example_for_packages_pip():
    assert DEFAULTS["packages_pip"] == []
    source = (ROLE / "defaults/main.yml").read_text(encoding="utf-8")
    assert "\n  # - pip\n" not in source
