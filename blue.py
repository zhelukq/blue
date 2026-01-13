#!/usr/bin/env python3
"""
Bluetooth сканер для Termux/Android с автообновлением из GitHub
"""

import sys
import time
import subprocess
import os
import urllib.request
from datetime import datetime

__VERSION__ = "1.0.1"
GITHUB_RAW_URL = "https://raw.githubusercontent.com/zhelukq/blue/main/blue.py"
SCRIPT_PATH = os.path.abspath(__file__)


def clear_screen():
    subprocess.run(['clear'] if sys.platform != 'win32' else ['cls'], shell=True)


def scan_bluetooth():
    try:
        subprocess.run(['bluetoothctl', 'scan', 'on'],
                       capture_output=True, text=True, timeout=1)
        time.sleep(8)
        result = subprocess.run(['bluetoothctl', 'devices'],
                                capture_output=True, text=True, timeout=3)

        subprocess.run(['bluetoothctl', 'scan', 'off'],
                       capture_output=True, text=True, timeout=1)

        devices = []
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                if line.startswith('Device '):
                    parts = line.split()
                    if len(parts) >= 3:
                        mac = parts[1]
                        name = ' '.join(parts[2:])
                        devices.append((mac, name))
        return devices
    except Exception as e:
        print(f"Ошибка сканирования: {e}")
        return []


def print_devices(devices):
    clear_screen()
    print("=" * 50)
    print(f"🔍 Bluetooth Scanner v{__VERSION__} [{datetime.now().strftime('%H:%M:%S')}]")
    print("=" * 50)
    if not devices:
        print("📱 Нет устройств. Проверь BT!")
    else:
        print(f"📡 Найдено: {len(devices)} устройств")
        for i, (mac, name) in enumerate(devices, 1):
            print(f"[{i:2d}] {mac} → {name}")
    print("=" * 50)
    print("[0] Обновить | [u] Обновить скрипт | [q] Выход")
    print()


def check_for_update():
    """Проверка и автообновление скрипта с GitHub"""
    try:
        print("🔄 Проверка обновлений с GitHub...")
        with urllib.request.urlopen(GITHUB_RAW_URL, timeout=5) as resp:
            remote_code = resp.read().decode('utf-8')

        # Очень простая проверка: ищем строку __VERSION__
        remote_version = None
        for line in remote_code.splitlines():
            if line.strip().startswith("__VERSION__"):
                # __VERSION__ = "1.0.1"
                remote_version = line.split('=')[1].strip().strip('"\'')
                break

        if not remote_version:
            print("❌ Не удалось определить версию на GitHub")
            return

        if remote_version == __VERSION__:
            print(f"✅ У тебя уже последняя версия ({__VERSION__})")
            time.sleep(1.5)
            return

        print(f"⬆️ Найдена новая версия: {remote_version} (у тебя {__VERSION__})")
        print("💾 Скачиваю обновление...")

        # Бэкап старого файла
        backup_path = SCRIPT_PATH + ".bak"
        try:
            if os.path.exists(SCRIPT_PATH):
                os.replace(SCRIPT_PATH, backup_path)
        except Exception as e:
            print(f"⚠️ Не удалось сделать бэкап: {e}")

        # Записываем новый код
        with open(SCRIPT_PATH, 'w', encoding='utf-8') as f:
            f.write(remote_code)

        print("✅ Обновление завершено, перезапуск...")
        time.sleep(1)
        os.execv(sys.executable, [sys.executable, SCRIPT_PATH])

    except Exception as e:
        print(f"❌ Ошибка обновления: {e}")
        time.sleep(2)


def main():
    print(f"🚀 Запуск Bluetooth Scanner v{__VERSION__}")
    print("Установи: pkg install bluez && bluetoothctl power on")
    # авто‑проверка при старте
    check_for_update()

    while True:
        devices = scan_bluetooth()
        print_devices(devices)

        try:
            choice = input("Выбор: ").strip().lower()

            if choice == '0':
                continue  # просто обновить список устройств
            elif choice == 'u':
                check_for_update()
            elif choice == 'q':
                print("👋 До свидания!")
                break
            else:
                try:
                    idx = int(choice) - 1
                    if 0 <= idx < len(devices):
                        mac, name = devices[idx]
                        print(f"\n📱 Выбрано: {mac} ({name})")
                        print("Пример: bluetoothctl info", mac)
                        input("\nНажми Enter для возврата...")
                except ValueError:
                    print("❌ Введи 0, номер, u или q")
                    time.sleep(1.5)
        except KeyboardInterrupt:
            print("\n👋 Выход по Ctrl+C")
            break


if __name__ == "__main__":
    main()
