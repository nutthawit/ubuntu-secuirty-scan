from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os

from ansible.errors import AnsibleError
from ansible.playbook.conditional import Conditional
from ansible.plugins.action import ActionBase
from ansible.module_utils.six import string_types
from ansible.module_utils._text import to_bytes

class ActionModule(ActionBase):
    '''
    Example usage
    assert_csv:
      item_no: "0.1.1"
      level: "m"
      topic: "example"
      action: "# systemctl"
      check_command: ""
      expected_result: "Disabled"
      result: check_result
      remark: "Test topic"
      report_date: tsal_report_dir
      error_item:
        - error_list
      that:
        - conditions
    '''
    TRANSFERS_FILES = False
    _VALID_ARGS = frozenset(('fail_msg', 'msg', 'success_msg', 'that', 'topic', 'report_date', 'item_no', 'level', 'action', 'check_command', 'expected_result', 'result', 'remark', 'error_item'))
    REPORT_DIR = 'reports'
    MSG_FORMAT = ',"%(item)s","%(level)s","%(topic)s","%(action)s","%(checkcmd)s","%(expected)s","%(result)s","%(state)s","%(remark)s","%(error_item)s",\n'

    # def __init__(self):
    #     self.ITEM_NO = ''
    #     self.LEVEL = "M"
    #     self.TOPIC = str()
    #     self.ACTION = str()
    #     self.CHECK_CMD = str()
    #     self.EXPC_RES = str()
    #     self.RESULT = str()
    #     self.REMARK = str()
    #     self.ERROR_ITEM = list()
    #     self.REPORT_DATE= str()
    #     self.HOSTNAME= str()
    #     self.THAT = False
    #     print("Pass init func")
    ITEM_NO = ''
    LEVEL = "M"
    TOPIC = str()
    ACTION = str()
    CHECK_CMD = str()
    EXPC_RES = str()
    RESULT = str()
    REMARK = str()
    ERROR_ITEM = list()
    REPORT_DATE= str()
    HOSTNAME= str()


    def count_totals(self,reportf):
        with open(reportf,'r') as f: keep = f.read()

        searching = keep[keep.find("Scan Totals:"):keep.find(",Scan Passed:")]

        with_rep = int(keep[keep.find("Scan Totals:")+13:keep.find(",,,,,,,,\n,Scan Passed:")]) + 1

        new_text = "Scan Totals:," + str(with_rep) + ",,,,,,,,\n"

        with open(reportf,'w') as f: f.write(keep.replace(searching , new_text))
    
    def count_passed(self,hostname):
        report_dir = os.path.join(self.REPORT_DIR, self.REPORT_DATE)
        REPORT_FILE = os.path.join(report_dir, hostname + '.csv')
        with open(REPORT_FILE,'r') as f: keep = f.read()

        searching = keep[keep.find("Scan Passed:"):keep.find(",Scan Failed:")]

        with_rep = int(keep[keep.find("Scan Passed:")+13:keep.find(",,,,,,,,\n,Scan Failed:")]) + 1

        new_text = "Scan Passed:," + str(with_rep) + ",,,,,,,,\n"

        with open(REPORT_FILE,'w') as f: f.write(keep.replace(searching , new_text))
        self.count_totals(REPORT_FILE)

    def count_failed(self,hostname):
        report_dir = os.path.join(self.REPORT_DIR, self.REPORT_DATE)
        REPORT_FILE = os.path.join(report_dir, hostname + '.csv')
        with open(REPORT_FILE,'r') as f: keep = f.read()

        searching = keep[keep.find("Scan Failed:"):keep.find(",Last Scan:")]

        with_rep = int(keep[keep.find("Scan Failed:")+13:keep.find(",,,,,,,,\n,Last Scan:")]) + 1

        new_text = "Scan Failed:," + str(with_rep) + ",,,,,,,,\n"

        with open(REPORT_FILE,'w') as f: f.write(keep.replace(searching , new_text))
        self.count_totals(REPORT_FILE)

    def report_csv(self, state, item , level, topic, action, checkcmd, expected, result, remark, error_item, hostname):
        report_dir = os.path.join(self.REPORT_DIR, self.REPORT_DATE)
        print("[+] Task record to >> " + report_dir)
        # report_dir = 'reports'
        if not os.path.exists(report_dir):
            os.makedirs(report_dir)
        REPORT_FILE = os.path.join(report_dir, self.HOSTNAME + '.csv')

        item = item if item != None else self.ITEM_NO
        level = level if level != None else self.LEVEL
        topic = topic if topic != None else self.TOPIC
        action = action if action != None else self.ACTION
        checkcmd = checkcmd if checkcmd != None else self.CHECK_CMD
        expected = expected if expected != None else self.EXPC_RES
        result = result if result != None else self.RESULT
        remark = remark if remark != None else self.REMARK
        error_item = error_item if error_item != None else self.ERROR_ITEM
        hostname = hostname if hostname != None else self.HOSTNAME

        msg = to_bytes(self.MSG_FORMAT % dict(item=item, level=level, topic=topic, action=action, checkcmd=checkcmd, expected=expected, result=result, state=state, remark=remark, error_item=error_item))
        with open(REPORT_FILE, "ab") as fd:
            fd.write(msg)

    def run(self, tmp=None, task_vars=None):
        if task_vars is None:
            task_vars = dict()
        self.HOSTNAME=task_vars['ansible_hostname']
        if self._task.args.get('report_date') is None:
            self.REPORT_DATE=task_vars['tsal_report_dir']
        else:
            self.REPORT_DATE=self._task.args.get('report_date')

        result = super(ActionModule, self).run(tmp, task_vars)
        del tmp  # tmp no longer has any effect

        if 'that' not in self._task.args:
            raise AnsibleError('conditional required in "that" string')

        fail_msg = None
        success_msg = None

        fail_msg = self._task.args.get('fail_msg', self._task.args.get('msg'))
        if fail_msg is None:
            fail_msg = 'Assertion failed'
        elif not isinstance(fail_msg, string_types):
            raise AnsibleError('Incorrect type for fail_msg or msg, expected string and got %s' % type(fail_msg))

        success_msg = self._task.args.get('success_msg')
        if success_msg is None:
            success_msg = 'All assertions passed'
        elif not isinstance(success_msg, string_types):
            raise AnsibleError('Incorrect type for success_msg, expected string and got %s' % type(success_msg))

        # make sure the 'that' items are a list
        thats = self._task.args['that']
        if not isinstance(thats, list):
            thats = [thats]

        # Now we iterate over the that items, temporarily assigning them
        # to the task's when value so we can evaluate the conditional using
        # the built in evaluate function. The when has already been evaluated
        # by this point, and is not used again, so we don't care about mangling
        # that value now
        cond = Conditional(loader=self._loader)
        result['_ansible_verbose_always'] = True
        lst_itemserr = self._task.args.get('error_item')
        # if lst_itemserr:
        #     lst_itemserr = list(set(lst_itemserr))
        #     lst_itemserr.pop(lst_itemserr.index('undefined'))
        is_task_pass = True
        for that in thats:
            cond.when = [that]
            try:
                test_result = cond.evaluate_conditional(templar=self._templar, all_vars=task_vars)
            except:
                test_result = False
            if not test_result:
                is_task_pass = False
            elif test_result and lst_itemserr:
                try:
                    lst_itemserr[thats.index(that)] = ''
                except (IndexError,ValueError):
                    print("[-] Unable to pop in condition: " + that + "\n[-] At index " + str(thats.index(that)+1))
                    if len(lst_itemserr[thats.index(that)-1:-1]) == 0:
                        print("[-] Error index was too shortly than list of [that]" )
                    else: pass
                pass
        if lst_itemserr:
            lst_itemserr = filter(None, lst_itemserr)
            itemerr = "\n".join(lst_itemserr)
        else:
            itemerr = ""
        if not is_task_pass:
            result['failed'] = True
            result['evaluated_to'] = test_result
            result['assertion'] = that

            result['msg'] = fail_msg
            self.report_csv('FAILED', self._task.args.get('item_no'), self._task.args.get('level'), self._task.args.get('topic'), self._task.args.get('action'), self._task.args.get('check_command'), self._task.args.get('expected_result'), self._task.args.get('result'), self._task.args.get('remark'), itemerr, self.HOSTNAME)
            self.count_failed(task_vars['ansible_hostname'])
            return result
        else:
            result['changed'] = False
            result['msg'] = success_msg
            self.report_csv('PASS', self._task.args.get('item_no'), self._task.args.get('level'), self._task.args.get('topic'), self._task.args.get('action'), self._task.args.get('check_command'), self._task.args.get('expected_result'), self._task.args.get('result'), self._task.args.get('remark'), itemerr, self.HOSTNAME)
            self.count_passed(task_vars['ansible_hostname'])
            return result
