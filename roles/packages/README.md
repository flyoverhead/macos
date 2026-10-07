# `flyoverhead.macos.packages`

Installs Homebrew and then everything else: brew formulae, casks and taps, DMG
images, standalone binaries from an archive URL, and Python packages into a
virtualenv. Afterwards it configures git, ssh, nano, vim, iTerm2, VS Code /
VSCodium and Docker, and deploys a pre-commit hook with a set of linter
configurations. Claude Code lives in its own role, `flyoverhead.macos.claude`.

Every list defaults to empty, so the role installs nothing until told to.

## Role variables

### User and paths

| Variable | Description | Example |
| :--- | :--- | :--- |
| `packages_user_name` | User to install and configure for | `{{ ansible_user }}` |
| `packages_user_group` | That user's primary group | `{{ ansible_facts.user_gid }}` |
| `packages_user_home` | That user's home directory | `{{ ansible_facts.user_dir }}` |
| `packages_tmp_path` | Scratch directory for DMG and archive downloads | `/Users/me/tmp` |
| `packages_venv_path` | Virtualenv `packages_pip` is installed into, created with `uv venv` | `/Users/me/.venv` |
| `packages_binary_path` | Where archive binaries are installed | `/usr/local/bin` |

### Homebrew

| Variable | Description | Example |
| :--- | :--- | :--- |
| `packages_homebrew_repo` | Repository Homebrew is cloned from | `https://github.com/Homebrew/brew` |
| `packages_homebrew_version` | Git ref to clone | `master` |
| `packages_homebrew_root_path` | Homebrew prefix | `/opt/homebrew` |
| `packages_homebrew_bin_path` | Homebrew `bin` directory | `/opt/homebrew/bin` |
| `packages_brew_folders` | Directory structure created under the prefix | Definition example in [defaults/main.yml](defaults/main.yml) |
| `packages_brew` | Formulae. A plain name, or a mapping with `name`, `state`, `path`, `install_options` | `[git, python3]` |
| `packages_brew_taps` | Taps. A plain name, or a mapping with `name`, `url`, `state` | `[cirruslabs/cli]` |
| `packages_brew_casks` | Casks. A plain name, or a mapping with `name`, `state`, `greedy`, `accept_external_apps`, `install_options` | `[iterm2, vscodium]` |
| `packages_brew_cask_apps_path` | Where casks install applications | `/Applications` |
| `packages_brew_upgrade` | Run `brew upgrade` for everything | `false` |
| `packages_brew_clear_cache` | Delete the download cache afterwards | `false` |

### Other package sources

| Variable | Description | Example |
| :--- | :--- | :--- |
| `packages_dmg` | Disk images: `name`, `url`, optional `app_name` | Definition example in [defaults/main.yml](defaults/main.yml) |
| `packages_binary` | Archives holding a single binary: `name`, `url` | Definition example in [defaults/main.yml](defaults/main.yml) |
| `packages_pip` | Packages installed into `packages_venv_path` with `uv pip install`. Requires `uv` in `packages_brew` | `[ansible-lint, yamllint]` |
| `packages_rosetta_install` | Install Rosetta 2. Skipped on Intel | `false` |

### Configuration

| Variable | Description | Example |
| :--- | :--- | :--- |
| `packages_git_config` | Global git options: `name`, `value`. Not logged | Definition example in [defaults/main.yml](defaults/main.yml) |
| `packages_ssh_hosts` | `~/.ssh/config` stanzas: `host` plus an `options` mapping | Definition example in [defaults/main.yml](defaults/main.yml) |
| `packages_vscode_extensions` | Extension identifiers | `[redhat.ansible]` |
| `packages_vscode_settings` | Deep-merged over the base settings and the editor's `settings.json` | Definition example in [defaults/main.yml](defaults/main.yml) |
| `packages_docker_config` | Deep-merged over `~/.docker/config.json`. Not logged | Definition example in [defaults/main.yml](defaults/main.yml) |
| `packages_pre_commit_install` | Deploy the pre-commit hook and configs | `true` |
| `packages_pre_commit_path` | Git template directory | `/Users/me/.pre-commit` |
| `packages_pre_commit_hooks_path` | Where the hook and configs are installed | `/Users/me/.pre-commit/hooks` |
| `packages_pre_commit_configs` | Configs the hook copies into a repository | Definition example in [defaults/main.yml](defaults/main.yml) |

`packages_ssh_hosts` renders one stanza per entry, in order. An option whose
value is a list is emitted once per element, which is what `IdentityFile`
needs:

```yaml
packages_ssh_hosts:
  - host: '*'
    options:
      UseKeychain: 'yes'
      IdentityFile:
        - ~/.ssh/id_ed25519
        - ~/.ssh/work
```

Quote `yes` and `no` — unquoted, YAML turns them into booleans and ssh rejects
`True`.

## Facts set by this role

| Fact | Description |
| :--- | :--- |
| `packages_homebrew_installed` | Whether `brew` already exists at the configured prefix; a false value triggers the install |
| `packages_homebrew_user` / `packages_homebrew_group` | Ownership applied to the Homebrew prefix |
| `packages_homebrew_cache_path` | Registered only when `packages_brew_clear_cache` is set; read by the handler |
| `packages_vscode_executable` | `code` or `codium`, from which cask is present |
| `packages_vscode_config_path` | Settings directory for whichever editor that is |
| `packages_iterm_config_path` | iTerm2 DynamicProfiles directory |

## Behaviour worth knowing before the first run

- **Homebrew is installed by git clone at a branch, not a release.** With
  `packages_homebrew_version` at its `master` default, the first run gets
  upstream as of that moment; `update: false` then leaves the checkout alone,
  so later runs change nothing unless `packages_brew_upgrade` is set.
- **Configuration files are overwritten, not merged.** `~/.vimrc` and
  `~/.config/nano/nanorc` are templated with `force: true` every run. Local
  edits are lost. `~/.ssh/config` is managed with `blockinfile`, so only the
  delimited block is replaced; the VS Code `settings.json` and
  `~/.docker/config.json` are merged (below).
- **The VS Code `settings.json` is deep-merged.** The editor's own file is the
  base, the role's settings (`templates/vscode.j2`) go over it, and
  `packages_vscode_settings` goes over both, so settings changed in the editor
  survive unless the role or the variable names them. Removing a key from the
  variable does not remove it from the file. The parsed content is compared,
  so the editor's formatting is not a change. The file must be plain JSON: a
  `settings.json` with comments or trailing commas fails to parse.
- **`packages_docker_config` is deep-merged over `~/.docker/config.json`.**
  Docker Desktop keeps its own keys there (`currentContext`, `features`,
  `plugins`), so they survive; keys you name win and a list you name replaces
  the existing one. The parsed content is compared, so Docker Desktop
  rewriting the file in its own format is not a change. The file is set to
  `0600` because `auths` carries credentials — supply it from a vault. Every
  task touching it is `no_log: true`, so a failure will not show its content.
- **The iTerm2 profile is written once.** It is skipped if a profile named
  after the user already exists, because the GUID is generated at creation
  time; changing the template afterwards has no effect until you delete the
  file.
- **The editor blocks are conditional on casks.** The VS Code block runs only
  when `vscodium` or `visual-studio-code` is in `packages_brew_casks`, iTerm2
  only when `iterm2` is, Docker only when `docker` or `docker-desktop` is, and nano only when
  `nano` is in `packages_brew`. Installing an editor by other means will not
  get it configured.
- **Extensions are installed for whichever editor the cask list names**, and
  they are per-user — the task runs as `packages_user_name`.
- **DMG installation assumes an `.app` bundle at the top level of the image.**
  Images that ship an installer `.pkg` instead fail with a message saying so.
  The application is copied to `<app_name | name | capitalize>.app`, so set
  `app_name` when the bundle inside is not simply the capitalised name.
- **No tags.** The role runs as a whole.

## Check mode

`--check --diff` reports drift in the templated configuration files against a
machine where Homebrew and the casks are already installed.

It cannot usefully check a machine without Homebrew: the package modules report
what they would install, but every later task depends on binaries that are not
there, and the editor and Docker blocks are gated on casks the check run has
not installed.

`config | create iterm2 guid` runs even in a check run — it only generates a
UUID, and the template that reads it would otherwise fail on an undefined
variable. `brew | get cache path` likewise only reads.

## Example playbook

```yaml
- hosts: workstation
  gather_facts: true
  roles:
    - role: flyoverhead.macos.packages
      vars:
        packages_brew:
          - git
          - python3
        packages_brew_casks:
          - iterm2
          - vscodium
        packages_vscode_extensions:
          - redhat.ansible
```
