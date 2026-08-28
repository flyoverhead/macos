# `flyoverhead.macos.dock`

Manages the contents and ordering of the macOS Dock with
[dockutil](https://github.com/kcrawford/dockutil), which it installs from
Homebrew. Removals happen before additions, and each item is placed at the
position you give it.

## Role variables

| Variable | Description | Example |
| :--- | :--- | :--- |
| `dock_items_add` | Items to place: `name`, `path`, optional `position` | Definition example in [defaults/main.yml](defaults/main.yml) |
| `dock_items_remove` | Items to remove. A plain name, or a mapping with `name` | `[Mail, Maps, TV]` |
| `dock_user_name` | User whose Dock is managed | `{{ ansible_user }}` |
| `dock_user_group` | That user's primary group | `{{ ansible_user_gid }}` |
| `dock_user_home` | That user's home directory | `{{ ansible_user_dir }}` |
| `dock_homebrew_bin_path` | Homebrew `bin` directory, where dockutil is found | `/opt/homebrew/bin` |
| `dock_brew_clear_cache` | Delete the Homebrew download cache after installing dockutil | `false` |
| `dock_apply_timeout` | Seconds to wait after each change for the Dock to settle | `15` |

`position` is 1-based and counts the whole persistent-apps section, including
Finder. A `position` of `0` or absent means the item is added but not moved.

```yaml
dock_items_add:
  - name: iTerm
    path: /Applications/iTerm.app
    position: 4
```

## Facts set by this role

| Fact | Description |
| :--- | :--- |
| `dock_dockutil_installed` | Whether `dockutil` exists at the configured Homebrew prefix; a false value triggers the install |
| `dock_items_all` | `dock_items_remove` and `dock_items_add` normalised into one ordered list, each entry carrying its own `state` |
| `dock_homebrew_cache_path` | Registered only when `dock_brew_clear_cache` is set; read by the handler |
| `dock_item_section` | Which Dock section the current item was found in, or empty |
| `dock_item_slot` | The current item's slot number, or `0` |

## Behaviour worth knowing before the first run

- **Each change restarts the Dock**, and the role waits `dock_apply_timeout`
  seconds afterwards. With a dozen items that is a slow role by construction —
  handlers are flushed between items on purpose, because a rapid sequence of
  dockutil writes loses changes.
- **The applications have to exist already.** dockutil will happily add a
  path that is not there, giving you a broken tile. Run the `packages` role
  first.
- **An application sitting in `recent-apps` is treated as absent** and added as
  a persistent item, because a recent-apps entry is not a Dock entry.
- **Ordering depends on dockutil's `--find` output format.** The slot number is
  parsed out of it with a regex. A future dockutil that reworks its wording
  would leave items added but unordered, not misplaced.
- **`dock_items_remove` entries name the label, not the path** — `Mail`, not
  `/System/Applications/Mail.app`. Labels are what the Dock shows, and they are
  localised: on a non-English system, the English name will not match.
- **No tags.** The role runs as a whole.

## Check mode

`--check --diff` is honest but not very useful here, and it will not fail.

The three `dockutil --find` probes carry `check_mode: false` — they only read,
and the add, remove and move decisions all branch on their output, so without
the exemption a check run would abort on a missing `stdout`. What a check run
therefore reports is accurate for removals and additions.

It cannot report ordering correctly: the re-read after an add returns the state
before the add that never happened, so items that would be added are reported
as not needing a move.

## Example playbook

```yaml
- hosts: workstation
  gather_facts: true
  roles:
    - role: flyoverhead.macos.dock
      vars:
        dock_items_add:
          - name: iTerm
            path: /Applications/iTerm.app
            position: 3
        dock_items_remove:
          - Mail
          - TV
```
