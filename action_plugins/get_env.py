from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.plugins.action import ActionBase

class ActionModule(ActionBase):
    
    _VALID_ARGS = frozenset(('env_list',))

    def run(self, tmp=None, task_vars=None):

        result = super(ActionModule, self).run(tmp, task_vars)
        
        # Create origin_list to store output from stdout_lines
        origin_env = self._task.args.get('env_list')

        # Create new array to store value after re-formating
        get_env = {}

        # Looping to seperate env to dictionary format
        for e in origin_env:
            # Process values only if there is '=' inside string!
            if '=' in e:
                # Seperate values with '='
                v = e.split('=', 1)
                # Push value into an array
                get_env.update({v[0]: v[1]})

        result = get_env

        return result
