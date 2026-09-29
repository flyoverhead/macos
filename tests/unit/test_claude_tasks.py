"""The packages role's Claude Code tasks, asserted as data."""

import pathlib

import yaml

ROLE = pathlib.Path(__file__).resolve().parents[2] / "roles/packages"

CLAUDE = yaml.safe_load((ROLE / "tasks/claude.yml").read_text(encoding="utf-8"))
DEFAULTS = yaml.safe_load((ROLE / "defaults/main.yml").read_text(encoding="utf-8"))


def _find(tasks, needle):
    for task in tasks:
        if needle in task.get("name", ""):
            return task
        found = _find(task.get("block", []), needle) if "block" in task else None
        if found:
            return found
    return None


def test_settings_are_merged_over_the_existing_file():
    content = _find(CLAUDE, "create settings")["ansible.builtin.copy"]["content"]
    assert "packages_claude_settings_current.content" in content
    assert "combine(packages_claude_settings, recursive=True)" in content


def test_settings_keep_the_existing_key_order():
    content = _find(CLAUDE, "create settings")["ansible.builtin.copy"]["content"]
    assert "sort_keys=False" in content


def test_every_file_is_opt_in():
    assert DEFAULTS["packages_claude_settings"] == {}
    assert DEFAULTS["packages_claude_md"] == ""
    assert DEFAULTS["packages_claude_statusline_install"] is False


def test_statusline_is_not_swept_into_the_pre_commit_configs():
    assert not list((ROLE / "files").rglob("*statusline*"))


def test_statusline_reads_settings_from_the_active_config_dir():
    script = (ROLE / "templates/claude_statusline.j2").read_text(encoding="utf-8")
    assert 'settings_path="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/settings.json"' in script
    assert ".claude-enterprise" not in script


def test_mcp_servers_are_replaced_per_server_not_deep_merged():
    content = _find(CLAUDE, "create mcp servers")["ansible.builtin.copy"]["content"]
    assert "combine(packages_claude_mcp_servers)" in content
    assert "recursive" not in content


def test_state_file_keeps_its_format():
    content = _find(CLAUDE, "create mcp servers")["ansible.builtin.copy"]["content"]
    assert "sort_keys=False" in content
    assert "ensure_ascii=False" in content
    assert not content.endswith("\n")


def test_state_file_contents_are_never_logged():
    for needle in ("read state file", "parse state file", "create mcp servers"):
        assert _find(CLAUDE, needle)["no_log"] is True, needle
    assert _find(CLAUDE, "create mcp servers")["ansible.builtin.copy"]["mode"] == "0600"


def test_mcp_servers_are_opt_in():
    assert DEFAULTS["packages_claude_mcp_servers"] == {}
