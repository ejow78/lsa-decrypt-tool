#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
Script de compilación y protección de código para LSA Decryption Tool.exe
Ejecutar: python build_protected_exe.py
"""

import base64
import hashlib
import marshal
import math
import os
import secrets
import shutil
import subprocess
import sys
import zlib

WORK_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_FILE = os.path.join(WORK_DIR, "acd_tool.py")
ICON_FILE = os.path.join(WORK_DIR, "lsa_icon.ico")
LOADER_FILE = os.path.join(WORK_DIR, "lsa_protected_entry.py")
EXE_NAME = "LSA Decryption Tool"


def stream_xor(data: bytes, seed: bytes) -> bytes:
    out = bytearray(len(data))
    block_idx = 0
    pos = 0
    while pos < len(data):
        digest = hashlib.sha256(seed + block_idx.to_bytes(4, "little")).digest()
        chunk = data[pos : pos + 32]
        for i, b in enumerate(chunk):
            out[pos + i] = (b ^ digest[i]) ^ ((pos + i) & 0xFF)
        pos += 32
        block_idx += 1
    return bytes(out)


def build_protected_loader() -> None:
    with open(SRC_FILE, "r", encoding="utf-8") as f:
        source_code = f.read()

    code_obj = compile(source_code, "<lsa_secure_core>", "exec", optimize=2)
    marshalled = marshal.dumps(code_obj)
    compressed = zlib.compress(marshalled, level=9)

    salt = secrets.token_bytes(32)
    pepper = secrets.token_bytes(32)
    derived_seed = hashlib.sha256(salt + b"LSA_DECRYPTION_LANCOOL" + pepper).digest()
    encrypted = stream_xor(compressed, derived_seed)

    b64_payload = base64.b85encode(encrypted).decode("ascii")
    b64_salt = base64.b85encode(salt).decode("ascii")
    b64_pepper = base64.b85encode(pepper).decode("ascii")

    loader_code = f'''# -*- coding: utf-8 -*-
import argparse
import base64
import ctypes
from ctypes import wintypes
import hashlib
import marshal
import math
import os
import re
import shutil
import struct
import sys
import tkinter as tk
import traceback
import zlib
from tkinter import filedialog, messagebox, ttk

def _0x9f1():
    if sys.gettrace() is not None:
        sys.exit(1)
    try:
        if ctypes.windll.kernel32.IsDebuggerPresent() != 0:
            sys.exit(1)
    except Exception:
        pass

def _0x4a2(_d: bytes, _s: bytes) -> bytes:
    _o = bytearray(len(_d))
    _b = 0
    _p = 0
    while _p < len(_d):
        _dg = hashlib.sha256(_s + _b.to_bytes(4, "little")).digest()
        _ch = _d[_p : _p + 32]
        for _i, _v in enumerate(_ch):
            _o[_p + _i] = (_v ^ _dg[_i]) ^ ((_p + _i) & 0xFF)
        _p += 32
        _b += 1
    return bytes(_o)

def _0x7e0():
    _0x9f1()
    _s1 = base64.b85decode({b64_salt!r})
    _s2 = base64.b85decode({b64_pepper!r})
    _pl = base64.b85decode({b64_payload!r})
    _sd = hashlib.sha256(_s1 + b"LSA_DECRYPTION_LANCOOL" + _s2).digest()
    _raw = zlib.decompress(_0x4a2(_pl, _sd))
    _co = marshal.loads(_raw)
    _g = {{"__name__": "__main__", "__file__": sys.argv[0]}}
    exec(_co, _g)

if __name__ == "__main__":
    _0x7e0()
'''
    with open(LOADER_FILE, "w", encoding="utf-8") as f:
        f.write(loader_code)


def cleanup_temp_files() -> None:
    for p in (LOADER_FILE, os.path.join(WORK_DIR, f"{EXE_NAME}.spec")):
        if os.path.isfile(p):
            try:
                os.remove(p)
            except Exception:
                pass
    build_dir = os.path.join(WORK_DIR, "build")
    if os.path.isdir(build_dir):
        shutil.rmtree(build_dir, ignore_errors=True)


def main() -> None:
    os.chdir(WORK_DIR)
    print("[1/2] Cifrando y ofuscando bytecode...")
    build_protected_loader()

    print(f"[2/2] Compilando '{EXE_NAME}.exe' con PyInstaller...")
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",
        "--noconsole",
        "--clean",
        "--name",
        EXE_NAME,
        "--icon",
        ICON_FILE,
        "--add-data",
        f"{ICON_FILE};.",
        LOADER_FILE,
    ]
    try:
        subprocess.run(cmd, check=True)
    finally:
        cleanup_temp_files()

    exe_path = os.path.join(WORK_DIR, "dist", f"{EXE_NAME}.exe")
    if os.path.isfile(exe_path):
        print(f"[OK] Ejecutable creado en: {exe_path}")


if __name__ == "__main__":
    main()
