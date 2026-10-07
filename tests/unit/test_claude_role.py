"""The claude role, asserted as data."""

import pathlib

import yaml

ROLE = pathlib.Path(__file__).resolve().parents[2] / "roles/claude"

CLAUDE = yaml.safe_load((ROLE / "tasks/config.yml").read_text(encoding="utf-8"))
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
    assert "claude_settings_current.content" in content
    assert "combine(claude_settings, recursive=True)" in content


def test_settings_keep_the_existing_key_order():
    content = _find(CLAUDE, "create settings")["ansible.builtin.copy"]["content"]
    assert "sort_keys=False" in content


def test_every_file_is_opt_in():
    assert DEFAULTS["claude_settings"] == {}
    assert DEFAULTS["claude_md"] == ""
    assert DEFAULTS["claude_statusline_install"] is False


def test_statusline_is_not_swept_into_the_pre_commit_configs():
    packages = ROLE.parent / "packages"
    assert not list((packages / "files").rglob("*statusline*"))
    assert not (ROLE / "files").exists()


def test_statusline_reads_settings_from_the_active_config_dir():
    script = (ROLE / "templates/statusline.j2").read_text(encoding="utf-8")
    assert 'settings_path="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/settings.json"' in script
    assert ".claude-enterprise" not in script


def test_mcp_servers_are_replaced_per_server_not_deep_merged():
    content = _find(CLAUDE, "create mcp servers")["ansible.builtin.copy"]["content"]
    assert "combine(claude_mcp_servers)" in content
    assert "recursive" not in content


def test_state_file_keeps_its_format():
    content = _find(CLAUDE, "create mcp servers")["ansible.builtin.copy"]["content"]
    assert "sort_keys=False" in content
    assert "ensure_ascii=False" in content
    assert not content.endswith("\n")


def test_state_file_contents_are_never_logged():
    for needle in ("read state file", "parse state file", "create mcp servers"):
        assert _find(CLAUDE, needle)["no_log"] is True, needle


def test_state_file_mode_is_left_to_claude_code():
    mode = _find(CLAUDE, "create mcp servers")["ansible.builtin.copy"]["mode"]
    assert mode == "{{ '0600' if not claude_json_file.stat.exists else omit }}"


def test_mcp_servers_are_opt_in():
    assert DEFAULTS["claude_mcp_servers"] == {}
