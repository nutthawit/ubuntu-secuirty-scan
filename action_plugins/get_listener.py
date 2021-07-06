from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.plugins.action import ActionBase
import re

class ActionModule(ActionBase):
    
    _VALID_ARGS = frozenset(('listener_content',))

    def run(self, tmp=None, task_vars=None):

        result = super(ActionModule, self).run(tmp, task_vars)
        
        # Create origin_list to store output from stdout_lines
        origin_listener = self._task.args.get('listener_content')
        
        # Find listener name from listener.ora content
        find_listeners = re.findall('(\w+)\s*=\s*\(DESCRIPTION_LIST =', origin_listener)

        result['results'] = find_listeners

        return result
