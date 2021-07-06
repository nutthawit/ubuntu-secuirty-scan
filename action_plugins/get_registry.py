from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.plugins.action import ActionBase
import re

class ActionModule(ActionBase):
    
    _VALID_ARGS = frozenset(('reg_list',))

    def run(self, tmp=None, task_vars=None):

        result = super(ActionModule, self).run(tmp, task_vars)
        
        #Save stdout_lines to origin_list
        origin_list = self._task.args.get('reg_list')
        
        #Create empty dict 
        registry_dict = dict()

        #Create pattern for registry path
        pattern = re.compile('\[.*\]')

        #Create registry_dict KEY with 'registry path' from origin_list
        for item in range(len(origin_list)):
            if pattern.match(origin_list[item]):
                registry_dict[origin_list[item]] = []

        #Create registry_dict VALUE
        for key in registry_dict.iterkeys(): 
            #Search 'registry path' from origin_list that match with KEY in registry_dict and get thire index (number)
            index = origin_list.index(key) 
            #Empty list for saved value
            value = [] 
            while True:
                #Plus index by 1 for indicate value of the 'registry path'
                index = index + 1 
                #Set cursor to current 'registry value'
                cursor = origin_list[index] 
                #Extend 'registry value' to 'value list(value[])'
                value.extend([cursor])
                #Set ncursor to next 'registry value' for confirm that is the final value
                try: ncursor = origin_list[index+1]
                except IndexError: ncursor = "[IndexError]" 
                #Loop will break when cursor equal empty string and ncursor match with 'registry path' pattern
                if cursor == "" and pattern.match(ncursor): break
            registry_dict.setdefault(key, []).append(value) #Append 'value list(value[])' to registry_dict as a VALUE 

        result['result'] = registry_dict
        return result


#### Sample output #####
# {
#     '[HKEY_LOCAL_MACHINE\\SOFTWARE\\Policies\\Microsoft\\Cryptography\\Configuration\\SSL]': [['']],
#     '[HKEY_LOCAL_MACHINE\\SOFTWARE\\Policies\\Microsoft\\Cryptography\\Configuration]': [['']],
#     '[HKEY_LOCAL_MACHINE\\SOFTWARE\\Policies\\Microsoft\\Cryptography]': [['"ForceKeyProtection"=dword:00000001','']],
#     '[HKEY_LOCAL_MACHINE\\SOFTWARE\\Policies\\Microsoft\\Windows NT\\Terminal Services\\Client]':[[
#         '"fEnableUsbNoAckIsochWriteToDevice"=dword:00000050', 
#         '"fEnableUsbBlockDeviceBySetupClass"=dword:00000001',
#         '"fEnableUsbSelectDeviceByInterface"=dword:00000001',
#         '']],
#     '[HKEY_LOCAL_MACHINE\\SOFTWARE\\Policies\\Microsoft]': [['']]
# }

