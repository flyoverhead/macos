# Changelog

All notable changes to `flyoverhead.macos`.

## 1.0.0

Initial release. The four macOS workstation roles were extracted from a
playbook repository, where they lived as loose local roles under `roles/`
alongside an inventory, a `vault_pass` and a `group_vars/all.yml` carrying one
operator's entire configuration. Each role gained a README, a corrected
`meta/main.yml` and empty defaults; the opinionated configuration moved out to
the consuming inventory.

### Added

- `galaxy.yml`, `meta/runtime.yml`, `CHANGELOG.md`, `.gitignore`, and a
  `build_ignore` so the published tarball stops shipping the test harness and
  the linter configs.
- A `tests/` harness — `ansible.cfg`, `inventory.yml`, `playbook.yml`,
  `group_vars/` and `host_vars/` — replacing the playbook, inventory and
  variable files that used to sit in the repository root. It targets
  `localhost` by default and a Tart VM when `ANSIBLE_HOST` is set.
- A README per role, and a collection README following the format shared with
  the other `flyoverhead` collections.
- `plugins/modules/vscode_extension.py`, moved out of
  `roles/packages/library/`. It gained `DOCUMENTATION`, `EXAMPLES` and `RETURN`
  blocks, check-mode support, and an `action` return value. Callers now address
  it as `flyoverhead.macos.vscode_extension`.
- **packages**: `packages_ssh_hosts`, `packages_binary_path`,
  `packages_pre_commit_install`, `packages_pre_commit_configs`,
  `packages_homebrew_version`. `packages_git_config` and
  `packages_pre_commit_hooks_path` are now declared in `defaults/` — they were
  read by tasks but had no default at all, so the role only worked when the
  consuming inventory happened to define them.
- **ohmyzsh**: `ohmyzsh_vault_addr`, `ohmyzsh_exports`, `ohmyzsh_ci_registry`,
  `ohmyzsh_ci_images`, `ohmyzsh_repo`, `ohmyzsh_version`, `ohmyzsh_shell`,
  `ohmyzsh_theme_package`, `ohmyzsh_task_completion`,
  `ohmyzsh_history_substring_bindkeys`.
- **dock**: `dock_brew_clear_cache`, `dock_apply_timeout`.
- **osx**: `osx_reload_services`, and `osx_type_map` in `vars/`.
- `Taskfile.yml` gained `install`, `lint`, `build` and `check` targets, and the
  VM targets are prefixed `vm-`.

### Fixed

- **dock — dock items were reordered on every run.** The slot number was
  regexed out of the registered result *dictionary* rather than its `stdout`,
  so the comparison against the desired position never matched and
  `dockutil --move` always ran. It now reads `stdout`, and re-reads the item
  after an add rather than reusing a stale result.
- **dock — a dock item that dockutil could not find aborted the play.**
  `dock_item_section` was set by a `set_fact` guarded on `rc == 0` but read
  unconditionally by the next task's `when`. It now defaults to an empty
  string.
- **dock — the `dockutil --find` guard tested an attribute that never
  exists.** `failed_when` inspected `.msg`, which a successful `command` does
  not set. A missing item is a normal answer here, so it is now
  `failed_when: false`.
- **dock could not run without `packages`.** Its handler read
  `homebrew_cache_path` and `packages_brew_clear_cache`, both facts of the
  `packages` role. It now registers its own cache path and reads
  `dock_brew_clear_cache`.
- **osx — every entry that omitted `type` failed.** The fallback was
  `item.value | type_debug`, which yields Python type names (`str`, `bool`),
  while `osx_defaults` expects its own vocabulary (`string`, `bool`). An
  explicit map in `vars/main.yml` translates them, defaulting to `string`.
- **osx — the reload handler failed on any machine where one of the three
  processes was not running.** `killall` exits 1 in that case, which is not an
  error here. It is now `failed_when: rc not in [0, 1]`, with `changed_when`
  tied to a successful signal.
- **ohmyzsh — `url` and `branch` in `ohmyzsh_install_plugins` were dead
  configuration.** Only `name` was ever passed, to `community.general.homebrew`
  — the plugins have always come from Homebrew, never from the git repositories
  those fields named. The variable is now a list of `name`/`source` mappings,
  and `.zshrc` sources each one from the Homebrew share directory instead of
  hardcoding four plugin filenames.
- **ohmyzsh — `ohmyzsh_force_reinstall` reinstalled nothing.** `main.yml`
  branched on it but no task ever removed the existing `~/.oh-my-zsh`.
- **ohmyzsh — `.zshrc` sourced powerlevel10k twice** and contained a bare
  `source ${share_path}/`, which sources a directory.
- **ohmyzsh — `eval "$(task --completion zsh)"` broke every shell on a machine
  without go-task.** It is now guarded by a `command -v` check.
- **ohmyzsh — the `fc-cache` handler was unreachable and unusable.** Nothing
  notified it, and `fc-cache` is not present on a stock macOS. Removed; the
  fonts come from the `font-meslo-for-powerlevel10k` cask.
- **packages — the deployed `pre-commit` wrapper hardcoded one operator's home
  directory.** It now templates `packages_pre_commit_hooks_path`, and runs
  under `set -euo pipefail`.
- **packages — `~/.ssh/config` was written from a template containing no
  variables**: a fixed list of hosts, users, addresses and ports. It is now
  rendered from `packages_ssh_hosts`, and skipped entirely when that is empty.
  The directory is created first at `0700` and the file written `0600`;
  previously `blockinfile` was asked to create the file without its parent, at
  `0644`.
- **packages — the binary installer ignored `packages_tmp_path`**, using `/tmp`,
  and set `mode: '0644'` on the unarchive destination *directory*, stripping
  the traversal bit. The download now retries.
- **packages — the DMG installer deleted the whole of `packages_tmp_path`**
  after each image, which is shared with the binary installer. It now removes
  only that image's own artefacts, detaches the image in an `always` block so a
  failed copy cannot leak a mountpoint, copies with `mode: preserve` instead of
  forcing `0755` across a bundle, and fails with a clear message when the image
  contains no `.app` at the top level.
- **packages — the Homebrew cache handler dereferenced an unregistered
  variable.** `homebrew_cache_path` is only registered inside `brew.yml`, which
  is skipped when no brew packages are requested.
- **packages — `loop_var` was named `vscode_extension`, shadowing the
  module.** Renamed to `extension`, which the FQCN call requires.
- **packages — `brew | taps`, `brew | cask` and `brew | packages` each carried
  a redundant `when: <list> | length > 0`** guarding a loop over that same
  list, which an empty loop already handles.
- **packages — the role re-gathered facts.** `detect.yml` opened with an
  explicit `ansible.builtin.setup` although the play already gathers.
- **packages — Rosetta installation is now skipped on Intel**, where the
  installer refuses, via `ansible_architecture == 'arm64'`.
- **packages — the Homebrew directory structure was never created.**
  `packages_brew_folders` was defined and documented but no task consumed it.
- Three roles set a boolean with `'{{ true if x else false }}'`, where the
  condition is already the boolean.
- `force: True` is now `true`.

### Changed

- **Every list and dictionary variable defaults to empty.** The roles ship no
  packages, no casks, no dock items and no defaults; the configuration belongs
  to the consuming inventory. `tests/group_vars/` carries a worked example.
- **Licence is `GPL-3.0-only`**, and the author is `flyoverhead`. The role
  metadata previously said MIT and `Positive Technologies`.
- **ansible-core `>=2.16`.** The roles required `2.15` while the README badge
  claimed `2.18+`.
- **`community.crypto` is no longer a dependency.** It was declared in
  `requirements.yml` and used nowhere. `community.general` is the only
  dependency, pinned `>=8.0.0`.
- **`requirements.txt` is `ansible-core>=2.16`.** It previously installed
  `ansible`, `ansible-lint`, `github3.py`, `jmespath`, `passlib` and `yamllint`
  — lint tooling and unused libraries, none of them a runtime dependency.
- `dock`, `osx` and `packages` no longer claim Debian `bookworm`/`bullseye`
  support in `meta/main.yml`. `osx_defaults`, `dockutil` and Homebrew casks are
  macOS-only. `dock` and `osx` also carried `description: Oh-my-zsh
  configuration` and the `ohmyzsh` tag, from a copy-paste.
- The `nano` configuration is now conditional on `nano` being installed,
  matching how the iTerm2, VS Code and Docker blocks already behaved.
- Registry credentials and the git signing key are written with `no_log: true`,
  and `~/.docker/config.json` is created `0600` rather than `0644`. The
  `git_config` loop label printed every value.
- The pre-commit configuration the `packages` role deploys was repinned:
  `pre-commit-hooks` v5.0.0 → v6.0.0, `pre-commit-terraform`
  v1.96.1 → v1.106.0, `ansible-lint` v24.9.2 → v26.4.0, `yamllint`
  v1.35.1 → v1.38.0.
- The payload `.gitignore` in `roles/packages/files/` ships as `gitignore`,
  without the leading dot, and is renamed on copy. Git reads any file named
  `.gitignore` as ignore rules for its directory, and that file's contents
  listed the four linter configs sitting beside it — so the collection would
  have been published without the configs it exists to deploy.
- The test VM is `macos-tahoe-base` rather than `macos-sequoia-base`.

### Check mode

`ansible-playbook --check --diff` now completes against a Mac this collection
has already configured. Every read-only probe that a later task branches on —
`dockutil --find`, `brew --cache`, `uuidgen` — carries `check_mode: false`,
because `command` skips itself in a check run and a skipped result has no
`stdout` to read. `which dockutil` was replaced by a `stat`, which needs no
exemption. Each role README states what a check run does and does not cover.
