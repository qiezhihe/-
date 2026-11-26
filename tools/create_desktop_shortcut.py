"""Create a desktop shortcut to the packaged desktop build."""
import base64
import ctypes
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / 'dist/RogueFPS/RogueFPS.exe'
NAME = '异星实验场'


def desktop_directory():
    buffer = ctypes.create_unicode_buffer(260)
    ctypes.windll.shell32.SHGetFolderPathW(None, 0x10, None, 0, buffer)
    return Path(buffer.value)


def main():
    if not TARGET.is_file():
        print(f'Missing build: {TARGET}')
        return 1
    script = f"""
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut('{desktop_directory() / (NAME + ".lnk")}')
$shortcut.TargetPath = '{TARGET}'
$shortcut.WorkingDirectory = '{TARGET.parent}'
$shortcut.IconLocation = '{TARGET},0'
$shortcut.Description = '{NAME} · 无限强化'
$shortcut.Save()
Write-Output $shortcut.TargetPath
"""
    encoded = base64.b64encode(script.encode('utf-16-le')).decode('ascii')
    result = subprocess.run(
        ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-EncodedCommand', encoded],
        capture_output=True, text=True, encoding='utf-8', errors='replace',
    )
    link = desktop_directory() / f'{NAME}.lnk'
    print(f'shortcut={link} exists={link.is_file()}')
    print(f'target={result.stdout.strip()}')
    if result.returncode or not link.is_file():
        print(result.stderr.strip())
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())