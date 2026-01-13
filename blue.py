#!/usr/bin/env python3
"""
Простой Bluetooth сканер для Termux - показывает все устройства поблизости
"""

import os
import sys
import time
import subprocess
import urllib.request
from datetime import datetime

__VERSION__ = "2.0.1"
GITHUB_RAW_URL = "https://raw.githubusercontent.com/zhelukq/blue/main/blue.py"
SCRIPT_PATH = os.path.abspath(__file__)

def clear_screen():
    """Очистка экрана"""
    os.system('clear' if os.name != 'nt' else 'cls')

def check_dependencies():
    """Проверка необходимых пакетов - упрощенная версия"""
    print("🔍 Проверка окружения...")
    
    # Проверяем наличие bluetoothctl (но не требуем установки)
    try:
        result = subprocess.run(['which', 'bluetoothctl'], 
                               capture_output=True, text=True)
        if result.returncode != 0:
            print("⚠️  bluetoothctl не найден")
            print("Пробую альтернативные методы...")
            return False
        return True
    except:
        return False

def enable_bluetooth():
    """Включаем Bluetooth разными способами"""
    print("🔵 Включаем Bluetooth...")
    
    # Способ 1: через service call (Android API)
    try:
        print("Попытка 1: через Android API...")
        # Этот метод работает на многих Android устройствах
        subprocess.run(['su', '-c', 'service call bluetooth_manager 6'], 
                      capture_output=True, timeout=3)
        time.sleep(2)
    except:
        pass
    
    # Способ 2: через settings put
    try:
        print("Попытка 2: через настройки Android...")
        subprocess.run(['settings', 'put', 'global', 'bluetooth_on', '1'], 
                      capture_output=True, timeout=3)
        time.sleep(2)
    except:
        pass
    
    # Способ 3: через bluetoothctl (если есть)
    try:
        print("Попытка 3: через bluetoothctl...")
        subprocess.run(['bluetoothctl', 'power', 'on'], 
                      capture_output=True, timeout=5)
        time.sleep(1)
    except:
        pass
    
    print("✅ Проверьте включен ли Bluetooth в шторке уведомлений")
    return True

def scan_devices_simple():
    """Простое сканирование устройств без bluetoothctl"""
    devices = []
    
    print("\n🔍 Начинаю сканирование...")
    print("Сканирование займет 8 секунд...")
    
    try:
        # Метод 1: Попробуем через bluetoothctl если есть
        try:
            # Включаем сканирование
            scan_proc = subprocess.Popen(['bluetoothctl', 'scan', 'on'], 
                                        stdout=subprocess.DEVNULL, 
                                        stderr=subprocess.DEVNULL)
            time.sleep(8)
            scan_proc.terminate()
            
            # Получаем список устройств
            result = subprocess.run(['bluetoothctl', 'devices'], 
                                   capture_output=True, text=True, timeout=5)
            
            # Выключаем сканирование
            subprocess.run(['bluetoothctl', 'scan', 'off'], 
                          capture_output=True, timeout=2)
            
            # Парсим результат
            for line in result.stdout.strip().split('\n'):
                if line.startswith('Device '):
                    parts = line.split()
                    if len(parts) >= 3:
                        mac = parts[1].strip()
                        name = ' '.join(parts[2:]).strip()
                        devices.append((mac, name))
                        
            if devices:
                return devices
                
        except:
            pass
        
        # Метод 2: Попробуем через hcitool если есть
        try:
            print("Пробую hcitool...")
            result = subprocess.run(['hcitool', 'scan'], 
                                   capture_output=True, text=True, timeout=10)
            
            for line in result.stdout.strip().split('\n')[1:]:
                if line.strip():
                    parts = line.strip().split('\t')
                    if len(parts) >= 2:
                        mac = parts[0].strip()
                        name = parts[1].strip()
                        devices.append((mac, name))
        except:
            pass
        
        # Метод 3: Через dumpsys bluetooth (Android)
        try:
            print("Пробую dumpsys bluetooth...")
            result = subprocess.run(['dumpsys', 'bluetooth'], 
                                   capture_output=True, text=True, timeout=5)
            
            for line in result.stdout.strip().split('\n'):
                if 'Device:' in line and 'Address:' in line:
                    try:
                        # Парсим MAC адрес
                        mac_start = line.find('Address:') + 8
                        mac = line[mac_start:mac_start+17].strip()
                        
                        # Парсим имя
                        name_start = line.find('Name:')
                        if name_start != -1:
                            name = line[name_start+5:].strip()
                        else:
                            name = "Unknown"
                            
                        if mac and len(mac) == 17:
                            devices.append((mac, name))
                    except:
                        continue
        except:
            pass
        
        return devices
        
    except Exception as e:
        print(f"❌ Ошибка сканирования: {e}")
        return []

def check_for_update():
    """Проверка и обновление скрипта с GitHub"""
    try:
        print("🔄 Проверка обновлений...")
        
        # Создаем временный файл
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
            tmp_path = tmp.name
        
        # Скачиваем через urllib (не требует curl)
        try:
            req = urllib.request.Request(
                GITHUB_RAW_URL,
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                remote_code = response.read().decode('utf-8')
                
                # Сохраняем во временный файл
                with open(tmp_path, 'w', encoding='utf-8') as f:
                    f.write(remote_code)
        except Exception as e:
            print(f"❌ Не удалось скачать обновление: {e}")
            os.unlink(tmp_path)
            time.sleep(2)
            return
        
        # Ищем версию в удаленном файле
        remote_version = None
        for line in remote_code.split('\n'):
            if '__VERSION__' in line and '=' in line:
                remote_version = line.split('=')[1].strip().strip('"\'')
                break
        
        if not remote_version:
            print("❌ Не удалось определить версию на GitHub")
            os.unlink(tmp_path)
            time.sleep(2)
            return
        
        if remote_version == __VERSION__:
            print(f"✅ У вас последняя версия ({__VERSION__})")
            os.unlink(tmp_path)
            time.sleep(1)
            return
        
        print(f"⬆️ Найдена новая версия: {remote_version} (ваша: {__VERSION__})")
        print("💾 Обновляю скрипт...")
        
        # Создаем бэкап
        backup_path = SCRIPT_PATH + ".bak"
        try:
            import shutil
            shutil.copy2(SCRIPT_PATH, backup_path)
            print(f"✅ Бэкап создан: {backup_path}")
        except:
            pass
        
        # Заменяем текущий скрипт
        with open(SCRIPT_PATH, 'w', encoding='utf-8') as f:
            f.write(remote_code)
        
        os.chmod(SCRIPT_PATH, 0o755)  # Делаем исполняемым
        
        print("✅ Обновление завершено!")
        print("🔄 Перезапускаю скрипт...")
        time.sleep(2)
        
        os.execv(sys.executable, [sys.executable, SCRIPT_PATH])
        
    except Exception as e:
        print(f"❌ Ошибка при обновлении: {e}")
        time.sleep(2)

def print_devices(devices):
    """Выводим список устройств"""
    clear_screen()
    print("="*60)
    print(f"📱 Bluetooth Scanner v{__VERSION__} [{datetime.now().strftime('%H:%M:%S')}]")
    print("="*60)
    
    if not devices:
        print("\n❌ Устройства не найдены")
        print("\nСоветы:")
        print("1. Включите Bluetooth в шторке уведомлений")
        print("2. Убедитесь, что устройства включены и видны")
        print("3. Перезапустите скрипт")
    else:
        print(f"\n✅ Найдено {len(devices)} устройств:\n")
        
        for i, (mac, name) in enumerate(devices, 1):
            print(f"📶 [{i:2d}] {name}")
            print(f"    MAC: {mac}")
            print()
    
    print("="*60)
    print("\nДействия:")
    print("  [R] - Сканировать заново")
    print("  [U] - Проверить обновления")
    print("  [S номер] - Подробнее об устройстве")
    print("  [C номер] - Подключиться к устройству")
    print("  [Q] - Выход")
    print()

def connect_to_device(mac, name):
    """Попытка подключиться к устройству"""
    print(f"\n🔗 Пытаюсь подключиться к {name}...")
    
    try:
        # Пробуем разные методы подключения
        methods = [
            ['bluetoothctl', 'connect', mac],
            ['am', 'start', '-a', 'android.bluetooth.devicepicker.ACTION_LAUNCH'],
            ['su', '-c', f'btcli connect {mac}']
        ]
        
        for method in methods:
            try:
                result = subprocess.run(method, 
                                      capture_output=True, text=True, timeout=10)
                if 'success' in result.stdout.lower() or 'connected' in result.stdout.lower():
                    print(f"✅ Успешно подключено к {name}")
                    return True
            except:
                continue
        
        print("⚠️  Не удалось автоматически подключиться")
        print(f"Попробуйте подключиться вручную к устройству: {name}")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    input("\nНажми Enter чтобы продолжить...")
    return False

def main():
    """Главная функция"""
    clear_screen()
    print("="*60)
    print(f"📱 Bluetooth Scanner v{__VERSION__} для Termux")
    print("="*60)
    print("Автообновление включено | Простой интерфейс")
    print("="*60)
    
    # Проверяем обновления при старте
    check_for_update()
    
    # Простая проверка окружения
    print("\n📋 Проверка окружения...")
    if not check_dependencies():
        print("\n⚠️  Некоторые инструменты недоступны")
        print("Скрипт будет использовать базовые методы")
        input("Нажми Enter чтобы продолжить...")
    
    # Включаем Bluetooth
    enable_bluetooth()
    
    devices = []
    
    while True:
        if not devices:
            print("\n🔄 Выполняю первое сканирование...")
            devices = scan_devices_simple()
        
        print_devices(devices)
        
        try:
            choice = input("Введите команду: ").strip().upper()
            
            if choice == 'R':
                print("\n🔄 Сканирую...")
                devices = scan_devices_simple()
                
            elif choice == 'U':
                check_for_update()
                devices = []  # Сбрасываем список для обновления
                
            elif choice == 'Q':
                print("\n👋 Выход...")
                # Пытаемся выключить сканирование если было включено
                try:
                    subprocess.run(['bluetoothctl', 'scan', 'off'], 
                                  capture_output=True, timeout=2)
                except:
                    pass
                sys.exit(0)
                
            elif choice.startswith('S '):
                try:
                    num = int(choice.split()[1]) - 1
                    if 0 <= num < len(devices):
                        mac, name = devices[num]
                        print(f"\n🔍 Детали устройства:")
                        print(f"Имя: {name}")
                        print(f"MAC: {mac}")
                        print(f"Тип: Bluetooth устройство")
                        print(f"Статус: Обнаружено при сканировании")
                        input("\nНажми Enter чтобы продолжить...")
                    else:
                        print("❌ Неверный номер устройства")
                        time.sleep(1)
                except:
                    print("❌ Неверный формат. Используйте: S 1")
                    time.sleep(1)
                    
            elif choice.startswith('C '):
                try:
                    num = int(choice.split()[1]) - 1
                    if 0 <= num < len(devices):
                        mac, name = devices[num]
                        connect_to_device(mac, name)
                    else:
                        print("❌ Неверный номер устройства")
                        time.sleep(1)
                except:
                    print("❌ Неверный формат. Используйте: C 1")
                    time.sleep(1)
                    
            else:
                print("❌ Неизвестная команда")
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n\n👋 Выход по Ctrl+C")
            sys.exit(0)

if __name__ == "__main__":
    main()
