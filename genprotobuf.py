import importlib
import os
import platform
import subprocess
from fmtfileconvert import JsonToProtoConverter

JSON_FILENAME = 'liqi.json'
PROTO_FILENAME = 'liqi.proto'
META_FILENAME = 'liqi_pb2.py'

def metafile_exists():
    dir = os.path.dirname(__file__)
    return os.path.exists(os.path.abspath(os.path.join(dir, META_FILENAME)))

def generate_metafile():
    # Generate `liqi.proto` file if not exists first
    dirname = os.path.dirname(__file__)
    liqijson = os.path.abspath(os.path.join(dirname, JSON_FILENAME))
    liqiproto = os.path.abspath(os.path.join(dirname, PROTO_FILENAME))
    if not os.path.exists(liqiproto):
        converter = JsonToProtoConverter()
        with open(liqijson, 'r') as fin, open(liqiproto, 'w') as fout:
            converter.convert(fin, fout, generic_services=True)
    # Determine the compiler
    uname, machine = platform.system(), platform.machine()
    if uname == 'Windows' and machine in ('x86_64', 'AMD64'):
        compiler = os.path.abspath(os.path.join(dirname, 'compiler', 'windows', 'x64', 'bin', 'protoc.exe'))
    elif uname == 'Linux' and machine in ('x86_64', 'x64'):
        compiler = os.path.abspath(os.path.join(dirname, 'compiler', 'linux', 'x64', 'bin', 'protoc'))
    elif uname == 'Darwin':
        compiler = os.path.abspath(os.path.join(dirname, 'compiler', 'osx', 'universal', 'bin', 'protoc'))
    else:
        raise RuntimeError('Unable to find a proper compiler for your platform, or your platform cannot be determined.')
    result = subprocess.run([compiler, f'-I={dirname}', f'--python_out={dirname}', liqiproto],
        capture_output=True,
    )
    if result.returncode != 0:
        raise RuntimeError('Compilation failed.')
    
def load_protobuf():
    if not metafile_exists():
        generate_metafile()
    return importlib.import_module(os.path.splitext(META_FILENAME)[0])
