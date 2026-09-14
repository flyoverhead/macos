# `flyoverhead.macos.ohmyzsh`

Installs Oh My Zsh with the powerlevel10k theme and a set of Homebrew-provided
plugins, writes `.zshrc` and `.p10k.zsh`, and makes zsh the user's login shell.

This is the macOS counterpart of `flyoverhead.server.ohmyzsh`. They are not
interchangeable: this one installs through Homebrew, takes its fonts from a
cask rather than downloading them, and templates macOS-specific settings such
as `ssh-add --apple-load-keychain`.

## Role variables

| Variable | Description | Example |
| :--- | :--- | :--- |
| `ohmyzsh_user_name` | User to install for | `{{ ansible_user }}` |
| `ohmyzsh_user_group` | That user's primary group | `{{ ansible_user_gid }}` |
| `ohmyzsh_user_home` | That user's home directory | `{{ ansible_user_dir }}` |
| `ohmyzsh_repo` | Oh My Zsh repository | `https://github.com/ohmyzsh/ohmyzsh.git` |
| `ohmyzsh_version` | Git ref to clone | `master` |
| `ohmyzsh_shell` | Login shell to set | `/bin/zsh` |
| `ohmyzsh_dependencies` | Formulae installed first | `[curl, fzf, git, zsh]` |
| `ohmyzsh_install_plugins` | Plugin formulae to install and source: `name`, `source` | Definition example in [defaults/main.yml](defaults/main.yml) |
| `ohmyzsh_plugins` | Plugins written into the `plugins=(...)` line | `[git, pip, python]` |
| `ohmyzsh_theme` | `ZSH_THEME` value | `powerlevel10k/powerlevel10k` |
| `ohmyzsh_theme_package` | Formula providing the theme, and the directory it is sourced from | `powerlevel10k` |
| `ohmyzsh_venv_path` | Virtualenv prepended to `$PATH` | `/Users/me/.venv` |
| `ohmyzsh_homebrew_bin_path` | Homebrew `bin` directory | `/opt/homebrew/bin` |
| `ohmyzsh_ssh_key_file` | Identity given to the `ssh-agent` plugin | `/Users/me/.ssh/id_ed25519` |
| `ohmyzsh_force_reinstall` | Delete `~/.oh-my-zsh` and install again | `false` |
| `ohmyzsh_task_completion` | Emit go-task completions, guarded by a `command -v` check | `true` |
| `ohmyzsh_history_substring_bindkeys` | Bind up/down to history-substring-search | `true` |
| `ohmyzsh_extra_fpath` | Directories prepended to `$fpath` before `compinit` | `[]` |
| `ohmyzsh_vault_addr` | `VAULT_ADDR`, and the `vault-login` helper. Empty omits both | `''` |
| `ohmyzsh_exports` | Extra `export NAME=value` lines | `{EDITOR: nano}` |
| `ohmyzsh_ci_registry` | Registry for the `ci-run` helper | `''` |
| `ohmyzsh_ci_images` | Alias-to-image map for `ci-run` | `{ansible: ansible-ci:10}` |

`ohmyzsh_install_plugins` is what gets installed and sourced;
`ohmyzsh_plugins` is what Oh My Zsh itself loads. They are different
mechanisms — the first is a list of Homebrew formulae sourced by absolute path
from the Homebrew share directory, the second is the names of plugins bundled
with Oh My Zsh. A Homebrew plugin does not belong in `ohmyzsh_plugins`.

`source` differs per plugin and is not derivable from the name, which is why
the variable is a list of mappings:

```yaml
ohmyzsh_install_plugins:
  - name: zsh-autosuggestions
    source: zsh-autosuggestions.zsh
  - name: zsh-autocomplete
    source: zsh-autocomplete.plugin.zsh
```

`ci-run` and `vault-login` are only rendered when their variables are set, so
by default `.zshrc` contains neither.

## Facts set by this role

| Fact | Description |
| :--- | :--- |
| `ohmyzsh_installed` | Whether `~/.oh-my-zsh` already exists; a false value triggers the install |
| `ohmyzsh_homebrew_share_path` | Homebrew `share` directory, derived from the bin path, where the theme and plugins are sourced from |

## Behaviour worth knowing before the first run

- **`~/.zshrc` and `~/.p10k.zsh` are overwritten every run.** `.zshrc` is
  written with `backup: true`, so the previous version is kept beside it;
  `.p10k.zsh` is not backed up. Anything you want to survive belongs in
  `~/.aliases`, which the template sources if present.
- **The role needs egress to GitHub and to Homebrew.** Oh My Zsh is cloned from
  `github.com` at a branch, not a release, so a run reflects upstream at that
  moment.
- **The theme renders as boxes without the font.** powerlevel10k needs MesloLGS
  NF, which comes from the `font-meslo-for-powerlevel10k` cask — install it via
  the `packages` role, or the prompt will look broken. Your *terminal* also has
  to be set to use it.
- **The login shell change takes effect at next login**, not in the current
  session.
- **Plugins are sourced by absolute path**, from
  `ohmyzsh_homebrew_share_path`. Each `source` line is guarded by a file test,
  so a plugin whose formula lays its files out differently is skipped silently
  rather than breaking the shell.
- **Completion directories must be on `$fpath` before `compinit`.** Oh My Zsh
  runs `compinit` itself, before sourcing plugins, so anything added afterwards
  is never registered and fails with `command not found` at completion time.
  Hence `zsh-autocomplete`'s `Completions/` up front, and `ohmyzsh_extra_fpath`
  for other tools' directories.
- **`ohmyzsh_force_reinstall` deletes `~/.oh-my-zsh`.** Any custom plugins or
  themes you dropped in there by hand go with it.
- **No tags.** The role runs as a whole.

## Check mode

`--check --diff` reports drift in `.zshrc` and `.p10k.zsh` against a machine
where Oh My Zsh is already installed. The role has no `command` tasks, so
nothing needs a check-mode exemption.

Against a machine without Oh My Zsh, the clone and the Homebrew installs are
reported as pending without running, and the `.zshrc` diff is rendered against
a theme and plugin set that are not on the machine yet.

## Example playbook

```yaml
- hosts: workstation
  gather_facts: true
  roles:
    - role: flyoverhead.macos.ohmyzsh
      vars:
        ohmyzsh_plugins:
          - git
          - pip
          - python
```
