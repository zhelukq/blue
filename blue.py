#!/usr/bin/env python3
"""
Bluetooth сканер для Termux через Termux:API
Простое сканирование устройств
"""

import os
import sys
import json
import time
import subprocess
from datetime import datetime

__VERSION__ = "2.2.0"
GITHUB_RAW_URL = "https://raw.githubusercontent.com/zhelukq/blue/main/blue.py"
SCRIPT_PATH = os.path.abspath(__file__)

def clear_screen():
    """Очистка экрана"""
    os.system('clear' if os.name != 'nt' else 'cls')

def check_termux_api():
    """Проверка наличия Termux:API"""
    try:
        result = subprocess.run(['termux-bluetooth-status'], 
                               capture_output=True, text=True, timeout=3)
        return result.returncode == 0
    except:
        return False

def install_termux_api():
    """Инструкция по установке Termux:API"""
    clear_screen()
    print("=" * 60)
    print("📱 ТРЕБУЕТСЯ Termux:API")
    print("=" * 60)
    print("\n1. Установите Termux:API из Play Store:")
    print("   https://play.google.com/store/apps/details?id=com.termux.api")
    print("\n2. Дайте все разрешения приложению")
    print("\n3. Вернитесь в Termux и нажмите Enter...")
    print("=" * 60)
    input()

def enable_bluetooth():
    """Включить Bluetooth"""
    try:
        result = subprocess.run(['termux-bluetooth-enable'], 
                               capture_output=True, text=True, timeout=5)
        time.sleep(2)
        return True
    except:
        return False

def scan_bluetooth(duration=10):
    """
    Сканировать Bluetooth устройства
    duration: время сканирования в секундах
    """
    devices = []
    
    try:
        print(f"\n🔍 Сканирование {duration} секунд...")
        
        # Запускаем сканирование с таймаутом
        result = subprocess.run(
            ['timeout', str(duration), 'termux-bluetooth-scan'],
            capture_output=True,
            text=True,
            timeout=duration + 2
        )
        
        if result.stdout.strip():
            try:
                # Пробуем распарсить JSON
                devices = json.loads(result.stdout)
            except json.JSONDecodeError:
                # Если не JSON, парсим построчно
                for line in result.stdout.strip().split('\n'):
                    line = line.strip()
                    if line and not line.startswith('WARNING'):
                        try:
                            # Пробуем парсить как JSON объект
                            device = json.loads(line)
                            devices.append(device)
                        except:
                            # Или создаем простой объект
                            if 'mac' in line.lower() or 'name' in line.lower():
                                device = {}
                                if 'name:' in line:
                                    device['name'] = line.split('name:')[1].split(',')[0].strip()
                                if 'mac:' in line:
                                    device['mac'] = line.split('mac:')[1].split(',')[0].strip()
                                if device:
                                    devices.append(device)
        
        return devices
        
    except subprocess.TimeoutExpired:
        print("⚠️  Таймаут сканирования")
        return []
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return []

def print_devices(devices):
    """Вывод списка устройств"""
    clear_screen()
    print("=" * 60)
    print(f"📡 Bluetooth Scanner v{__VERSION__}")
    print(f"🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    if not devices:
        print("\n❌ Устройства не найдены")
        print("\nВозможные причины:")
        print("• Bluetooth выключен на телефоне")
        print("• Нет устройств поблизости")
        print("• Устройства не в режиме обнаружения")
    else:
        print(f"\n✅ Найдено устройств: {len(devices)}\n")
        print("-" * 60)
        
        for i, device in enumerate(devices, 1):
            name = device.get('name', device.get('alias', 'Unknown'))
            mac = device.get('mac', device.get('address', 'N/A'))
            rssi = device.get('rssi', 'N/A')
            
            print(f"[{i:2d}] {name}")
            print(f"     MAC: {mac}")
            if rssi != 'N/A':
                print(f"     Сигнал: {rssi} dBm")
            print()
    
    print("=" * 60)
    print("\nКОМАНДЫ:")
    print("  [s] - Сканировать (10 сек)")
    print("  [f] - Сканировать (30 сек)")
    print("  [e] - Включить Bluetooth")
    print("  [d] - Выключить Bluetooth")
    print("  [u] - Обновить скрипт")
    print("  [q] - Выход")
    print("=" * 60)

def check_for_update():
    """Проверка обновлений"""
    print("\n🔄 Проверка обновлений...")
    
    try:
        # Скачиваем файл напрямую через urllib
        import urllib.request
        
        req = urllib.request.Request(
            GITHUB_RAW_URL,
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        
        with urllib.request.urlopen(req, timeout=10) as response:
            remote_code = response.read().decode('utf-8')
        
        # Ищем версию
        remote_version = None
        for line in remote_code.split('\n'):
            if '__VERSION__' in line and '=' in line:
                remote_version = line.split('=')[1].strip().strip('"\'')
                break
        
        if not remote_version:
            print("❌ Не удалось определить версию")
            time.sleep(2)
            return
        
        if remote_version == __VERSION__:
            print(f"✅ У вас последняя версия ({__VERSION__})")
            time.sleep(1)
            return
        
        print(f"⬆️ Доступна версия {remote_version} (у вас {__VERSION__})")
        choice = input("Обновить? (y/N): ").strip().lower()
        
        if choice == 'y':
            # Создаем бэкап
            backup_path = SCRIPT_PATH + '.bak'
            try:
                import shutil
                shutil.copy2(SCRIPT_PATH, backup_path)
                print(f"📋 Создан бэкап: {backup_path}")
            except:
                pass
            
            # Сохраняем новую версию
            with open(SCRIPT_PATH, 'w', encoding='utf-8') as f:
                f.write(remote_code)
            
            print("✅ Обновлено! Перезапуск...")
            time.sleep(2)
            os.execv(sys.executable, [sys.executable, SCRIPT_PATH])
        else:
            print("❌ Обновление отменено")
            time.sleep(1)
            
    except Exception as e:
        print(f"❌ Ошибка обновления: {e}")
        time.sleep(2)

def main():
    """Главная функция"""
    # Проверяем Termux:API
    if not check_termux_api():
        install_termux_api()
        if not check_termux_api():
            print("❌ Termux:API не установлен. Выход.")
            sys.exit(1)
    
    clear_screen()
    print("=" * 60)
    print(f"🚀 Bluetooth Scanner v{__VERSION__}")
    print("=" * 60)
    print("Используется Termux:API для гарантированной работы")
    print("=" * 60)
    
    # Проверяем обновления при старте
    check_for_update()
    
    # Включаем Bluetooth
    print("\n🔵 Включаю Bluetooth...")
    if enable_bluetooth():
        print("✅ Bluetooth включен")
    else:
        print("⚠️  Не удалось включить автоматически")
        print("   Включите Bluetooth в шторке уведомлений")
    
    time.sleep(2)
    
    devices = []
    scan_count = 0
    
    while True:
        print_devices(devices)
        
        try:
            choice = input("\nВведите команду: ").strip().lower()
            
            if choice == 's':
                scan_count += 1
                print(f"\n📡 Сканирование #{scan_count}...")
                devices = scan_bluetooth(10)
                
            elif choice == 'f':
                scan_count += 1
                print(f"\n🔍 Детальное сканирование #{scan_count}...")
                devices = scan_bluetooth(30)
                
            elif choice == 'e':
                print("\n🔵 Включаю Bluetooth...")
                if enable_bluetooth():
                    print("✅ Bluetooth включен")
                else:
                    print("❌ Не удалось включить")
                time.sleep(1)
                
            elif choice == 'd':
                print("\n🔴 Выключаю Bluetooth...")
                subprocess.run(['termux-bluetooth-disable'], 
                              capture_output=True, timeout=3)
                print("✅ Bluetooth выключен")
                time.sleep(1)
                
            elif choice == 'u':
                check_for_update()
                
            elif choice == 'q':
                print("\n👋 Выход...")
                break
                
            else:
                print("❌ Неизвестная команда")
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n\n👋 Выход по Ctrl+C")
            break

if __name__ == "__main__":
    main()
