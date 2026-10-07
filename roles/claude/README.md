# `flyoverhead.macos.claude`

Installs Claude Code with Anthropic's native installer and manages its
configuration: `settings.json`, `CLAUDE.md`, a status line script and
user-scope MCP servers. Every part is opt-in.

## Role variables

| Variable | Description | Example |
| :--- | :--- | :--- |
| `claude_user_name` | User Claude Code is installed and configured for | `{{ ansible_user }}` |
| `claude_user_group` | That user's group | `{{ ansible_user_gid }}` |
| `claude_user_home` | That user's home | `{{ ansible_user_dir }}` |
| `claude_install` | Run the native installer when Claude Code is missing or off its pin | `false` |
| `claude_version` | `stable`, `latest` or an exact version | `stable` |
| `claude_installer_url` | Installer script | `https://claude.ai/install.sh` |
| `claude_bin_path` | Where the installer puts the launcher; read to detect an install | `~/.local/bin/claude` |
| `claude_tmp_path` | Where the installer is downloaded to | `~/tmp` |
| `claude_config_path` | Claude Code config directory, i.e. `CLAUDE_CONFIG_DIR` | `/Users/me/.claude` |
| `claude_settings` | Deep-merged over `settings.json`. Empty leaves the file alone | Definition example in [defaults/main.yml](defaults/main.yml) |
| `claude_md` | Written verbatim to `CLAUDE.md`. Empty leaves the file alone | `''` |
| `claude_statusline_install` | Deploy `statusline.sh` into the config directory | `false` |
| `claude_json_path` | Claude Code's state file, `.claude.json` | `/Users/me/.claude.json` |
| `claude_mcp_servers` | User-scope MCP servers merged into the state file. Not logged | Definition example in [defaults/main.yml](defaults/main.yml) |

## Facts set by this role

| Fact | Description |
| :--- | :--- |
| `claude_installed_version` | Version reported by `claude --version`, empty when not installed |
| `claude_install_needed` | Whether the installer would run: Claude Code is missing, or `claude_version` is an exact version the installed one differs from |

## Behaviour worth knowing before the first run

- **A channel installs once; an exact version is enforced.** With
  `claude_version` at `stable` or `latest` the installer runs only when
  Claude Code is missing, and updates are left to Claude Code's own updater.
  An exact version is reinstalled whenever the installed one differs, so set
  `DISABLE_AUTOUPDATER: '1'` under `claude_settings.env` as well, or every
  auto-update is undone on the next run.
- **The installer runs as `claude_user_name`.** It refuses to run as root
  under sudo and installs into that user's `~/.local`; it verifies the binary's
  SHA-256 against Anthropic's manifest itself. It needs egress to `claude.ai`
  and `downloads.claude.ai`.
- **Claude Code's `settings.json` is merged, not overwritten.** Claude Code
  rewrites that file itself, so `claude_settings` is deep-merged over
  whatever is there: keys it does not name survive, keys it names win, and a
  list it names replaces the existing list rather than extending it -- so a
  managed `permissions.allow` discards every permission approved
  interactively since the last run. Removing a key from the variable does not
  remove it from the file.
- **MCP servers are written into Claude Code's state file.** `.claude.json`
  holds the OAuth account, caches and per-project history, and Claude Code
  rewrites it constantly, so each server in `claude_mcp_servers` replaces the
  server of that name whole and nothing else in the file is touched. Unlisted
  servers are kept, and removing one from the variable does not remove it. Apply
  with no Claude Code session running, or a live session may save its in-memory
  copy over the change. The file is created `0600`; an existing file keeps the
  mode Claude Code gives it, since Claude Code rewrites it at `0644` and forcing
  it back would report a change on every run. The tasks are `no_log: true`, so a
  failure will not show its content. It sits at `~/.claude.json` by default but
  inside `CLAUDE_CONFIG_DIR` when that is set — keep `claude_json_path` in step.
- **The Claude Code status line reads `CLAUDE_CONFIG_DIR`.** `statusline.sh`
  looks for `settings.json` under `$CLAUDE_CONFIG_DIR`, falling back to
  `~/.claude`. Deploying it does not enable it; set `statusLine` in
  `claude_settings`.
- **The role does not install `jq`.** The status line needs it; install it
  through `flyoverhead.macos.packages`.

## Check mode

`--check --diff` reports drift in `settings.json`, `CLAUDE.md` and
`statusline.sh`. The state file task is `no_log: true`, so a check run reports
that `.claude.json` would change but not how.

`detect | claude version` runs even in a check run; it only reads. The
installer is reported as pending without running.

## Example playbook

```yaml
- hosts: workstation
  gather_facts: true
  roles:
    - role: flyoverhead.macos.claude
      vars:
        claude_install: true
        claude_settings:
          model: opus
        claude_statusline_install: true
```
