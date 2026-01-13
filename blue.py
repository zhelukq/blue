#!/usr/bin/env python3
"""
Bluetooth сканер для Termux/Android с автообновлением из GitHub
(использует termux-bt scan вместо bluetoothctl)
"""

import sys
import time
import subprocess
import os
from datetime import datetime

__VERSION__ = "2.1.0"
GITHUB_RAW_URL = "https://raw.githubusercontent.com/zhelukq/blue/main/blue.py"
SCRIPT_PATH = os.path.abspath(__file__)


def clear_screen():
    subprocess.run(['clear'] if sys.platform != 'win32' else ['cls'], shell=True)


def scan_bluetooth():
    """
    Сканирование через termux-bt scan (нужен Termux:API и pkg install termux-api).
    Формат вывода смотри через: termux-bt scan
    """
    devices = []
    try:
        # termux-bt scan может немного висеть, дадим ему до 15 секунд
        result = subprocess.run(
            ["termux-bt", "scan"],
            capture_output=True, text=True, timeout=15
        )

        if result.returncode != 0:
            print(f"Ошибка termux-bt scan (код {result.returncode}):\n{result.stderr}")
            time.sleep(2)
            return devices

        # Примерный формат строк (см. у себя через termux-bt scan):
        # AA:BB:CC:DD:EE:FF SomeDeviceName
        # 11:22:33:44:55:66 JBL Flip 6
        for line in result.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) >= 1:
                mac = parts[0]
                name = " ".join(parts[1:]) if len(parts) > 1 else "Unknown"
                devices.append((mac, name))

        return devices

    except subprocess.TimeoutExpired:
        print("Ошибка сканирования: termux-bt scan timeout")
        time.sleep(2)
        return devices
    except Exception as e:
        print(f"Ошибка сканирования: {e}")
        time.sleep(2)
        return devices


def print_devices(devices):
    clear_screen()
    print("=" * 50)
    print(f"🔍 Bluetooth Scanner v{__VERSION__} [{datetime.now().strftime('%H:%M:%S')}]")
    print("=" * 50)
    if not devices:
        print("📱 Нет устройств. Проверь BT / права Termux:API!")
    else:
        print(f"📡 Найдено: {len(devices)} устройств")
        for i, (mac, name) in enumerate(devices, 1):
            print(f"[{i:2d}] {mac} → {name}")
    print("=" * 50)
    print("[0] Обновить | [u] Обновить скрипт | [q] Выход")
    print()


def check_for_update():
    """Проверка и автообновление скрипта с GitHub через curl (надёжно в Termux)"""
    try:
        print("🔄 Проверка обновлений с GitHub...")

        import tempfile

        # Временный файл для загрузки
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name

        # Качаем через curl
        curl_cmd = ["curl", "-L", "-s", GITHUB_RAW_URL, "-o", tmp_path]
        res = subprocess.run(curl_cmd)

        if res.returncode != 0:
            print("❌ curl не смог скачать файл (проверь URL/интернет)")
            time.sleep(2)
            return

        # Читаем скачанный код
        with open(tmp_path, "r", encoding="utf-8") as f:
            remote_code = f.read()

        # Ищем __VERSION__ в удалённом файле
        remote_version = None
        for line in remote_code.splitlines():
            if line.strip().startswith("__VERSION__"):
                remote_version = line.split("=", 1)[1].strip().strip("\"'")
                break

        if not remote_version:
            print("❌ Не удалось определить версию на GitHub")
            time.sleep(2)
            return

        if remote_version == __VERSION__:
            print(f"✅ У тебя уже последняя версия ({__VERSION__})")
            time.sleep(1.5)
            return

        print(f"⬆️ Найдена новая версия: {remote_version} (у тебя {__VERSION__})")
        print("💾 Обновляю скрипт...")

        # Бэкап
        backup_path = SCRIPT_PATH + ".bak"
        try:
            if os.path.exists(SCRIPT_PATH):
                os.replace(SCRIPT_PATH, backup_path)
        except Exception as e:
            print(f"⚠️ Не удалось сделать бэкап: {e}")

        # Записываем новый код
        with open(SCRIPT_PATH, "w", encoding="utf-8") as f:
            f.write(remote_code)

        print("✅ Обновление завершено, перезапуск...")
        time.sleep(1)
        os.execv(sys.executable, [sys.executable, SCRIPT_PATH])

    except Exception as e:
        print(f"❌ Ошибка обновления: {e}")
        time.sleep(2)


def main():
    print(f"🚀 Запуск Bluetooth Scanner v{__VERSION__}")
    print("Нужно: Termux:API + pkg install termux-api, BT включен, права выданы.")
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
                        print("Дальше можно руками дернуть: termux-bt info (если появится в API)")
                        input("\nНажми Enter для возврата...")
                except ValueError:
                    print("❌ Введи 0, номер, u или q")
                    time.sleep(1.5)
        except KeyboardInterrupt:
            print("\n👋 Выход по Ctrl+C")
            break


if __name__ == "__main__":
    main()
