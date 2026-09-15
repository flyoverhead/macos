# `flyoverhead.macos`

[![Version](https://img.shields.io/badge/version-1.0.0-blue)](galaxy.yml)
[![ansible-core](https://img.shields.io/badge/ansible--core-%E2%89%A52.16-black?logo=ansible&logoColor=white)](https://docs.ansible.com/ansible-core/devel/index.html)
[![License](https://img.shields.io/badge/license-GPL--3.0--only-green)](https://www.gnu.org/licenses/gpl-3.0)
[![Platform](https://img.shields.io/badge/platform-macOS%2015%20%7C%2026-000000?logo=apple&logoColor=white)](#-supported-os)
[![Roles](https://img.shields.io/badge/roles-4-orange)](#-roles)

macOS workstation configuration: Homebrew and the software on top of it, a zsh
login shell, the Dock, and system preferences.

These roles configure a Mac you already have. Every list they take defaults to
empty, so the collection installs nothing until an inventory tells it what to
install.

## 🚀 Quick Start

### Requirements

- `ansible-core >=2.16`

- Collections: `community.general >=8.0.0`

- macOS on Apple Silicon, with an administrator account for `become`

- `uv`, from `packages_brew`: `roles/packages/tasks/pip.yml` hard-fails
  without it

- Task `>=3.20` and [Tart](https://tart.run/), for the test harness only

### Installation

Installing the collection dependencies:

```bash
ansible-galaxy collection install -r requirements.yml
uv pip install --python "$HOME/.venv/bin/python" -r requirements.txt
```

Installing the collection itself:

```bash
ansible-galaxy collection install git+https://github.com/flyoverhead/macos.git
```

### Roles usage

Full documentation and usage examples of role `<role>` can be found in
`roles/<role>/README.md`.

Run `flyoverhead.macos.packages` first. It installs Homebrew, which the other
three depend on, plus the applications that `dock` places and the font that
makes the `ohmyzsh` prompt render. `dock` needs `dockutil` and the applications
themselves, so it goes after `packages`. `osx` is independent and can go
anywhere.

### Example Playbook

```yaml
---
- hosts: workstation
  gather_facts: true
  roles:
    - flyoverhead.macos.packages
    - flyoverhead.macos.ohmyzsh
    - flyoverhead.macos.dock
    - flyoverhead.macos.osx
```

A worked configuration for all four roles is in
[tests/group_vars/](tests/group_vars), which is what the test harness runs.

## 🖥 Supported OS

| OS | Status |
| :--- | :--- |
| macOS 26 "Tahoe" (Apple Silicon) | Tested |
| macOS 15 "Sequoia" (Apple Silicon) | Supported |

Apple Silicon only. `packages_homebrew_root_path` defaults to `/opt/homebrew`,
which is the Apple Silicon prefix; an Intel Mac needs it set to
`/usr/local`. Rosetta installation is skipped on Intel automatically.

## 📦 Roles

| Name | Description |
| :--- | :--- |
| [`packages`](roles/packages/README.md) | Homebrew, formulae, casks, DMGs, binaries, uv; git, ssh, nano, vim, iTerm2, VS Code and Docker configuration |
| [`ohmyzsh`](roles/ohmyzsh/README.md) | Oh My Zsh, powerlevel10k, plugins, `.zshrc` |
| [`dock`](roles/dock/README.md) | Dock contents and ordering via dockutil |
| [`osx`](roles/osx/README.md) | System preferences via the `defaults` database |

## 🔌 Modules

| Name | Description |
| :--- | :--- |
| `flyoverhead.macos.vscode_extension` | Installs, upgrades and removes VS Code / VSCodium extensions |

```yaml
- name: Install an extension
  flyoverhead.macos.vscode_extension:
    executable: codium
    name: redhat.ansible
    state: present
```

## ⚠️ Gotchas

- **Configuration files are replaced, not merged.** `~/.zshrc`, `~/.p10k.zsh`,
  `~/.vimrc`, `~/.config/nano/nanorc`, the VS Code `settings.json` and
  `~/.docker/config.json` are rewritten on every run. `.zshrc` is backed up
  first; the others are not. `~/.ssh/config` is the exception — it is managed
  with `blockinfile`, so only the delimited block is touched.
- **`packages_docker_config` becomes `~/.docker/config.json` verbatim**,
  including any `auths` you put in it. Supply it from a vault. The task is
  `no_log: true`, as is the `git_config` loop, since a signing key is usually
  set there.
- **`dock` is slow by design.** Every dockutil write restarts the Dock, and the
  role waits `dock_apply_timeout` (15s) between items, because a rapid sequence
  of writes loses changes.
- **Homebrew is installed from a git branch, not a release.** A run reflects
  upstream at that moment.
- **Dock labels are localised.** `dock_items_remove` matches what the Dock
  displays, so the English names will not match on a non-English system.

## 🧪 Testing

Against a Tart VM:

```bash
task vm-deploy      # clone a macos-tahoe-base VM, boot it, configure it
task vm-provision   # re-run the playbook
task vm-destroy
```

Against the machine you are on:

```bash
task check          # syntax check, then --check --diff
task play
```

`task lint` runs `ansible-lint` and `yamllint`; `task build` produces the
collection tarball.

Check-mode support is per-role; see the `## Check mode` section of each role's
README for what a check run does and does not cover.

## 📄 License

GPL-3.0-only. See [LICENSE](LICENSE).

## 🙏 Acknowledgments

- [Homebrew](https://brew.sh/) — macOS package manager
- [Oh My Zsh](https://ohmyz.sh/) — zsh framework
- [powerlevel10k](https://github.com/romkatv/powerlevel10k) — zsh theme
- [dockutil](https://github.com/kcrawford/dockutil) — Dock management
- [Tart](https://tart.run/) — macOS virtualization
