import sys
import json
from collections import OrderedDict
from textwrap import indent
from typing import TextIO

class JsonToProtoConverter:
    def __init__(self):
        self.indent = 0
        self.data = None
        self.fproto = None
    
    def convert(self, fjson : TextIO, fproto : TextIO,
        generic_services=False,
    ):
        self.indent = 0
        self.data = json.load(fjson, object_pairs_hook=OrderedDict)
        self.fproto = fproto
        # Write syntax info
        self.write_indented_line('syntax = "proto3";\n')

        # Write package name
        pkgname, pkgdata = next(iter(self.data['nested'].items()))
        self.write_indented_line(f'package {pkgname};\n')

        # Check generic_services flag
        if generic_services:
            self.write_indented_line('option py_generic_services = true;\n')

        # Iterate over package and parse each item
        for key, item in pkgdata['nested'].items():
            self.parse_item(key, item)
        

    def write_indented_line(self, text : str):
        whitespaces = ' ' * self.indent * 2
        self.fproto.write(whitespaces + text + '\n')

    def parse_item(self, name, item):
        # Check for fields(=message)
        if 'fields' in item:
            self.write_indented_line(f'message {name} {{')
            self.indent += 1
            for msg_name, msg_item in item['fields'].items():
                rule = msg_item.get('rule')
                if rule:
                    # rule type varname = id
                    self.write_indented_line(
                        f'{rule} {msg_item["type"]} {msg_name} = {msg_item["id"]};')
                else:
                    # type varname = id
                    self.write_indented_line(
                        f'{msg_item["type"]} {msg_name} = {msg_item["id"]};')
        # Check for methods(=service)
        elif 'methods' in item:
            self.write_indented_line(f'service {name} {{')
            self.indent += 1
            for svc_name, svc_item in item['methods'].items():
                # rpc methodName (requestType) returns (responseType)
                self.write_indented_line(
                    f'rpc {svc_name} ({svc_item["requestType"]}) returns ({svc_item["responseType"]});')
        # Check for values(=enum)
        elif 'values' in item:
            self.write_indented_line(f'enum {name} {{')
            self.indent += 1
            for enum_name, enum_value in item['values'].items():
                # NAME = VALUE
                self.write_indented_line(f'{enum_name} = {enum_value};')
        else:
            # Unknown new type
            print(f'Unknwon new type "{name}" = {item}\n', file=sys.stderr)
            print('Conversion failed.\n', file=sys.stderr)

        # parse child items recursively
        if 'nested' in item:
            for child_name, child_item in item['nested'].items():
                self.parse_item(child_name, child_item)
        
        self.indent -= 1
        self.write_indented_line('}')
        if self.indent == 0:
            self.fproto.write('\n')

if __name__ == '__main__':
    with open('liqi.json', 'r') as fin, open('liqi.proto', 'w') as fout:
        converter = JsonToProtoConverter()
        converter.convert(fin, fout)
