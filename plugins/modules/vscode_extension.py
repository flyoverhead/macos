#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2026, flyoverhead
# GNU General Public License v3.0 only (see https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
module: vscode_extension
short_description: Manage Visual Studio Code and VSCodium extensions
version_added: 1.0.0
description:
  - Installs, upgrades and removes extensions for Visual Studio Code, VSCodium,
    VS Code Insiders and Code OSS by driving the editor's own command line.
  - Idempotency is determined by reading the installed extension list, and for
    upgrades by comparing the extension directory names, which carry the version
    number.
options:
  executable:
    description:
      - The editor command line to drive.
      - Must be resolvable on C(PATH); pass the Homebrew C(bin) directory through
        the task C(environment) if it is not.
    type: str
    choices:
      - code
      - code-insiders
      - code-oss
      - codium
    default: code
  name:
    description:
      - Extension identifier in C(publisher.name) form, for example
        C(redhat.ansible).
    type: str
    required: true
  state:
    description:
      - C(present) installs the extension, and upgrades it if already installed.
      - C(absent) removes it.
    type: str
    choices:
      - absent
      - present
    default: present
notes:
  - Runs as the user who owns the editor's extension directory. Extensions are
    per-user, so C(become_user) matters.
  - An C(absent) run reports C(changed) only when the extension was present.
author:
  - flyoverhead (@flyoverhead)
'''

EXAMPLES = r'''
- name: Install the Ansible extension into VSCodium
  flyoverhead.macos.vscode_extension:
    executable: codium
    name: redhat.ansible
    state: present

- name: Install several extensions
  flyoverhead.macos.vscode_extension:
    executable: codium
    name: '{{ extension }}'
  loop:
    - hashicorp.terraform
    - redhat.vscode-yaml
  loop_control:
    loop_var: extension

- name: Remove an extension
  flyoverhead.macos.vscode_extension:
    executable: code
    name: ms-python.python
    state: absent
'''

RETURN = r'''
msg:
  description: What the module did to the extension.
  returned: always
  type: str
  sample: redhat.ansible is now installed
action:
  description:
    - The operation performed. C(none) when the extension was already in the
      requested state.
  returned: always
  type: str
  choices:
    - install
    - upgrade
    - uninstall
    - none
  sample: install
'''

import os

from ansible.module_utils.basic import AnsibleModule

# The extension directory lives under a different dotdir per editor build.
EXTENSION_DIRS = {
    'code': '.vscode',
    'code-insiders': '.vscode-insiders',
    'code-oss': '.vscode-oss',
    'codium': '.vscode-oss',
}

# `code --install-extension` emits this deprecation warning on some Node
# builds. It is not an error, so it must not fail the task.
IGNORED_STDERR = '[DEP0005]'


def _failed(rc, stderr):
    return rc != 0 or (stderr and IGNORED_STDERR not in stderr)


def installed_extensions(module, executable):
    """Return the lowercased set of installed extension identifiers."""
    rc, stdout, stderr = module.run_command([executable, '--list-extensions'])
    if _failed(rc, stderr):
        module.fail_json(
            msg='Error querying installed extensions: '
                '({0}) {1}'.format(rc, stdout + stderr))
    return {line.strip().lower() for line in stdout.splitlines() if line.strip()}


def is_installed(module, executable, name):
    return name.lower() in installed_extensions(module, executable)


def extension_dirs(executable):
    """Directory names under the extensions dir; each carries a version."""
    ext_dir = os.path.expanduser(
        os.path.join('~', EXTENSION_DIRS[executable], 'extensions'))
    if not os.path.isdir(ext_dir):
        return []
    return sorted(entry for entry in os.listdir(ext_dir)
                  if os.path.isdir(os.path.join(ext_dir, entry)))


def install(module, executable, name):
    """Install or upgrade. Returns (changed, action)."""
    if is_installed(module, executable, name):
        if module.check_mode:
            # An upgrade cannot be predicted without contacting the
            # marketplace, so report no change rather than guess.
            return False, 'none'
        # Extension directory names carry the version, so a change in the
        # listing is the only reliable upgrade signal: `--force` suppresses
        # the output that would otherwise say.
        before = extension_dirs(executable)
        rc, stdout, stderr = module.run_command(
            [executable, '--install-extension', name, '--force'])
        if _failed(rc, stderr):
            module.fail_json(
                msg='Error while upgrading extension [{0}]: '
                    '({1}) {2}'.format(name, rc, stdout + stderr))
        return before != extension_dirs(executable), 'upgrade'

    if module.check_mode:
        return True, 'install'

    rc, stdout, stderr = module.run_command(
        [executable, '--install-extension', name])
    if _failed(rc, stderr):
        module.fail_json(
            msg='Error while installing extension [{0}]: '
                '({1}) {2}'.format(name, rc, stdout + stderr))
    return 'already installed' not in stdout, 'install'


def uninstall(module, executable, name):
    """Remove the extension. Returns (changed, action)."""
    if not is_installed(module, executable, name):
        return False, 'none'

    if module.check_mode:
        return True, 'uninstall'

    rc, stdout, stderr = module.run_command(
        [executable, '--uninstall-extension', name])
    if 'successfully uninstalled' not in (stdout + stderr):
        module.fail_json(
            msg='Error while uninstalling extension [{0}], unexpected '
                'response: ({1}) {2}'.format(name, rc, stdout + stderr))
    return True, 'uninstall'


def run_module():
    module = AnsibleModule(
        argument_spec=dict(
            executable=dict(
                type='str',
                default='code',
                choices=sorted(EXTENSION_DIRS)),
            name=dict(type='str', required=True),
            state=dict(
                type='str',
                default='present',
                choices=['absent', 'present']),
        ),
        supports_check_mode=True,
    )

    executable = module.params['executable']
    name = module.params['name']
    state = module.params['state']

    if state == 'absent':
        changed, action = uninstall(module, executable, name)
        msg = ('{0} is now uninstalled' if changed
               else '{0} is not installed').format(name)
    else:
        changed, action = install(module, executable, name)
        if action == 'upgrade' and changed:
            msg = '{0} was upgraded'.format(name)
        elif changed:
            msg = '{0} is now installed'.format(name)
        else:
            msg = '{0} is already installed'.format(name)

    module.exit_json(changed=changed, action=action, msg=msg)


def main():
    run_module()


if __name__ == '__main__':
    main()
