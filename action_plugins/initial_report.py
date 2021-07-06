from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import json

from ansible.errors import AnsibleError
from ansible.playbook.conditional import Conditional
from ansible.plugins.action import ActionBase
from ansible.module_utils.six import string_types
from ansible.module_utils._text import to_bytes

class ActionModule(ActionBase):
    '''
    Example usage
    initial_report:
      standard_name: "Test module standard"
      scan_date: tsal_scan_date
      report_date: tsal_report_dir
    '''

    TRANSFERS_FILES = False
    _VALID_ARGS = frozenset(('standard_name', 'scan_date', 'report_date'))
    REPORT_DIR = 'reports'
    LASTTIME_DIR = 'lasttimes'
    MSG_FORMAT = ',,,,,,,,,,\n,Standard Name:,%(standard_name)s,,,,,,,,\n,Server Name:,%(host)s,,,,,,,,\n,OS Version:,%(os_version)s,,,,,,,,\n,Scan date and time:,%(scan_date)s,,,,,,,,\n,Scan Totals:,0,,,,,,,,\n,Scan Passed:,0,,,,,,,,\n,Scan Failed:,0,,,,,,,,\n,Last Scan:,%(last_scan)s,,,,,,,,\n,Exception memo,,,,,,,,,\n,,,,,,,,,,\n,Item No.,Level,Task Requirement,Action or Value,Mismatch condition,Expect Result,Scan Result,Compliance State,Remark,Error items,Exception memo\n'
    
    def initial_report(self, standard_name, os_version, scan_date, host, last_scan):

        report_dir = os.path.join(self.REPORT_DIR, self._task.args.get('report_date'))
        # report_dir = 'reports'
        if not os.path.exists(report_dir):
            os.makedirs(report_dir)
        path = os.path.join(report_dir, host + '.csv')

        msg = to_bytes(self.MSG_FORMAT % dict(standard_name=standard_name, host=host, os_version=os_version, scan_date=scan_date, last_scan=last_scan))
        with open(path, "ab") as fd:
            fd.write(msg)

    def run(self, tmp=None, task_vars=None):
        if task_vars is None:
            task_vars = dict()

        result = super(ActionModule, self).run(tmp, task_vars)
        del tmp  # tmp no longer has any effect

        success_msg = 'Reports are successfully initialized'

        result['_ansible_verbose_always'] = True
        result['changed'] = False
        result['msg'] = success_msg
        last_scan = self.get_lasttimes(task_vars['ansible_hostname'], self._task.args.get('scan_date'))
        self.initial_report(self._task.args.get('standard_name'), task_vars['ansible_distribution_version'], self._task.args.get('scan_date'), task_vars['ansible_hostname'], last_scan)
        self.save_lasttimes(task_vars['ansible_hostname'], self._task.args.get('scan_date'))
        return result

    def save_lasttimes(self, host, scan_date):
        
        lasttime_dir = os.path.join(self.REPORT_DIR, self.LASTTIME_DIR)
        if not os.path.exists(lasttime_dir):
            os.makedirs(lasttime_dir)

        path = os.path.join(lasttime_dir, self.LASTTIME_DIR + '.json')
        if not os.path.exists(path):
            with open(path, "a"):
                os.utime(path, None)

        with open(path) as fd:  
            try:
                buffer = json.load(fd)
            except ValueError:
                buffer = {}
        
        buffer[host] = scan_date

        with open(path, "w") as fd:
            json.dump(buffer, fd)

    def get_lasttimes(self, host, scan_date):

        result = scan_date
        lasttime_dir = os.path.join(self.REPORT_DIR, self.LASTTIME_DIR)
        path = os.path.join(lasttime_dir, self.LASTTIME_DIR + '.json')

        if (os.path.exists(lasttime_dir) and os.path.exists(path)):
            with open(path) as fd:
                buffer = json.load(fd)
            if (buffer.get(host)):
                result = buffer.get(host)
            
        return result


