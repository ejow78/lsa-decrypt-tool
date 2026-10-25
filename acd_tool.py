#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LSA Decryption Tool
Ante cualquier duda o error, contactar en Discord a: lancool
"""

import argparse
import ctypes
from ctypes import wintypes
import math
import os
import re
import shutil
import struct
import sys
import tkinter as tk
import traceback
from tkinter import filedialog, messagebox, ttk
from typing import Callable, Dict, List, Optional, Tuple

APP_TITLE = "LSA Decryption Tool"
DISCORD_CONTACT = "lancool"
SUPPORT_FOOTER = f"Ante cualquier duda o error, contactar en Discord a: {DISCORD_CONTACT}"

DROPPED_PLACEHOLDER = (
    "\n"
    "   Arrastra y solta aca tu archivo data.acd (o la carpeta del auto)\n"
    "   para cargarlo y desencriptarlo automaticamente.\n\n"
    "   Tambien podes usar las pestañas de arriba:\n"
    "   - Archivos y Editor: Ver y editar todos los archivos .ini / .lut / .rto\n"
    "   - Balance: Ajustar potencia, peso, RPM y sistema hibrido\n"
    "   - Sonido y Renombrar Auto: Cambiar sonido con backup y renombrar carpeta del auto"
)

WEC_ET_LUT_9000 = [
    (0, 319.999), (250, 319.999), (500, 319.999), (750, 319.999),
    (1000, 319.999), (1250, 319.999), (1500, 319.999), (1750, 319.999),
    (2000, 319.999), (2250, 319.999), (2500, 319.999), (2750, 319.999),
    (3000, 319.999), (3250, 319.999), (3500, 319.999), (3750, 319.999),
    (4000, 276.625), (4250, 260.353), (4400, 251.477), (4700, 235.426),
    (5000, 221.300), (5300, 208.774), (5600, 197.589), (5900, 187.542),
    (6200, 178.468), (6500, 170.231), (6800, 162.721), (7100, 155.845),
    (7400, 149.527), (7600, 145.592), (7900, 140.063), (8100, 136.605),
    (8300, 133.313), (8500, 130.176), (8700, 127.184), (8850, 125.028),
    (9050, 122.265), (9250, 119.622), (9400, 117.713), (9550, 115.864),
    (9750, 113.487), (10000, 110.650), (12500, 0.0),
]

WEC_ECT_LUT_9000 = [
    (0, 3.855), (250, 3.855), (500, 7.789), (750, 11.882),
    (1000, 16.214), (1250, 20.863), (1500, 25.911), (1750, 31.436),
    (2000, 37.517), (2250, 44.235), (2500, 51.668), (2750, 59.897),
    (3000, 69.000), (3250, 79.015), (3500, 89.808), (3750, 101.202),
    (4000, 113.020), (4250, 125.085), (4400, 132.370), (4700, 146.863),
    (5000, 161.000), (5300, 174.522), (5600, 187.357), (5900, 199.479),
    (6200, 210.861), (6500, 221.477), (6800, 231.302), (7100, 240.308),
    (7400, 248.471), (7600, 253.432), (7900, 260.148), (8100, 264.152),
    (8300, 267.784), (8500, 271.050), (8700, 273.958), (8850, 275.906),
    (9050, 278.199), (9250, 280.151), (9400, 281.393), (9550, 282.450),
    (9750, 283.573), (10000, 284.605), (12500, 0.0),
]

WEC_UMDREH_LUT_9000 = [
    (0, 0.5), (5000, 0.0), (5200, 0.141), (6000, 0.453),
    (7500, 0.467), (7800, 0.348), (8300, 0.166), (8600, 0.0),
    (8800, 0.0), (9100, 0.0), (10000, 0.0),
]

# Win32 Drag & Drop constants and types
WM_DROPFILES = 0x0233
WM_COPYDATA = 0x004A
WM_COPYGLOBALDATA = 0x0049
MSGFLT_ALLOW = 1
GWL_WNDPROC = -4
WNDPROC = ctypes.WINFUNCTYPE(
    ctypes.c_ssize_t, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM
)

_user32 = ctypes.windll.user32
_shell32 = ctypes.windll.shell32

_shell32.DragAcceptFiles.argtypes = [wintypes.HWND, wintypes.BOOL]
_shell32.DragQueryFileW.argtypes = [wintypes.WPARAM, wintypes.UINT, wintypes.LPWSTR, wintypes.UINT]
_shell32.DragQueryFileW.restype = wintypes.UINT
_shell32.DragFinish.argtypes = [wintypes.WPARAM]

_user32.SetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int, WNDPROC]
_user32.SetWindowLongPtrW.restype = ctypes.c_void_p
_user32.CallWindowProcW.argtypes = [
    ctypes.c_void_p,
    wintypes.HWND,
    wintypes.UINT,
    wintypes.WPARAM,
    wintypes.LPARAM,
]
_user32.CallWindowProcW.restype = ctypes.c_ssize_t
_user32.GetParent.argtypes = [wintypes.HWND]
_user32.GetParent.restype = wintypes.HWND


def resource_path(rel_path: str) -> str:
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, rel_path)


def show_error_dialog(title: str, detail: str) -> None:
    messagebox.showerror(
        title,
        f"{detail}\n\n--------------------------------------\n{SUPPORT_FOOTER}",
    )


def _s8(v: int) -> int:
    return ctypes.c_int8(v & 0xFF).value


def _u8(v: int) -> int:
    return v & 0xFF


def generate_key(folder_name: str) -> str:
    folder_name = folder_name.strip().lower()
    b = [ord(c) for c in folder_name]
    n = len(b)
    if n == 0:
        return "0-0-0-0-0-0-0-0"

    o1 = _u8(sum(b))

    o2 = 0
    for i in range(0, n - 1, 2):
        o2 = _s8(o2 * b[i] - b[i + 1])
    o2 = _u8(o2)

    o3 = 0
    for i in range(1, n - 3, 3):
        o3 = int((o3 * b[i]) / (b[i + 1] + 0x1B)) - 0x1B - b[i - 1]
    o3 = _u8(o3)

    o4 = 0x1683
    for i in range(1, n):
        o4 -= b[i]
    o4 = _u8(o4)

    o5 = 0x42
    for i in range(1, n - 4, 4):
        o5 = (b[i] + 0x0F) * o5 * (b[i - 1] + 0x0F) + 0x16
    o5 = _u8(o5)

    o6 = 0x65
    for i in range(0, n - 2, 2):
        o6 -= b[i]
    o6 = _u8(o6)

    o7 = 0xAB
    for i in range(0, n - 2, 2):
        o7 = int(o7 % b[i])
    o7 = _u8(o7)

    o8 = 0xAB
    for i in range(0, n - 1):
        o8 = int(o8 / b[i]) + b[i + 1]
    o8 = _u8(o8)

    return f"{o1}-{o2}-{o3}-{o4}-{o5}-{o6}-{o7}-{o8}"


def parse_raw_acd(acd_path: str) -> List[Tuple[str, bytes]]:
    with open(acd_path, "rb") as f:
        data = f.read()

    pos = 0
    total = len(data)
    if total >= 8:
        first_int = struct.unpack_from("<i", data, 0)[0]
        if first_int == -1111:
            pos = 8

    entries: List[Tuple[str, bytes]] = []
    while pos < total:
        if pos + 4 > total:
            break
        name_len = struct.unpack_from("<I", data, pos)[0]
        pos += 4

        if name_len == 0 or name_len > 256 or pos + name_len > total:
            if entries:
                break
            raise ValueError(f"Formato ACD invalido en offset {pos - 4}.")

        raw_name = data[pos : pos + name_len]
        if not all(32 <= c <= 126 for c in raw_name):
            if entries:
                break
            raise ValueError(f"Nombre de archivo corrupto en offset {pos - 4}.")

        name = raw_name.decode("ascii", errors="replace")
        pos += name_len

        if pos + 4 > total:
            if entries:
                break
            raise ValueError(f"Formato ACD truncado leyendo tamaño de {name}.")

        file_len = struct.unpack_from("<I", data, pos)[0]
        pos += 4
        if pos + file_len * 4 > total:
            if entries:
                avail_len = max(0, (total - pos) // 4)
                raw_bytes = data[pos : pos + avail_len * 4 : 4]
                if raw_bytes:
                    entries.append((name, raw_bytes))
                break
            raise ValueError(f"Formato ACD truncado leyendo contenido de {name}.")

        raw_bytes = data[pos : pos + file_len * 4 : 4]
        pos += file_len * 4
        entries.append((name, raw_bytes))

    return entries


def decrypt_bytes(raw_bytes: bytes, key_str: str) -> bytes:
    key = key_str.encode("ascii")
    klen = len(key)
    return bytes((b - key[i % klen]) & 0xFF for i, b in enumerate(raw_bytes))


def encrypt_bytes(plain_bytes: bytes, key_str: str) -> bytes:
    key = key_str.encode("ascii")
    klen = len(key)
    out = bytearray(len(plain_bytes) * 4)
    for i, b in enumerate(plain_bytes):
        enc_b = (b + key[i % klen]) & 0xFF
        struct.pack_into("<I", out, i * 4, enc_b)
    return bytes(out)


def is_likely_valid_text(dec: bytes) -> bool:
    if not dec:
        return True
    sample = dec[:512]
    printable = sum(1 for c in sample if c in (9, 10, 13) or 32 <= c <= 126)
    return (printable / len(sample)) >= 0.85


def auto_recover_key(entries: List[Tuple[str, bytes]]) -> Optional[str]:
    entry_dict = dict(entries)
    known_prefixes = [
        ("engine.ini", b"[HEADER]\r\nVERSION=1\r\nPOWER_CURVE="),
        ("car.ini", b"[HEADER]\r\nVERSION="),
        ("aero.ini", b"[HEADER]\r\nVERSION="),
        ("tyres.ini", b"[HEADER]\r\nVERSION="),
        ("drivetrain.ini", b"[HEADER]\r\nVERSION="),
        ("brakes.ini", b"[HEADER]\r\nVERSION="),
        ("suspensions.ini", b"[HEADER]\r\nVERSION="),
    ]

    for fname, expected in known_prefixes:
        if fname in entry_dict and len(entry_dict[fname]) >= len(expected):
            raw = entry_dict[fname][: len(expected)]
            derived = bytes((r - e) & 0xFF for r, e in zip(raw, expected)).decode("ascii", errors="ignore")
            m = re.match(r"^(\d{1,3}(?:-\d{1,3}){7})", derived)
            if m:
                cand_key = m.group(1)
                if is_likely_valid_text(decrypt_bytes(entry_dict[fname], cand_key)):
                    return cand_key

    valid_key_chars = set(b"0123456789-")
    ini_files = [raw for name, raw in entries if name.lower().endswith((".ini", ".lut", ".rto")) and len(raw) >= 64]
    if not ini_files:
        return None

    for klen in range(15, 32):
        cand = bytearray(klen)
        possible = True
        for pos_idx in range(klen):
            col_bytes = []
            for raw in ini_files[:12]:
                col_bytes.extend(raw[pos_idx::klen][:40])
            if not col_bytes:
                possible = False
                break

            best_k = None
            best_score = -1
            for k in valid_key_chars:
                score = 0
                valid_count = 0
                for b in col_bytes:
                    p = (b - k) & 0xFF
                    if p in (9, 10, 13) or 32 <= p <= 126:
                        valid_count += 1
                        if p in (10, 13, 32, 61) or 48 <= p <= 57 or 65 <= p <= 90 or 97 <= p <= 122:
                            score += 2
                        else:
                            score += 1
                if valid_count >= len(col_bytes) * 0.90 and score > best_score:
                    best_score = score
                    best_k = k
            if best_k is None:
                possible = False
                break
            cand[pos_idx] = best_k

        if possible:
            cand_str = cand.decode("ascii", errors="ignore")
            if re.fullmatch(r"\d{1,3}(?:-\d{1,3}){7}", cand_str):
                if is_likely_valid_text(decrypt_bytes(ini_files[0], cand_str)):
                    return cand_str

    return None


def resolve_car_dir(path_str: str) -> str:
    path_str = os.path.abspath(path_str)
    if os.path.isfile(path_str):
        parent = os.path.dirname(path_str)
        if os.path.basename(parent).lower() in ("data", "sfx", "ui", "extension"):
            return os.path.dirname(parent)
        return parent
    if os.path.basename(path_str).lower() in ("data", "sfx", "ui", "extension") and os.path.isdir(path_str):
        return os.path.dirname(path_str)
    return path_str


def unpack_acd(
    car_dir: str,
    custom_key: Optional[str] = None,
    backup_acd: bool = True,
) -> Tuple[int, str, str]:
    car_dir = resolve_car_dir(car_dir)
    acd_path = os.path.join(car_dir, "data.acd")
    if not os.path.isfile(acd_path):
        raise FileNotFoundError(f"No se encontro data.acd en:\n{car_dir}")

    folder_name = os.path.basename(car_dir)
    key_str = custom_key.strip() if custom_key else generate_key(folder_name)

    entries = parse_raw_acd(acd_path)
    if not entries:
        raise ValueError("El archivo data.acd esta vacio.")

    ini_entries = [raw for name, raw in entries if name.lower().endswith(".ini") and len(raw) > 0]
    if ini_entries and not is_likely_valid_text(decrypt_bytes(ini_entries[0], key_str)):
        recovered = auto_recover_key(entries)
        if recovered:
            key_str = recovered
        else:
            raise ValueError(
                "No se pudo desencriptar el archivo (el nombre de la carpeta del auto no coincide "
                "con el original o usa un cifrado distinto)."
            )

    data_dir = os.path.join(car_dir, "data")
    os.makedirs(data_dir, exist_ok=True)

    if backup_acd:
        bak_path = os.path.join(car_dir, "data.acd.bak")
        if not os.path.exists(bak_path):
            shutil.copy2(acd_path, bak_path)

    for name, raw_bytes in entries:
        dec = decrypt_bytes(raw_bytes, key_str)
        out_path = os.path.join(data_dir, name)
        with open(out_path, "wb") as out_f:
            out_f.write(dec)

    return len(entries), key_str, data_dir


def pack_acd(
    car_dir: str,
    custom_key: Optional[str] = None,
    create_backup: bool = True,
) -> Tuple[int, str, str]:
    car_dir = resolve_car_dir(car_dir)
    data_dir = os.path.join(car_dir, "data")
    if not os.path.isdir(data_dir):
        raise FileNotFoundError(f"No existe la carpeta 'data' en:\n{car_dir}")

    folder_name = os.path.basename(car_dir)
    key_str = custom_key.strip() if custom_key else generate_key(folder_name)

    files = sorted(
        f for f in os.listdir(data_dir) if os.path.isfile(os.path.join(data_dir, f))
    )
    if not files:
        raise ValueError(f"La carpeta 'data' esta vacia:\n{data_dir}")

    acd_path = os.path.join(car_dir, "data.acd")
    if create_backup and os.path.isfile(acd_path):
        bak_path = os.path.join(car_dir, "data.acd.bak")
        if not os.path.exists(bak_path):
            shutil.copy2(acd_path, bak_path)

    chunks: List[bytes] = []
    for fname in files:
        fpath = os.path.join(data_dir, fname)
        with open(fpath, "rb") as f:
            plain = f.read()
        name_bytes = fname.encode("ascii")
        enc_payload = encrypt_bytes(plain, key_str)
        header = struct.pack("<I", len(name_bytes)) + name_bytes + struct.pack("<I", len(plain))
        chunks.append(header + enc_payload)

    with open(acd_path, "wb") as out_f:
        out_f.write(b"".join(chunks))

    return len(files), key_str, acd_path


def get_ini_value(text: str, section: str, key: str) -> Optional[str]:
    in_sec = False
    sec_upper = f"[{section.upper()}]"
    key_upper = key.upper()
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith((";", "//", "#")):
            continue
        if s.startswith("[") and "]" in s:
            in_sec = s[: s.index("]") + 1].upper() == sec_upper
            continue
        if in_sec and "=" in s:
            k, v = s.split("=", 1)
            if k.strip().upper() == key_upper:
                val_part = v.split(";")[0].split("//")[0].strip()
                return val_part
    return None


def set_ini_value(text: str, section: str, key: str, new_val: str) -> str:
    lines = text.splitlines()
    in_sec = False
    sec_upper = f"[{section.upper()}]"
    key_upper = key.upper()
    replaced = False
    sec_found = False
    last_sec_line = -1

    for idx, line in enumerate(lines):
        s = line.strip()
        if s.startswith("[") and "]" in s:
            if in_sec and not replaced:
                lines.insert(last_sec_line + 1, f"{key}={new_val}")
                replaced = True
                break
            in_sec = s[: s.index("]") + 1].upper() == sec_upper
            if in_sec:
                sec_found = True
                last_sec_line = idx
            continue
        if in_sec:
            if s and not s.startswith((";", "//", "#")):
                last_sec_line = idx
            if "=" in s and not s.startswith((";", "//", "#")):
                k, v = s.split("=", 1)
                if k.strip().upper() == key_upper:
                    comment = ""
                    if ";" in v:
                        comment = " \t;" + v.split(";", 1)[1]
                    lines[idx] = f"{k.strip()}={new_val}{comment}"
                    replaced = True
                    break

    if not replaced:
        if sec_found:
            lines.insert(last_sec_line + 1, f"{key}={new_val}")
        else:
            if lines and lines[-1].strip() != "":
                lines.append("")
            lines.append(f"[{section}]")
            lines.append(f"{key}={new_val}")

    return "\r\n".join(lines) + "\r\n"


def parse_lut_file(fpath: str) -> List[Tuple[float, float]]:
    if not os.path.isfile(fpath):
        return []
    pts: List[Tuple[float, float]] = []
    with open(fpath, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            s = line.strip()
            if not s or s.startswith((";", "//", "#")):
                continue
            s = s.split(";")[0].split("//")[0].strip()
            if "|" in s:
                parts = s.split("|")
                if len(parts) >= 2:
                    try:
                        pts.append((float(parts[0].strip()), float(parts[1].strip())))
                    except ValueError:
                        pass
    return pts


def write_lut_file(fpath: str, pts: List[Tuple[float, float]], int_x: bool = True, decimals_y: int = 3) -> None:
    lines = []
    for x, y in pts:
        x_str = str(int(round(x))) if int_x else f"{x:g}"
        y_str = f"{round(y, decimals_y):g}" if decimals_y <= 3 else f"{y:.{decimals_y}f}".rstrip("0").rstrip(".")
        lines.append(f"{x_str}|{y_str}")
    with open(fpath, "w", encoding="utf-8", newline="\r\n") as f:
        f.write("\r\n".join(lines) + "\r\n")


def create_physics_backup(car_dir: str) -> str:
    car_dir = resolve_car_dir(car_dir)
    backup_dir = os.path.join(car_dir, "backup_data")
    os.makedirs(backup_dir, exist_ok=True)

    acd_path = os.path.join(car_dir, "data.acd")
    if os.path.isfile(acd_path):
        shutil.copy2(acd_path, os.path.join(backup_dir, "data.acd"))

    data_dir = os.path.join(car_dir, "data")
    if os.path.isdir(data_dir):
        b_data = os.path.join(backup_dir, "data")
        os.makedirs(b_data, exist_ok=True)
        for f in os.listdir(data_dir):
            src_f = os.path.join(data_dir, f)
            if os.path.isfile(src_f):
                shutil.copy2(src_f, os.path.join(b_data, f))

    return backup_dir


def restore_physics_backup(car_dir: str) -> bool:
    car_dir = resolve_car_dir(car_dir)
    backup_dir = os.path.join(car_dir, "backup_data")
    if not os.path.isdir(backup_dir):
        return False

    b_acd = os.path.join(backup_dir, "data.acd")
    if os.path.isfile(b_acd):
        shutil.copy2(b_acd, os.path.join(car_dir, "data.acd"))

    b_data = os.path.join(backup_dir, "data")
    if os.path.isdir(b_data):
        target_data = os.path.join(car_dir, "data")
        os.makedirs(target_data, exist_ok=True)
        for f in os.listdir(b_data):
            src_f = os.path.join(b_data, f)
            if os.path.isfile(src_f):
                shutil.copy2(src_f, os.path.join(target_data, f))

    return True


def create_sound_backup(car_dir: str) -> str:
    car_dir = resolve_car_dir(car_dir)
    target_sfx = os.path.join(car_dir, "sfx")
    if not os.path.isdir(target_sfx):
        raise FileNotFoundError(f"No existe la carpeta 'sfx' en:\n{car_dir}")

    backup_sfx = os.path.join(car_dir, "sfx_backup")
    os.makedirs(backup_sfx, exist_ok=True)
    for f in os.listdir(target_sfx):
        src_f = os.path.join(target_sfx, f)
        if os.path.isfile(src_f):
            shutil.copy2(src_f, os.path.join(backup_sfx, f))
    return backup_sfx


def swap_car_sound(target_car_dir: str, donor_path: str) -> Tuple[str, int]:
    target_car_dir = resolve_car_dir(target_car_dir)
    target_name = os.path.basename(target_car_dir)
    target_sfx = os.path.join(target_car_dir, "sfx")
    os.makedirs(target_sfx, exist_ok=True)

    donor_path = os.path.abspath(donor_path)
    if os.path.isfile(donor_path) and donor_path.lower().endswith(".bank"):
        donor_sfx = os.path.dirname(donor_path)
        donor_bank_file = donor_path
    else:
        donor_car_dir = resolve_car_dir(donor_path)
        donor_sfx = os.path.join(donor_car_dir, "sfx")
        if not os.path.isdir(donor_sfx):
            donor_sfx = donor_path
        banks = [
            os.path.join(donor_sfx, f)
            for f in os.listdir(donor_sfx)
            if f.lower().endswith(".bank") and f.lower() not in ("common.bank", "showroom.bank")
        ]
        if not banks:
            raise FileNotFoundError(f"No se encontro ningun archivo .bank de auto en:\n{donor_sfx}")
        donor_bank_file = banks[0]

    donor_guids_file = os.path.join(donor_sfx, "GUIDs.txt")
    if not os.path.isfile(donor_guids_file):
        raise FileNotFoundError(
            f"No se encontro el archivo GUIDs.txt junto al banco donante en:\n{donor_sfx}"
        )

    backup_sfx = os.path.join(target_car_dir, "sfx_backup")
    if not os.path.isdir(backup_sfx):
        create_sound_backup(target_car_dir)

    with open(donor_guids_file, "r", encoding="utf-8", errors="replace") as f:
        guids_text = f.read()

    car_names_found = re.findall(r"event:/cars/([^/\s]+)/", guids_text)
    if not car_names_found:
        donor_car_id = os.path.splitext(os.path.basename(donor_bank_file))[0]
    else:
        donor_car_id = car_names_found[0]

    new_lines = []
    replaced_count = 0
    for line in guids_text.splitlines():
        orig = line
        line = re.sub(
            r"(event:/cars/)([^/\s]+)(/)",
            lambda m: f"{m.group(1)}{target_name}{m.group(3)}",
            line,
            flags=re.IGNORECASE,
        )
        m_bank = re.search(r"(bank:/)([^\s]+)", line, flags=re.IGNORECASE)
        if m_bank and m_bank.group(2).lower() not in ("common", "showroom", "master"):
            line = f"{m_bank.group(1)}{target_name}"
        if line != orig:
            replaced_count += 1
        new_lines.append(line)

    if target_name != target_name.lower():
        for line in list(new_lines):
            if f"bank:/{target_name}" in line:
                mirror = line.replace(f"bank:/{target_name}", f"bank:/{target_name.lower()}")
                if mirror not in new_lines:
                    new_lines.append(mirror)

    target_bank_path = os.path.join(target_sfx, f"{target_name}.bank")
    shutil.copy2(donor_bank_file, target_bank_path)

    target_guids_path = os.path.join(target_sfx, "GUIDs.txt")
    with open(target_guids_path, "w", encoding="utf-8", newline="\r\n") as f:
        f.write("\r\n".join(new_lines) + "\r\n")

    return donor_car_id, replaced_count


class LSADecryptionToolGUI:
    def __init__(self, root: tk.Tk, initial_dir: Optional[str] = None) -> None:
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("1000x690")
        self.root.minsize(860, 580)

        self._wndproc_hooks: Dict[int, Tuple[object, int]] = {}
        self._apply_window_icon()

        self.current_car_dir: str = ""
        self.current_file_name: Optional[str] = None
        self.all_files: List[str] = []

        self._build_ui()
        self._setup_drag_and_drop()

        default_start = initial_dir
        if not default_start:
            if os.path.isdir(r"Z:\FH6\evo"):
                default_start = r"Z:\FH6\evo"
            else:
                default_start = os.getcwd()

        if initial_dir and (
            os.path.isfile(os.path.join(resolve_car_dir(initial_dir), "data.acd"))
            or os.path.isdir(os.path.join(resolve_car_dir(initial_dir), "data"))
        ):
            self.handle_dropped_item(initial_dir)
        else:
            self.path_var.set(default_start)
            self._show_placeholder()

    def _apply_window_icon(self) -> None:
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("LSA.Decryption.Tool.1")
        except Exception:
            pass
        try:
            ico_path = resource_path("lsa_icon.ico")
            if os.path.isfile(ico_path):
                self.root.iconbitmap(default=ico_path)
        except Exception:
            pass

    def _hook_single_hwnd(self, hwnd: int, callback: Callable[[List[str]], None]) -> None:
        if not hwnd or hwnd in self._wndproc_hooks:
            return
        try:
            if hasattr(_user32, "ChangeWindowMessageFilterEx"):
                _user32.ChangeWindowMessageFilterEx(hwnd, WM_DROPFILES, MSGFLT_ALLOW, None)
                _user32.ChangeWindowMessageFilterEx(hwnd, WM_COPYDATA, MSGFLT_ALLOW, None)
                _user32.ChangeWindowMessageFilterEx(hwnd, WM_COPYGLOBALDATA, MSGFLT_ALLOW, None)
        except Exception:
            pass

        _shell32.DragAcceptFiles(hwnd, True)
        old_proc_holder = [None]

        def _wnd_proc(h: int, msg: int, wp: int, lp: int) -> int:
            if msg == WM_DROPFILES:
                try:
                    count = _shell32.DragQueryFileW(wp, 0xFFFFFFFF, None, 0)
                    files: List[str] = []
                    for i in range(count):
                        length = _shell32.DragQueryFileW(wp, i, None, 0)
                        buf = ctypes.create_unicode_buffer(length + 1)
                        _shell32.DragQueryFileW(wp, i, buf, length + 1)
                        files.append(buf.value)
                    _shell32.DragFinish(wp)
                    if files:
                        self.root.after(10, lambda f=files[0]: callback([f]))
                except Exception:
                    pass
                return 0
            return _user32.CallWindowProcW(old_proc_holder[0], h, msg, wp, lp)

        proc_cb = WNDPROC(_wnd_proc)
        old_proc = _user32.SetWindowLongPtrW(hwnd, GWL_WNDPROC, proc_cb)
        old_proc_holder[0] = old_proc
        self._wndproc_hooks[hwnd] = (proc_cb, old_proc)

    def _setup_drag_and_drop(self) -> None:
        self.root.update_idletasks()
        top_hwnd = _user32.GetParent(self.root.winfo_id())
        if top_hwnd:
            self._hook_single_hwnd(top_hwnd, self._on_files_dropped)

        def hook_widget_tree(w: tk.Misc) -> None:
            try:
                self._hook_single_hwnd(w.winfo_id(), self._on_files_dropped)
            except Exception:
                pass
            for child in w.winfo_children():
                hook_widget_tree(child)

        hook_widget_tree(self.root)

    def _on_files_dropped(self, files: List[str]) -> None:
        if not files:
            return
        self.handle_dropped_item(files[0])

    def handle_dropped_item(self, dropped_path: str) -> None:
        dropped_path = os.path.abspath(dropped_path.strip('"'))
        if not os.path.exists(dropped_path):
            show_error_dialog("Error", f"El archivo o carpeta arrastrado no existe:\n{dropped_path}")
            return

        if os.path.isfile(dropped_path) and dropped_path.lower().endswith(".acd"):
            car_dir = os.path.dirname(dropped_path)
            try:
                count, _, _ = unpack_acd(car_dir)
                self.load_car_directory(car_dir)
                self.status_lbl.config(
                    text=f"data.acd desencriptado automaticamente ({count} archivos en data/)"
                )
                for idx, fname in enumerate(self.all_files):
                    if fname.lower() == "car.ini":
                        self.file_listbox.selection_clear(0, tk.END)
                        self.file_listbox.selection_set(idx)
                        self.file_listbox.see(idx)
                        self.on_file_selected()
                        break
            except Exception as e:
                self.load_car_directory(car_dir)
                show_error_dialog("Error al desencriptar el archivo arrastrado", str(e))
            return

        if os.path.isfile(dropped_path):
            car_dir = resolve_car_dir(dropped_path)
            fname = os.path.basename(dropped_path)
            self.load_car_directory(car_dir)
            for idx, item in enumerate(self.all_files):
                if item.lower() == fname.lower():
                    self.file_listbox.selection_clear(0, tk.END)
                    self.file_listbox.selection_set(idx)
                    self.file_listbox.see(idx)
                    self.on_file_selected()
                    break
            return

        car_dir = resolve_car_dir(dropped_path)
        acd_file = os.path.join(car_dir, "data.acd")
        data_dir = os.path.join(car_dir, "data")
        if os.path.isfile(acd_file) and not os.path.isdir(data_dir):
            try:
                count, _, _ = unpack_acd(car_dir)
                self.load_car_directory(car_dir)
                self.status_lbl.config(
                    text=f"data.acd desencriptado automaticamente ({count} archivos en data/)"
                )
                return
            except Exception as e:
                show_error_dialog("Error al desencriptar", str(e))
        self.load_car_directory(car_dir)

    def _show_placeholder(self) -> None:
        self.current_file_name = None
        self.editor_file_lbl.config(
            text="Ningun archivo seleccionado (Arrastra aca tu data.acd)"
        )
        self.text_editor.config(state=tk.NORMAL)
        self.text_editor.delete("1.0", tk.END)
        self.text_editor.insert("1.0", DROPPED_PLACEHOLDER)
        self.text_editor.config(state=tk.DISABLED)

    def _switch_tab(self, idx: int) -> None:
        self.current_tab_idx = idx
        for i, (frame, btn) in enumerate(zip(self.tab_frames, self.tab_buttons)):
            if i == idx:
                btn.config(
                    bg="#1d4ed8",
                    fg="#ffffff",
                    relief=tk.SUNKEN,
                    font=("Segoe UI", 9, "bold"),
                )
                frame.pack(fill=tk.BOTH, expand=True)
            else:
                btn.config(
                    bg="#dbeafe",
                    fg="#1e3a8a",
                    relief=tk.RAISED,
                    font=("Segoe UI", 9, "bold"),
                )
                frame.pack_forget()

    def _build_ui(self) -> None:
        style = ttk.Style()
        try:
            style.theme_use("vista")
        except Exception:
            pass

        top_frame = ttk.LabelFrame(
            self.root,
            text="Carpeta del Auto / Archivo data.acd",
            padding=10,
        )
        top_frame.pack(fill=tk.X, padx=10, pady=(10, 5))

        self.path_var = tk.StringVar()
        path_entry = ttk.Entry(top_frame, textvariable=self.path_var)
        path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        path_entry.bind("<Return>", lambda _: self.load_car_directory(self.path_var.get()))

        ttk.Button(top_frame, text="Buscar Carpeta...", command=self.browse_car_folder).pack(side=tk.LEFT, padx=4)
        ttk.Button(top_frame, text="Buscar data.acd...", command=self.browse_acd_file).pack(side=tk.LEFT, padx=4)
        ttk.Button(top_frame, text="Cargar", command=lambda: self.load_car_directory(self.path_var.get())).pack(side=tk.LEFT, padx=4)

        # Info bar
        info_frame = ttk.Frame(self.root, padding=(10, 4))
        info_frame.pack(fill=tk.X)

        ttk.Label(info_frame, text="Carpeta detectada:").pack(side=tk.LEFT)
        self.folder_lbl = ttk.Label(info_frame, text="-", font=("Segoe UI", 9, "bold"))
        self.folder_lbl.pack(side=tk.LEFT, padx=(4, 18))

        self.status_lbl = ttk.Label(
            info_frame,
            text="Arrastra un archivo data.acd a la ventana o selecciona un auto para comenzar.",
            foreground="#1d4ed8",
        )
        self.status_lbl.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Action buttons bar (sin iconos, nombres simples)
        btn_frame = ttk.Frame(self.root, padding=(10, 4))
        btn_frame.pack(fill=tk.X)

        self.unpack_btn = ttk.Button(
            btn_frame,
            text="Desencriptar data.acd",
            command=self.action_unpack,
        )
        self.unpack_btn.pack(side=tk.LEFT, padx=(0, 6))

        self.pack_btn = ttk.Button(
            btn_frame,
            text="Empaquetar data.acd",
            command=self.action_pack,
        )
        self.pack_btn.pack(side=tk.LEFT, padx=6)

        self.save_repack_btn = ttk.Button(
            btn_frame,
            text="Guardar y Re-empaquetar",
            command=self.action_save_and_repack,
        )
        self.save_repack_btn.pack(side=tk.LEFT, padx=6)

        self.backup_btn = ttk.Button(
            btn_frame,
            text="Guardar Backup",
            command=self.action_create_physics_backup,
        )
        self.backup_btn.pack(side=tk.LEFT, padx=6)

        self.open_explorer_btn = ttk.Button(
            btn_frame,
            text="Abrir Carpeta",
            command=self.action_open_explorer,
        )
        self.open_explorer_btn.pack(side=tk.RIGHT)

        # Footer (solo texto de soporte)
        footer_frame = ttk.Frame(self.root, padding=(10, 4))
        footer_frame.pack(fill=tk.X, side=tk.BOTTOM)
        ttk.Label(
            footer_frame,
            text=SUPPORT_FOOTER,
            foreground="#555555",
            font=("Segoe UI", 9),
        ).pack(side=tk.LEFT)

        # Barra de pestañas bien separadas y con alto contraste
        tab_bar = tk.Frame(self.root, padx=10, pady=6)
        tab_bar.pack(fill=tk.X)

        tab_titles = [
            "Archivos y Editor",
            "Balance",
            "Sonido y Renombrar Auto",
        ]
        self.tab_buttons: List[tk.Button] = []
        for idx, title in enumerate(tab_titles):
            b = tk.Button(
                tab_bar,
                text=title,
                padx=18,
                pady=6,
                bd=2,
                cursor="hand2",
                command=lambda i=idx: self._switch_tab(i),
            )
            b.pack(side=tk.LEFT, padx=(0, 10))
            self.tab_buttons.append(b)

        # Contenedor principal de pestañas con borde visible
        self.tab_container = tk.Frame(
            self.root,
            bd=1,
            relief=tk.SOLID,
            padx=8,
            pady=8,
        )
        self.tab_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 4))

        self.tab_files = ttk.Frame(self.tab_container)
        self.tab_bop_hybrid = ttk.Frame(self.tab_container)
        self.tab_sound_rename = ttk.Frame(self.tab_container)
        self.tab_frames = [self.tab_files, self.tab_bop_hybrid, self.tab_sound_rename]

        self._build_tab_files()
        self._build_tab_bop_hybrid()
        self._build_tab_sound_rename()

        self.current_tab_idx = 0
        self._switch_tab(0)

    def _build_tab_files(self) -> None:
        paned = ttk.PanedWindow(self.tab_files, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        left_frame = ttk.LabelFrame(paned, text="Archivos en data/", padding=6)
        paned.add(left_frame, weight=1)

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._refresh_file_list())
        search_entry = ttk.Entry(left_frame, textvariable=self.search_var)
        search_entry.pack(fill=tk.X, pady=(0, 6))

        list_scroll = ttk.Scrollbar(left_frame, orient=tk.VERTICAL)
        self.file_listbox = tk.Listbox(
            left_frame,
            yscrollcommand=list_scroll.set,
            font=("Consolas", 10),
            exportselection=False,
        )
        list_scroll.config(command=self.file_listbox.yview)
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        list_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_listbox.bind("<<ListboxSelect>>", self.on_file_selected)

        right_frame = ttk.LabelFrame(paned, text="Editor Rapido (.ini / .lut / .rto)", padding=6)
        paned.add(right_frame, weight=3)

        editor_top = ttk.Frame(right_frame)
        editor_top.pack(fill=tk.X, pady=(0, 4))
        self.editor_file_lbl = ttk.Label(
            editor_top,
            text="Ningun archivo seleccionado (Arrastra aca tu data.acd)",
            font=("Segoe UI", 9, "bold"),
        )
        self.editor_file_lbl.pack(side=tk.LEFT)

        ttk.Button(
            editor_top,
            text="Guardar en data/",
            command=self.save_current_file_only,
        ).pack(side=tk.RIGHT)

        text_scroll = ttk.Scrollbar(right_frame, orient=tk.VERTICAL)
        self.text_editor = tk.Text(
            right_frame,
            yscrollcommand=text_scroll.set,
            font=("Consolas", 10),
            undo=True,
            wrap=tk.NONE,
        )
        text_scroll.config(command=self.text_editor.yview)
        self.text_editor.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        text_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    def _build_tab_bop_hybrid(self) -> None:
        # Barra superior de Backup dentro de la pestaña Balance
        bop_backup_bar = ttk.LabelFrame(
            self.tab_bop_hybrid,
            text="Respaldo de Seguridad (Fisicas y data.acd)",
            padding=8,
        )
        bop_backup_bar.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(
            bop_backup_bar,
            text="Antes de modificar el balance o el sistema hibrido podes guardar una copia completa:",
        ).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(
            bop_backup_bar,
            text="Guardar Backup de Fisicas",
            command=self.action_create_physics_backup,
        ).pack(side=tk.LEFT, padx=4)

        ttk.Button(
            bop_backup_bar,
            text="Restaurar Backup de Fisicas",
            command=self.action_restore_physics_backup,
        ).pack(side=tk.LEFT, padx=4)

        columns_frame = ttk.Frame(self.tab_bop_hybrid)
        columns_frame.pack(fill=tk.BOTH, expand=True)

        # Columna izquierda: Motor, Potencia y Peso (BoP)
        left_col = ttk.LabelFrame(
            columns_frame,
            text="Balance de Motor y Peso (Potencia, Torque, Peso y RPM)",
            padding=12,
        )
        left_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 6))

        self.bop_summary_lbl = ttk.Label(
            left_col,
            text="Carga o desencripta un auto para ver sus datos de motor y peso.",
            foreground="#1d4ed8",
            font=("Segoe UI", 9, "bold"),
            wraplength=420,
        )
        self.bop_summary_lbl.pack(anchor=tk.W, pady=(0, 10))

        form = ttk.Frame(left_col)
        form.pack(fill=tk.X)

        self.bop_mass_var = tk.StringVar()
        self.bop_hp_var = tk.StringVar()
        self.bop_rpm_var = tk.StringVar()
        self.bop_boost_var = tk.StringVar()
        self.bop_scale_gears_var = tk.BooleanVar(value=True)

        rows = [
            ("Peso Total (kg) [car.ini TOTALMASS]:", self.bop_mass_var),
            ("Potencia Max. Motor con Turbo (CV):", self.bop_hp_var),
            ("Limitador de RPM [engine.ini LIMITER]:", self.bop_rpm_var),
            ("Presion Max. Turbo (bar) [MAX_BOOST]:", self.bop_boost_var),
        ]
        for idx, (label_txt, var) in enumerate(rows):
            ttk.Label(form, text=label_txt).grid(row=idx, column=0, sticky=tk.W, pady=5, padx=(0, 8))
            ttk.Entry(form, textvariable=var, width=16).grid(row=idx, column=1, sticky=tk.W, pady=5)

        ttk.Checkbutton(
            left_col,
            text="Si cambio las RPM, reescalar curvas y relacion final (mantiene sonido y LEDs)",
            variable=self.bop_scale_gears_var,
        ).pack(anchor=tk.W, pady=(8, 10))

        btn_row = ttk.Frame(left_col)
        btn_row.pack(fill=tk.X, pady=(6, 0))
        ttk.Button(
            btn_row,
            text="Aplicar Balance y Re-empaquetar",
            command=self.action_apply_bop,
        ).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(
            btn_row,
            text="Recargar Valores",
            command=self._load_bop_and_hybrid_fields,
        ).pack(side=tk.LEFT)

        # Columna derecha: Sistema Híbrido (Hypercar LMH / LMDh)
        right_col = ttk.LabelFrame(
            columns_frame,
            text="Sistema Hibrido / ERS (Hypercars LMH / LMDh)",
            padding=12,
        )
        right_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(6, 0))

        self.hybrid_status_lbl = ttk.Label(
            right_col,
            text="Sin datos hibridos cargados.",
            foreground="#047857",
            font=("Segoe UI", 9, "bold"),
            wraplength=420,
        )
        self.hybrid_status_lbl.pack(anchor=tk.W, pady=(0, 10))

        hform = ttk.Frame(right_col)
        hform.pack(fill=tk.X)

        self.hyb_mode_name_var = tk.StringVar()
        self.hyb_default_idx_var = tk.StringVar()
        self.hyb_peak_torque_var = tk.StringVar()
        self.hyb_charge_k_var = tk.StringVar()
        self.hyb_discharge_var = tk.StringVar()
        self.hyb_max_kj_var = tk.StringVar()
        self.hyb_min_kmh_var = tk.StringVar()
        self.hyb_max_kmh_var = tk.StringVar()

        hrows = [
            ("Nombre del Modo Activo (ej. MEDIUM):", self.hyb_mode_name_var),
            ("Indice Modo por Defecto [DEFAULT_CONTROLLER]:", self.hyb_default_idx_var),
            ("Torque Electrico Max. (Nm) [et.lut / kers]:", self.hyb_peak_torque_var),
            ("Recarga en Frenada [CHARGE_K]:", self.hyb_charge_k_var),
            ("Tiempo Descarga [DISCHARGE_TIME]:", self.hyb_discharge_var),
            ("Energia Max. por Vuelta [MAX_KJ_PER_LAP]:", self.hyb_max_kj_var),
            ("Velocidad Activacion Hibrido (km/h):", self.hyb_min_kmh_var),
            ("Velocidad Corte Hibrido (km/h):", self.hyb_max_kmh_var),
        ]
        for idx, (label_txt, var) in enumerate(hrows):
            ttk.Label(hform, text=label_txt).grid(row=idx, column=0, sticky=tk.W, pady=3, padx=(0, 8))
            ttk.Entry(hform, textvariable=var, width=16).grid(row=idx, column=1, sticky=tk.W, pady=3)

        hbtn_row = ttk.Frame(right_col)
        hbtn_row.pack(fill=tk.X, pady=(10, 4))
        ttk.Button(
            hbtn_row,
            text="Guardar Hibrido y Re-empaquetar",
            command=self.action_apply_hybrid,
        ).pack(side=tk.LEFT, padx=(0, 6))

        ttk.Button(
            right_col,
            text="Instalar Hibrido Hypercar WEC (Modo MEDIUM)",
            command=self.action_install_wec_hybrid_preset,
        ).pack(fill=tk.X, pady=(6, 0))

    def _build_tab_sound_rename(self) -> None:
        # Panel Izquierdo: Cambiador de Sonido en 1 Clic (Sound Swapper)
        sound_frame = ttk.LabelFrame(
            self.tab_sound_rename,
            text="Cambiar Sonido del Auto (Sound Swapper)",
            padding=12,
        )
        sound_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 6))

        ttk.Label(
            sound_frame,
            text=(
                "Copia el banco de sonido (.bank) de otro auto hacia el auto actual y adapta\n"
                "automaticamente todas las rutas internas de GUIDs.txt para que funcione directo."
            ),
            foreground="#444444",
        ).pack(anchor=tk.W, pady=(0, 12))

        self.sound_current_lbl = ttk.Label(
            sound_frame,
            text="Auto destino: Ninguno seleccionado",
            font=("Segoe UI", 9, "bold"),
        )
        self.sound_current_lbl.pack(anchor=tk.W, pady=(0, 8))

        ttk.Label(sound_frame, text="Carpeta del Auto Donante (o su archivo .bank):").pack(anchor=tk.W)
        donor_row = ttk.Frame(sound_frame)
        donor_row.pack(fill=tk.X, pady=(4, 12))

        self.donor_sound_var = tk.StringVar()
        ttk.Entry(donor_row, textvariable=self.donor_sound_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
        ttk.Button(donor_row, text="Buscar Auto...", command=self.browse_donor_sound_folder).pack(side=tk.LEFT, padx=2)
        ttk.Button(donor_row, text="Buscar .bank...", command=self.browse_donor_bank_file).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            sound_frame,
            text="Guardar Backup del Sonido Actual",
            command=self.action_create_sound_backup,
        ).pack(fill=tk.X, pady=(2, 6))

        ttk.Button(
            sound_frame,
            text="Aplicar Sonido del Donante al Auto Actual",
            command=self.action_apply_sound_swap,
        ).pack(fill=tk.X, pady=(2, 6))

        ttk.Button(
            sound_frame,
            text="Restaurar Sonido Original (desde sfx_backup)",
            command=self.action_restore_sound_backup,
        ).pack(fill=tk.X, pady=(2, 0))

        # Panel Derecho: Renombrador Seguro de Carpeta de Auto
        rename_frame = ttk.LabelFrame(
            self.tab_sound_rename,
            text="Renombrar Carpeta de Auto",
            padding=12,
        )
        rename_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(6, 0))

        ttk.Label(
            rename_frame,
            text=(
                "Si renombras la carpeta de un auto a mano en Windows, el data.acd y el sonido\n"
                "dejan de funcionar porque la clave depende del nombre de la carpeta.\n\n"
                "Esta herramienta guarda un backup, renombra la carpeta, adapta sfx/*.bank + GUIDs.txt\n"
                "y vuelve a cifrar data.acd con la nueva clave automaticamente."
            ),
            foreground="#444444",
        ).pack(anchor=tk.W, pady=(0, 12))

        self.rename_current_lbl = ttk.Label(
            rename_frame,
            text="Nombre actual: -",
            font=("Segoe UI", 9, "bold"),
        )
        self.rename_current_lbl.pack(anchor=tk.W, pady=(0, 8))

        ttk.Label(rename_frame, text="Nuevo nombre para la carpeta del auto (ej. lsa_genesis_lmh):").pack(anchor=tk.W)
        self.new_folder_name_var = tk.StringVar()
        ttk.Entry(rename_frame, textvariable=self.new_folder_name_var).pack(fill=tk.X, pady=(4, 14))

        ttk.Button(
            rename_frame,
            text="Guardar Backup Completo Antes de Renombrar",
            command=self.action_create_physics_backup,
        ).pack(fill=tk.X, pady=(2, 6))

        ttk.Button(
            rename_frame,
            text="Renombrar Auto y Re-empaquetar data.acd",
            command=self.action_safe_rename_car,
        ).pack(fill=tk.X, pady=(2, 0))

    # ==========================================================================
    # LÓGICA DE BACKUPS, BOP Y SISTEMA HÍBRIDO
    # ==========================================================================

    def action_create_physics_backup(self) -> None:
        if not self.current_car_dir:
            messagebox.showinfo("Aviso", "Primero selecciona o arrastra un auto.")
            return
        try:
            bdir = create_physics_backup(self.current_car_dir)
            self.status_lbl.config(text="Backup de fisicas guardado en backup_data/")
            messagebox.showinfo(
                "Backup Guardado",
                f"Se guardo una copia de seguridad de data.acd y de la carpeta data/ en:\n{bdir}",
            )
        except Exception as e:
            show_error_dialog("Error al crear backup", str(e))

    def action_restore_physics_backup(self) -> None:
        if not self.current_car_dir:
            messagebox.showinfo("Aviso", "Primero selecciona o arrastra un auto.")
            return
        try:
            ok = restore_physics_backup(self.current_car_dir)
            if not ok:
                messagebox.showinfo("Aviso", "No existe la carpeta 'backup_data/' en este auto todavía.")
                return
            self.load_car_directory(self.current_car_dir)
            self.status_lbl.config(text="Backup de fisicas restaurado desde backup_data/")
            messagebox.showinfo("Backup Restaurado", "Se restauraron data.acd y la carpeta data/ desde backup_data/.")
        except Exception as e:
            show_error_dialog("Error al restaurar backup", str(e))

    def action_create_sound_backup(self) -> None:
        if not self.current_car_dir:
            messagebox.showinfo("Aviso", "Primero selecciona o arrastra un auto.")
            return
        try:
            bdir = create_sound_backup(self.current_car_dir)
            self.status_lbl.config(text="Backup de sonido guardado en sfx_backup/")
            messagebox.showinfo(
                "Backup de Sonido Guardado",
                f"Se guardo una copia completa del sonido original en:\n{bdir}",
            )
        except Exception as e:
            show_error_dialog("Error al guardar backup de sonido", str(e))

    def _find_power_lut_name(self, data_dir: str) -> str:
        eng_path = os.path.join(data_dir, "engine.ini")
        if os.path.isfile(eng_path):
            with open(eng_path, "r", encoding="utf-8", errors="replace") as f:
                val = get_ini_value(f.read(), "HEADER", "POWER_CURVE")
                if val and os.path.isfile(os.path.join(data_dir, val)):
                    return val
        for cand in ("torque.lut", "force.lut", "power.lut"):
            if os.path.isfile(os.path.join(data_dir, cand)):
                return cand
        return "torque.lut"

    def _load_bop_and_hybrid_fields(self) -> None:
        if not self.current_car_dir:
            return
        data_dir = os.path.join(self.current_car_dir, "data")
        if not os.path.isdir(data_dir):
            self.bop_summary_lbl.config(
                text="Desencripta primero el data.acd (o arrastralo a la ventana) para editar Balance e Hibrido."
            )
            self.hybrid_status_lbl.config(text="Desencripta primero el data.acd para ver el sistema hibrido.")
            return

        car_ini = os.path.join(data_dir, "car.ini")
        mass_str = "1100"
        if os.path.isfile(car_ini):
            with open(car_ini, "r", encoding="utf-8", errors="replace") as f:
                m = get_ini_value(f.read(), "BASIC", "TOTALMASS")
                if m:
                    mass_str = m
        self.bop_mass_var.set(mass_str)

        eng_ini = os.path.join(data_dir, "engine.ini")
        limiter_str = "8000"
        boost_val = 0.0
        has_turbo = False
        if os.path.isfile(eng_ini):
            with open(eng_ini, "r", encoding="utf-8", errors="replace") as f:
                etext = f.read()
            lim = get_ini_value(etext, "ENGINE_DATA", "LIMITER")
            if lim:
                limiter_str = lim
            mb = get_ini_value(etext, "TURBO_0", "MAX_BOOST")
            if mb is not None:
                has_turbo = True
                try:
                    boost_val = float(mb)
                except ValueError:
                    boost_val = 0.0

        self.bop_rpm_var.set(limiter_str)
        self.bop_boost_var.set(f"{boost_val:g}" if has_turbo else "0")

        lut_name = self._find_power_lut_name(data_dir)
        pts = parse_lut_file(os.path.join(data_dir, lut_name))
        mult = 1.0 + boost_val
        max_nm = 0.0
        max_hp = 0.0
        peak_rpm = 0
        for rpm, t in pts:
            eff_t = t * mult
            hp = (eff_t * rpm) / 7127.0
            if eff_t > max_nm:
                max_nm = eff_t
            if hp > max_hp:
                max_hp = hp
                peak_rpm = int(round(rpm))

        self.bop_hp_var.set(f"{max_hp:.1f}" if max_hp > 0 else "")
        self.bop_summary_lbl.config(
            text=(
                f"Curva: {lut_name}  |  Torque Max (c/turbo): {max_nm:.1f} Nm  |  "
                f"Potencia Max: {max_hp:.1f} CV ({max_hp * 0.7355:.1f} kW) @ {peak_rpm} RPM"
            )
        )

        ers_ini = os.path.join(data_dir, "ers.ini")
        if not os.path.isfile(ers_ini):
            self.hybrid_status_lbl.config(
                text="Este auto no tiene ers.ini actualmente. Podes instalarle el Hibrido Hypercar WEC con el boton de abajo."
            )
            self.hyb_mode_name_var.set("MEDIUM")
            self.hyb_default_idx_var.set("0")
            self.hyb_peak_torque_var.set("320")
            self.hyb_charge_k_var.set("0.000017")
            self.hyb_discharge_var.set("150000")
            self.hyb_max_kj_var.set("200000")
            self.hyb_min_kmh_var.set("190")
            self.hyb_max_kmh_var.set("325")
            return

        with open(ers_ini, "r", encoding="utf-8", errors="replace") as f:
            erstext = f.read()

        def_idx = get_ini_value(erstext, "KINETIC", "DEFAULT_CONTROLLER") or "0"
        t_curve_name = get_ini_value(erstext, "KINETIC", "TORQUE_CURVE") or "et.lut"
        charge_k = get_ini_value(erstext, "KINETIC", "CHARGE_K") or "0.000017"
        dis_time = get_ini_value(erstext, "KINETIC", "DISCHARGE_TIME") or "150000"
        max_kj = get_ini_value(erstext, "KINETIC", "MAX_KJ_PER_LAP") or "200000"

        self.hyb_default_idx_var.set(def_idx)
        self.hyb_charge_k_var.set(charge_k)
        self.hyb_discharge_var.set(dis_time)
        self.hyb_max_kj_var.set(max_kj)

        ctrl_file = os.path.join(data_dir, f"ctrl_ers_{def_idx}.ini")
        if not os.path.isfile(ctrl_file):
            ctrl_file = os.path.join(data_dir, "ctrl_ers_0.ini")

        mode_name = "MEDIUM"
        speed_lut_name = None
        if os.path.isfile(ctrl_file):
            with open(ctrl_file, "r", encoding="utf-8", errors="replace") as f:
                ctext = f.read()
            mode_name = get_ini_value(ctext, "HEADER", "NAME") or "MEDIUM"
            for sec_i in range(6):
                inp = get_ini_value(ctext, f"CONTROLLER_{sec_i}", "INPUT")
                if inp and inp.upper() == "SPEED_KMH":
                    speed_lut_name = get_ini_value(ctext, f"CONTROLLER_{sec_i}", "LUT")
                    break

        self.hyb_mode_name_var.set(mode_name)

        e_pts = parse_lut_file(os.path.join(data_dir, t_curve_name))
        peak_et = max((y for _, y in e_pts), default=320.0)
        self.hyb_peak_torque_var.set(f"{peak_et:.1f}")

        min_kmh_str = "190"
        max_kmh_str = "325"
        if speed_lut_name and os.path.isfile(os.path.join(data_dir, speed_lut_name)):
            s_pts = parse_lut_file(os.path.join(data_dir, speed_lut_name))
            high_pts = [x for x, y in s_pts if x >= 80 and y > 0.05]
            if high_pts:
                min_kmh_str = str(int(round(min(high_pts))))
            zero_end = [x for x, y in s_pts if x > 200 and y == 0]
            if zero_end:
                max_kmh_str = str(int(round(max(zero_end))))
        self.hyb_min_kmh_var.set(min_kmh_str)
        self.hyb_max_kmh_var.set(max_kmh_str)

        ctrl_files = sorted(f for f in os.listdir(data_dir) if re.match(r"^ctrl_ers_\d+\.ini$", f.lower()))
        self.hybrid_status_lbl.config(
            text=(
                f"Sistema Hibrido detectado ({len(ctrl_files)} perfil/es)  |  "
                f"Curva: {t_curve_name} (Pico: {peak_et:.0f} Nm)  |  Modo activo: {mode_name}"
            )
        )

    def action_apply_bop(self) -> None:
        if not self.current_car_dir:
            messagebox.showinfo("Aviso", "Primero carga o arrastra un auto.")
            return
        data_dir = os.path.join(self.current_car_dir, "data")
        if not os.path.isdir(data_dir):
            self.action_unpack()
            if not os.path.isdir(data_dir):
                return

        try:
            if not os.path.isdir(os.path.join(self.current_car_dir, "backup_data")):
                create_physics_backup(self.current_car_dir)

            new_mass = int(round(float(self.bop_mass_var.get().strip())))
            target_hp = float(self.bop_hp_var.get().strip())
            new_rpm = int(round(float(self.bop_rpm_var.get().strip())))
            new_boost = float(self.bop_boost_var.get().strip())

            car_ini = os.path.join(data_dir, "car.ini")
            if os.path.isfile(car_ini):
                with open(car_ini, "r", encoding="utf-8", errors="replace") as f:
                    ctext = f.read()
                ctext = set_ini_value(ctext, "BASIC", "TOTALMASS", str(new_mass))
                with open(car_ini, "w", encoding="utf-8", newline="\r\n") as f:
                    f.write(ctext)

            eng_ini = os.path.join(data_dir, "engine.ini")
            old_rpm = new_rpm
            if os.path.isfile(eng_ini):
                with open(eng_ini, "r", encoding="utf-8", errors="replace") as f:
                    etext = f.read()
                old_lim_str = get_ini_value(etext, "ENGINE_DATA", "LIMITER")
                if old_lim_str:
                    try:
                        old_rpm = int(round(float(old_lim_str)))
                    except ValueError:
                        old_rpm = new_rpm
                etext = set_ini_value(etext, "ENGINE_DATA", "LIMITER", str(new_rpm))
                if get_ini_value(etext, "TURBO_0", "MAX_BOOST") is not None:
                    etext = set_ini_value(etext, "TURBO_0", "MAX_BOOST", f"{new_boost:g}")
                    etext = set_ini_value(etext, "TURBO_0", "WASTEGATE", f"{new_boost:g}")
                    etext = set_ini_value(etext, "TURBO_0", "DISPLAY_MAX_BOOST", f"{new_boost:g}")
                with open(eng_ini, "w", encoding="utf-8", newline="\r\n") as f:
                    f.write(etext)

            rpm_ratio = (new_rpm / old_rpm) if (old_rpm > 0 and self.bop_scale_gears_var.get()) else 1.0

            lut_name = self._find_power_lut_name(data_dir)
            lut_path = os.path.join(data_dir, lut_name)
            pts = parse_lut_file(lut_path)
            if pts:
                scaled_rpm_pts = [(rpm * rpm_ratio, t) for rpm, t in pts]
                mult = 1.0 + max(0.0, new_boost)
                current_max_hp = max(((t * mult * r) / 7127.0 for r, t in scaled_rpm_pts), default=0.0)
                hp_scale = (target_hp / current_max_hp) if (current_max_hp > 0 and target_hp > 0) else 1.0

                final_pts = [(r, t * hp_scale) for r, t in scaled_rpm_pts]
                write_lut_file(lut_path, final_pts, int_x=True, decimals_y=3)
                for mirror_lut in ("torque.lut", "force.lut"):
                    mp = os.path.join(data_dir, mirror_lut)
                    if os.path.isfile(mp) and os.path.abspath(mp) != os.path.abspath(lut_path):
                        write_lut_file(mp, final_pts, int_x=True, decimals_y=3)

            if abs(rpm_ratio - 1.0) > 0.001:
                for h_lut in ("et.lut", "ect.lut", "kers_torque.lut"):
                    hp_path = os.path.join(data_dir, h_lut)
                    if os.path.isfile(hp_path):
                        h_pts = parse_lut_file(hp_path)
                        if h_pts:
                            write_lut_file(
                                hp_path,
                                [(r * rpm_ratio, t / rpm_ratio) for r, t in h_pts],
                                int_x=True,
                                decimals_y=4,
                            )
                umd_path = os.path.join(data_dir, "umdreh.lut")
                if os.path.isfile(umd_path):
                    u_pts = parse_lut_file(umd_path)
                    if u_pts:
                        write_lut_file(umd_path, [(r * rpm_ratio, m) for r, m in u_pts], int_x=True, decimals_y=4)

                drv_path = os.path.join(data_dir, "drivetrain.ini")
                if os.path.isfile(drv_path):
                    with open(drv_path, "r", encoding="utf-8", errors="replace") as f:
                        dtext = f.read()
                    f_str = get_ini_value(dtext, "GEARS", "FINAL")
                    if f_str:
                        try:
                            new_final = float(f_str) * rpm_ratio
                            dtext = set_ini_value(dtext, "GEARS", "FINAL", f"{new_final:.3f}")
                            with open(drv_path, "w", encoding="utf-8", newline="\r\n") as f:
                                f.write(dtext)
                        except ValueError:
                            pass

            count, _, acd_path = pack_acd(self.current_car_dir)
            self._load_bop_and_hybrid_fields()
            self.status_lbl.config(text=f"Balance aplicado y {count} archivos re-empaquetados en data.acd")
            messagebox.showinfo(
                "Balance Aplicado",
                f"Se actualizaron Peso ({new_mass} kg), Potencia ({target_hp:.1f} CV), "
                f"RPM ({new_rpm}) y Turbo ({new_boost:g} bar), y se re-empaqueto:\n{acd_path}",
            )
        except Exception as e:
            show_error_dialog("Error al aplicar Balance", str(e))

    def action_apply_hybrid(self) -> None:
        if not self.current_car_dir:
            messagebox.showinfo("Aviso", "Primero carga o arrastra un auto.")
            return
        data_dir = os.path.join(self.current_car_dir, "data")
        ers_ini = os.path.join(data_dir, "ers.ini")
        if not os.path.isfile(ers_ini):
            self.action_install_wec_hybrid_preset()
            return

        try:
            if not os.path.isdir(os.path.join(self.current_car_dir, "backup_data")):
                create_physics_backup(self.current_car_dir)

            mode_name = self.hyb_mode_name_var.get().strip() or "MEDIUM"
            def_idx = self.hyb_default_idx_var.get().strip() or "0"
            target_peak_et = float(self.hyb_peak_torque_var.get().strip())
            charge_k = self.hyb_charge_k_var.get().strip()
            dis_time = self.hyb_discharge_var.get().strip()
            max_kj = self.hyb_max_kj_var.get().strip()
            min_kmh = int(round(float(self.hyb_min_kmh_var.get().strip())))
            max_kmh = int(round(float(self.hyb_max_kmh_var.get().strip())))

            with open(ers_ini, "r", encoding="utf-8", errors="replace") as f:
                erstext = f.read()

            t_curve_name = get_ini_value(erstext, "KINETIC", "TORQUE_CURVE") or "et.lut"
            erstext = set_ini_value(erstext, "KINETIC", "DEFAULT_CONTROLLER", def_idx)
            erstext = set_ini_value(erstext, "KINETIC", "CHARGE_K", charge_k)
            erstext = set_ini_value(erstext, "KINETIC", "DISCHARGE_TIME", dis_time)
            erstext = set_ini_value(erstext, "KINETIC", "MAX_KJ_PER_LAP", max_kj)

            with open(ers_ini, "w", encoding="utf-8", newline="\r\n") as f:
                f.write(erstext)

            t_curve_path = os.path.join(data_dir, t_curve_name)
            e_pts = parse_lut_file(t_curve_path)
            if e_pts:
                curr_peak = max((y for _, y in e_pts), default=0.0)
                if curr_peak > 0 and target_peak_et >= 0:
                    scale = target_peak_et / curr_peak
                    write_lut_file(t_curve_path, [(x, y * scale) for x, y in e_pts], int_x=True, decimals_y=3)

            ctrl_file = os.path.join(data_dir, f"ctrl_ers_{def_idx}.ini")
            if os.path.isfile(ctrl_file):
                with open(ctrl_file, "r", encoding="utf-8", errors="replace") as f:
                    ctext = f.read()
                ctext = set_ini_value(ctext, "HEADER", "NAME", mode_name)
                with open(ctrl_file, "w", encoding="utf-8", newline="\r\n") as f:
                    f.write(ctext)

                for sec_i in range(6):
                    inp = get_ini_value(ctext, f"CONTROLLER_{sec_i}", "INPUT")
                    if inp and inp.upper() == "SPEED_KMH":
                        slut = get_ini_value(ctext, f"CONTROLLER_{sec_i}", "LUT")
                        if slut:
                            slut_path = os.path.join(data_dir, slut)
                            new_speed_pts = [
                                (0, 1),
                                (50, 1),
                                (51, 0),
                                (max(52, min_kmh - 1), 0),
                                (min_kmh, 1),
                                (max(min_kmh + 1, max_kmh - 5), 0.8),
                                (max_kmh, 0),
                            ]
                            write_lut_file(slut_path, new_speed_pts, int_x=True, decimals_y=2)
                        break

            count, _, acd_path = pack_acd(self.current_car_dir)
            self._load_bop_and_hybrid_fields()
            self.status_lbl.config(text=f"Sistema Hibrido actualizado y empaquetado en data.acd ({count} archivos)")
            messagebox.showinfo(
                "Sistema Hibrido Actualizado",
                f"Se guardaron los parametros hibridos (Modo {mode_name}, {target_peak_et:.0f} Nm, "
                f"{min_kmh}-{max_kmh} km/h) y se re-empaqueto:\n{acd_path}",
            )
        except Exception as e:
            show_error_dialog("Error al guardar Sistema Hibrido", str(e))

    def action_install_wec_hybrid_preset(self) -> None:
        if not self.current_car_dir:
            messagebox.showinfo("Aviso", "Primero carga o arrastra un auto.")
            return
        data_dir = os.path.join(self.current_car_dir, "data")
        if not os.path.isdir(data_dir):
            self.action_unpack()
            if not os.path.isdir(data_dir):
                return

        try:
            if not os.path.isdir(os.path.join(self.current_car_dir, "backup_data")):
                create_physics_backup(self.current_car_dir)

            eng_ini = os.path.join(data_dir, "engine.ini")
            car_limiter = 8100.0
            if os.path.isfile(eng_ini):
                with open(eng_ini, "r", encoding="utf-8", errors="replace") as f:
                    lim = get_ini_value(f.read(), "ENGINE_DATA", "LIMITER")
                    if lim:
                        try:
                            car_limiter = float(lim)
                        except ValueError:
                            pass

            scale = 9000.0 / car_limiter if car_limiter > 0 else 1.0

            for fname in os.listdir(data_dir):
                if re.match(r"^ctrl_ers_[1-9]\d*\.ini$", fname.lower()):
                    os.remove(os.path.join(data_dir, fname))

            ers_content = (
                "[HEADER]\r\n"
                "VERSION=1\r\n"
                "[KINETIC]\r\n"
                "CHARGE_K=0.000017\r\n"
                "TORQUE_CURVE=et.lut\r\n"
                "COAST_CURVE=ect.lut\r\n"
                "DISCHARGE_TIME=150000\r\n"
                "HAS_BUTTON_OVERRIDE=0\r\n"
                "MAX_KJ_PER_LAP=200000\r\n"
                "DEFAULT_CONTROLLER=0\r\n"
                "BRAKE_REAR_CORRECTION=70\r\n\r\n"
                "[HEAT]\r\n"
                "CHARGE_K=0\r\n"
                "TORQUE_PERC=0\r\n\r\n"
                "[COCKPIT_CONTROLS]\r\n"
                "RECOVERY=0\r\n"
                "DELIVERY_PROFILE=0\r\n"
                "MGU_H_MODE=0\r\n"
            )
            with open(os.path.join(data_dir, "ers.ini"), "w", encoding="utf-8", newline="") as f:
                f.write(ers_content)

            ctrl_content = (
                "[HEADER]\r\n"
                "NAME=MEDIUM\r\n"
                "[CONTROLLER_0]\r\n"
                "COMBINATOR=ADD\r\n"
                "INPUT=GAS\r\n"
                "LUT=beschl.lut\r\n"
                "FILTER=0.9\r\n"
                "UP_LIMIT=1\r\n"
                "DOWN_LIMIT=0\r\n"
                "[CONTROLLER_1]\r\n"
                "COMBINATOR=MULT\r\n"
                "INPUT=SPEED_KMH\r\n"
                "LUT=geschw.lut\r\n"
                "FILTER=0.95\r\n"
                "UP_LIMIT=1\r\n"
                "DOWN_LIMIT=-1\r\n"
                "[CONTROLLER_2]\r\n"
                "COMBINATOR=MULT\r\n"
                "INPUT=RPMS\r\n"
                "LUT=umdreh.lut\r\n"
                "FILTER=0.98\r\n"
                "UP_LIMIT=1\r\n"
                "DOWN_LIMIT=0\r\n"
            )
            with open(os.path.join(data_dir, "ctrl_ers_0.ini"), "w", encoding="utf-8", newline="") as f:
                f.write(ctrl_content)

            write_lut_file(
                os.path.join(data_dir, "et.lut"),
                [(r / scale, t * scale) for r, t in WEC_ET_LUT_9000],
                int_x=True,
                decimals_y=3,
            )
            write_lut_file(
                os.path.join(data_dir, "ect.lut"),
                [(r / scale, t * scale) for r, t in WEC_ECT_LUT_9000],
                int_x=True,
                decimals_y=3,
            )
            write_lut_file(
                os.path.join(data_dir, "umdreh.lut"),
                [(r / scale, m) for r, m in WEC_UMDREH_LUT_9000],
                int_x=True,
                decimals_y=3,
            )
            write_lut_file(
                os.path.join(data_dir, "beschl.lut"),
                [(0, 0), (0.5, 0.3), (1, 1)],
                int_x=False,
                decimals_y=2,
            )
            write_lut_file(
                os.path.join(data_dir, "geschw.lut"),
                [(0, 1), (50, 1), (51, 0), (189, 0), (190, 1), (320, 0.8), (325, 0)],
                int_x=True,
                decimals_y=2,
            )

            count, _, acd_path = pack_acd(self.current_car_dir)
            self.load_car_directory(self.current_car_dir)
            self.status_lbl.config(text=f"Preset Hibrido Hypercar WEC instalado y empaquetado ({count} archivos)")
            messagebox.showinfo(
                "Preset Hibrido Hypercar WEC Instalado",
                f"Se configuro el sistema hibrido en modo MEDIUM (adaptado a {int(car_limiter)} RPM) "
                f"y se empaqueto en:\n{acd_path}",
            )
        except Exception as e:
            show_error_dialog("Error al instalar Preset Hibrido", str(e))

    # ==========================================================================
    # LÓGICA DE SONIDO (SOUND SWAPPER) Y RENOMBRADO SEGURO DE AUTO
    # ==========================================================================

    def browse_donor_sound_folder(self) -> None:
        initial = r"Z:\FH6\evo" if os.path.isdir(r"Z:\FH6\evo") else os.getcwd()
        selected = filedialog.askdirectory(initialdir=initial, title="Seleccionar carpeta del auto donante de sonido")
        if selected:
            self.donor_sound_var.set(selected)

    def browse_donor_bank_file(self) -> None:
        initial = r"Z:\FH6\evo" if os.path.isdir(r"Z:\FH6\evo") else os.getcwd()
        selected = filedialog.askopenfilename(
            initialdir=initial,
            title="Seleccionar archivo .bank donante",
            filetypes=[("FMOD Sound Bank", "*.bank"), ("Todos los archivos", "*.*")],
        )
        if selected:
            self.donor_sound_var.set(selected)

    def action_apply_sound_swap(self) -> None:
        if not self.current_car_dir:
            messagebox.showinfo("Aviso", "Primero selecciona o arrastra el auto al que queres cambiarle el sonido.")
            return
        donor = self.donor_sound_var.get().strip()
        if not donor:
            self.browse_donor_sound_folder()
            donor = self.donor_sound_var.get().strip()
            if not donor:
                return

        try:
            donor_id, count = swap_car_sound(self.current_car_dir, donor)
            car_name = os.path.basename(self.current_car_dir)
            self.status_lbl.config(
                text=f"Sonido de '{donor_id}' aplicado a '{car_name}' ({count} rutas adaptadas en GUIDs.txt)"
            )
            messagebox.showinfo(
                "Sonido Aplicado con Exito",
                f"Se copio el banco de sonido de '{donor_id}' a:\n"
                f"sfx/{car_name}.bank\n\n"
                f"Y se adaptaron {count} eventos en sfx/GUIDs.txt.\n"
                f"(Tu sonido anterior quedo resguardado en sfx_backup/)",
            )
        except Exception as e:
            show_error_dialog("Error al cambiar el sonido", str(e))

    def action_restore_sound_backup(self) -> None:
        if not self.current_car_dir:
            messagebox.showinfo("Aviso", "Primero selecciona un auto.")
            return
        backup_sfx = os.path.join(self.current_car_dir, "sfx_backup")
        target_sfx = os.path.join(self.current_car_dir, "sfx")
        if not os.path.isdir(backup_sfx):
            messagebox.showinfo("Aviso", "No hay copia de seguridad en 'sfx_backup/' para este auto.")
            return
        try:
            os.makedirs(target_sfx, exist_ok=True)
            for f in os.listdir(backup_sfx):
                src_f = os.path.join(backup_sfx, f)
                if os.path.isfile(src_f):
                    shutil.copy2(src_f, os.path.join(target_sfx, f))
            self.status_lbl.config(text="Sonido original restaurado desde sfx_backup/")
            messagebox.showinfo("Restaurado", "Se restauro el sonido original desde sfx_backup/.")
        except Exception as e:
            show_error_dialog("Error al restaurar sonido", str(e))

    def action_safe_rename_car(self) -> None:
        if not self.current_car_dir or not os.path.isdir(self.current_car_dir):
            messagebox.showinfo("Aviso", "Primero selecciona o arrastra un auto.")
            return

        new_name = self.new_folder_name_var.get().strip()
        if not new_name or any(c in new_name for c in r'\/:*?"<>| '):
            messagebox.showwarning(
                "Nombre invalido",
                "Ingresa un nombre de carpeta valido sin espacios ni caracteres especiales (ej. lsa_genesis_lmh).",
            )
            return

        old_dir = self.current_car_dir
        old_name = os.path.basename(old_dir)
        parent_dir = os.path.dirname(old_dir)
        new_dir = os.path.join(parent_dir, new_name)

        if os.path.abspath(old_dir).lower() == os.path.abspath(new_dir).lower() and old_name == new_name:
            messagebox.showinfo("Aviso", "El nuevo nombre es igual al actual.")
            return

        if os.path.exists(new_dir) and os.path.abspath(old_dir).lower() != os.path.abspath(new_dir).lower():
            show_error_dialog("Error", f"Ya existe una carpeta llamada:\n{new_dir}")
            return

        try:
            create_physics_backup(old_dir)
            data_dir = os.path.join(old_dir, "data")
            if not os.path.isdir(data_dir) and os.path.isfile(os.path.join(old_dir, "data.acd")):
                unpack_acd(old_dir)

            shutil.move(old_dir, new_dir)

            sfx_dir = os.path.join(new_dir, "sfx")
            if os.path.isdir(sfx_dir):
                old_bank = os.path.join(sfx_dir, f"{old_name}.bank")
                new_bank = os.path.join(sfx_dir, f"{new_name}.bank")
                if os.path.isfile(old_bank) and not os.path.exists(new_bank):
                    shutil.move(old_bank, new_bank)

                guids_path = os.path.join(sfx_dir, "GUIDs.txt")
                if os.path.isfile(guids_path):
                    with open(guids_path, "r", encoding="utf-8", errors="replace") as f:
                        gtext = f.read()
                    gtext = re.sub(
                        r"(event:/cars/)([^/\s]+)(/)",
                        lambda m: f"{m.group(1)}{new_name}{m.group(3)}",
                        gtext,
                        flags=re.IGNORECASE,
                    )
                    gtext = re.sub(
                        rf"(bank:/){re.escape(old_name)}\b",
                        f"\\1{new_name}",
                        gtext,
                        flags=re.IGNORECASE,
                    )
                    with open(guids_path, "w", encoding="utf-8", newline="\r\n") as f:
                        f.write(gtext)

            if os.path.isdir(os.path.join(new_dir, "data")):
                pack_acd(new_dir, create_backup=False)

            self.load_car_directory(new_dir)
            self.status_lbl.config(
                text=f"Auto renombrado a '{new_name}', sonido adaptado y data.acd re-encriptado."
            )
            messagebox.showinfo(
                "Auto Renombrado con Exito",
                f"La carpeta del auto ahora es:\n{new_dir}\n\n"
                f"- data.acd re-encriptado con la nueva clave\n"
                f"- sfx/{new_name}.bank y GUIDs.txt actualizados",
            )
        except Exception as e:
            show_error_dialog("Error al renombrar el auto", str(e))

    # ==========================================================================
    # NAVEGACIÓN Y ARCHIVOS
    # ==========================================================================

    def browse_car_folder(self) -> None:
        initial = self.path_var.get() if os.path.isdir(self.path_var.get()) else r"Z:\FH6\evo"
        selected = filedialog.askdirectory(initialdir=initial, title="Seleccionar carpeta del auto")
        if selected:
            self.load_car_directory(selected)

    def browse_acd_file(self) -> None:
        initial = self.path_var.get() if os.path.isdir(self.path_var.get()) else r"Z:\FH6\evo"
        selected = filedialog.askopenfilename(
            initialdir=initial,
            title="Seleccionar archivo data.acd",
            filetypes=[("Assetto Corsa Data", "data.acd *.acd"), ("Todos los archivos", "*.*")],
        )
        if selected:
            self.handle_dropped_item(selected)

    def load_car_directory(self, path_str: str) -> None:
        if not path_str:
            return
        car_dir = resolve_car_dir(path_str)
        if not os.path.isdir(car_dir):
            show_error_dialog("Error", f"La ruta no existe:\n{car_dir}")
            return

        self.current_car_dir = car_dir
        self.path_var.set(car_dir)
        folder_name = os.path.basename(car_dir)
        self.folder_lbl.config(text=folder_name)
        self.sound_current_lbl.config(text=f"Auto destino actual: {folder_name}")
        self.rename_current_lbl.config(text=f"Nombre actual: {folder_name}")
        self.new_folder_name_var.set(folder_name)

        acd_exists = os.path.isfile(os.path.join(car_dir, "data.acd"))
        data_dir = os.path.join(car_dir, "data")
        data_exists = os.path.isdir(data_dir)

        status_parts = []
        if acd_exists:
            status_parts.append("data.acd presente")
        if data_exists:
            status_parts.append("carpeta data/ presente")
        if not status_parts:
            status_parts.append("No se encontro data.acd ni carpeta data/ en esta ruta")

        self.status_lbl.config(text=" | ".join(status_parts))
        self._show_placeholder()

        if data_exists:
            self.all_files = sorted(
                f for f in os.listdir(data_dir) if os.path.isfile(os.path.join(data_dir, f))
            )
        else:
            self.all_files = []
        self._refresh_file_list()
        self._load_bop_and_hybrid_fields()

    def _refresh_file_list(self) -> None:
        query = self.search_var.get().strip().lower()
        self.file_listbox.delete(0, tk.END)
        for f in self.all_files:
            if not query or query in f.lower():
                self.file_listbox.insert(tk.END, f)

    def on_file_selected(self, _event: object = None) -> None:
        sel = self.file_listbox.curselection()
        if not sel or not self.current_car_dir:
            return
        fname = self.file_listbox.get(sel[0])
        fpath = os.path.join(self.current_car_dir, "data", fname)
        if not os.path.isfile(fpath):
            return

        try:
            with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            self.current_file_name = fname
            self.editor_file_lbl.config(text=f"Editando: data/{fname}")
            self.text_editor.config(state=tk.NORMAL)
            self.text_editor.delete("1.0", tk.END)
            self.text_editor.insert("1.0", content)
        except Exception as e:
            show_error_dialog("Error al leer archivo", str(e))

    def save_current_file_only(self) -> bool:
        if not self.current_car_dir or not self.current_file_name:
            messagebox.showinfo("Aviso", "Primero selecciona un archivo de la lista de la izquierda.")
            return False
        fpath = os.path.join(self.current_car_dir, "data", self.current_file_name)
        content = self.text_editor.get("1.0", "end-1c")
        try:
            with open(fpath, "w", encoding="utf-8", newline="\r\n") as f:
                f.write(content)
            self.status_lbl.config(text=f"Guardado data/{self.current_file_name}")
            self._load_bop_and_hybrid_fields()
            return True
        except Exception as e:
            show_error_dialog("Error al guardar", str(e))
            return False

    def action_unpack(self) -> None:
        path_str = self.path_var.get().strip()
        if not path_str:
            self.browse_car_folder()
            return
        try:
            count, _used_key, data_dir = unpack_acd(path_str)
            self.load_car_directory(path_str)
            self.status_lbl.config(text=f"Desencriptados {count} archivos en data/ (backup en data.acd.bak)")
            messagebox.showinfo(
                "Desencriptado exitoso",
                f"Se extrajeron {count} archivos en:\n{data_dir}\n\nBackup creado: data.acd.bak",
            )
        except Exception as e:
            show_error_dialog("Error al desencriptar", str(e))

    def action_pack(self) -> None:
        path_str = self.path_var.get().strip()
        if not path_str:
            self.browse_car_folder()
            return
        try:
            count, _used_key, acd_path = pack_acd(path_str)
            self.load_car_directory(path_str)
            self.status_lbl.config(text=f"Empaquetados {count} archivos en data.acd")
            messagebox.showinfo(
                "Empaquetado exitoso",
                f"Se empaquetaron {count} archivos en:\n{acd_path}",
            )
        except Exception as e:
            show_error_dialog("Error al empaquetar", str(e))

    def action_save_and_repack(self) -> None:
        if self.current_file_name:
            if not self.save_current_file_only():
                return
        self.action_pack()

    def action_open_explorer(self) -> None:
        target = self.current_car_dir or self.path_var.get().strip()
        if target and os.path.isdir(target):
            os.startfile(target)


def main() -> None:
    try:
        parser = argparse.ArgumentParser(
            description=f"{APP_TITLE} — {SUPPORT_FOOTER}"
        )
        subparsers = parser.add_subparsers(dest="command")

        p_unpack = subparsers.add_parser("unpack", help="Desencriptar data.acd hacia la carpeta data/")
        p_unpack.add_argument("path", help="Ruta a la carpeta del auto o al archivo data.acd")

        p_pack = subparsers.add_parser("pack", help="Empaquetar carpeta data/ hacia data.acd")
        p_pack.add_argument("path", help="Ruta a la carpeta del auto o a la carpeta data/")

        if len(sys.argv) == 2 and sys.argv[1] not in ("unpack", "pack", "-h", "--help"):
            dropped_path = sys.argv[1]
            root = tk.Tk()
            LSADecryptionToolGUI(root, initial_dir=dropped_path)
            root.mainloop()
            return

        args = parser.parse_args()

        if args.command == "unpack":
            count, _, data_dir = unpack_acd(args.path)
            print(f"[{APP_TITLE}] Extraídos {count} archivos en: {data_dir}")
        elif args.command == "pack":
            count, _, acd_path = pack_acd(args.path)
            print(f"[{APP_TITLE}] Empaquetados {count} archivos en: {acd_path}")
        else:
            root = tk.Tk()
            LSADecryptionToolGUI(root)
            root.mainloop()
    except Exception as exc:
        try:
            show_error_dialog(f"Error inesperado en {APP_TITLE}", f"{exc}\n\n{traceback.format_exc(limit=2)}")
        except Exception:
            sys.stderr.write(f"Error: {exc}\n{SUPPORT_FOOTER}\n")


if __name__ == "__main__":
    main()
