# `flyoverhead.macos.osx`

Writes macOS system preferences through the `defaults` database, then restarts
the processes that read them so the changes apply without a logout.

A thin wrapper over `community.general.osx_defaults`: the value of this role is
that it takes one list, infers the type when you omit it, and reloads once at
the end rather than per key.

## Role variables

| Variable | Description | Example |
| :--- | :--- | :--- |
| `osx_defaults` | Preferences to write: `key` plus optional `domain`, `type`, `value`, `state` | Definition example in [defaults/main.yml](defaults/main.yml) |
| `osx_reload_services` | Processes signalled after any change | `[Dock, Finder, SystemUIServer]` |

`domain` defaults to `NSGlobalDomain`, `state` to `present`, and `type` is
inferred from the value:

```yaml
osx_defaults:
  - domain: com.apple.dock
    key: tilesize
    type: float
    value: 50
  - domain: com.apple.finder
    key: ShowPathbar
    value: true          # inferred as bool
```

Inference maps Python types onto the vocabulary `osx_defaults` expects, via
`osx_type_map` in [vars/main.yml](vars/main.yml) — `str` to `string`, `list` to
`array`, and so on. Anything unrecognised becomes `string`. Being explicit is
still better where it matters: an integer written as `int` and as `float` are
different preferences to some applications, `tilesize` among them.

## Facts set by this role

None.

## Behaviour worth knowing before the first run

- **Not every preference takes effect on a restart of these three processes.**
  Some are read at login, some by an application at launch, some are cached by
  `cfprefsd`. If a key looks like it did not apply, log out and back in before
  assuming the role is at fault.
- **Some domains are protected.** Under System Integrity Protection a number of
  preferences cannot be written by `defaults` at all, and others need Full Disk
  Access for the process running Ansible. The task fails cleanly when this
  happens.
- **`killall` is not an error when the process is not running.** Exit code 1 is
  accepted, so the handler works on a machine where, say, SystemUIServer is
  absent.
- **The reload runs once**, as a handler, after all the keys are written.
- **Removal means removal.** `state: absent` deletes the key so the application
  falls back to its own default, which is not necessarily the macOS factory
  setting.
- **No tags.** The role runs as a whole.

## Check mode

`--check --diff` works fully. `osx_defaults` supports check mode natively and
reports per-key drift without writing.

The reload handler is `command`, which a check run skips, so a check run tells
you which preferences would change but never signals the processes.

## Example playbook

```yaml
- hosts: workstation
  gather_facts: true
  roles:
    - role: flyoverhead.macos.osx
      vars:
        osx_defaults:
          - domain: com.apple.dock
            key: tilesize
            type: float
            value: 50
          - domain: com.apple.finder
            key: ShowPathbar
            value: true
```
