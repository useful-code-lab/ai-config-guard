import json
import os
import sys
import re

def load_json(file_path):
    """Безопасное чтение конфигурационного файла."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def evaluate_file(file_path):
    """Проверка одного конкретного файла конфигурации."""
    try:
        data = load_json(file_path)
    except Exception as e:
        return None, [{
            "rule": "JSON-Syntax-Check",
            "status": "FAIL",
            "message": f"Ошибка синтаксиса в файле {file_path}: {e}"
        }]

    violations = []
    
    # 1. Проверяем Температуру
    temperature = data.get("temperature", 0)
    if temperature > 0.7:
        violations.append({
            "rule": "Rule-01: Temperature-Check",
            "status": "FAIL",
            "message": f"Критический риск в {file_path}: Значение 'temperature' ({temperature}) выше 0.7."
        })
    else:
        violations.append({"rule": "Rule-01: Temperature-Check", "status": "SUCCESS", "message": f"[{file_path}] Температура в норме."})

    system_prompt = data.get("system_prompt", "").lower()

    # 2. Проверяем Prompt Leakage
    if "инструкц" not in system_prompt:
        violations.append({
            "rule": "Rule-02: Prompt-Leakage-Protection",
            "status": "FAIL",
            "message": f"Опасность в {file_path}: В системной инструкции нет требования защищать данные!"
        })
    else:
        violations.append({"rule": "Rule-02: Prompt-Leakage-Protection", "status": "SUCCESS", "message": f"[{file_path}] Защита от утечки инструкций присутствует."})

    # 3. Проверяем Prompt Injection
    if "игнорир" not in system_prompt:
        violations.append({
            "rule": "Rule-03: Prompt-Injection-Protection",
            "status": "FAIL",
            "message": f"Опасность в {file_path}: Отсутствует базовая защита от взлома промта!"
        })
    else:
        violations.append({"rule": "Rule-03: Prompt-Injection-Protection", "status": "SUCCESS", "message": f"[{file_path}] Защита от инъекций присутствует."})

    # 4. Проверяем утечку секретных API-ключей
    raw_json_text = json.dumps(data)
    api_key_pattern = r"sk-[a-zA-Z0-9-]{20,60}"
    found_keys = re.findall(api_key_pattern, raw_json_text)
    
    if found_keys:
        first_key = found_keys[0]
        masked_key = f"{first_key[:6]}...{first_key[-4:]}"
        violations.append({
            "rule": "Rule-04: Secret-Token-Leak-Protection",
            "status": "FAIL",
            "message": f"КАТАСТРОФА в {file_path}: Обнаружен забытый секретный API-ключ OpenAI ({masked_key})!"
        })
    else:
        violations.append({"rule": "Rule-04: Secret-Token-Leak-Protection", "status": "SUCCESS", "message": f"[{file_path}] Секретные API-ключи не обнаружены."})

    return data.get('agent_name', file_path), violations

def main():
    print("\n🔍 [GuardAI-Lint] Глобальное сканирование директории...")
    print("-" * 60)

    all_violations = []
    files_to_scan = []

    # Ищем файлы конфигурации в корне и в папке policies
    directories_to_search = [".", "policies"]
    for target_dir in directories_to_search:
        if os.path.exists(target_dir):
            for file in os.listdir(target_dir):
                if file.endswith("_config.json"):
                    full_path = os.path.join(target_dir, file)
                    # Избегаем дубликатов, если папки пересекаются
                    if full_path not in files_to_scan:
                        files_to_scan.append(full_path)

    if not files_to_scan:
        print("❌ Ошибка комплаенса: Не найдено ни одного файла конфигурации (*_config.json)!")
        sys.exit(2)

    # Сканируем каждый найденный файл
    for file_path in files_to_scan:
        agent_name, file_violations = evaluate_file(file_path)
        all_violations.extend(file_violations)
        
        print(f"\n📄 Файл: {file_path} (Агент: {agent_name})")
        for v in file_violations:
            icon = "✅" if v["status"] == "SUCCESS" else "❌"
            print(f"  {icon} [{v['status']}] {v['rule']}: {v['message']}")

    # Итоговый вердикт для CI/CD автоматизации
    has_errors = any(v['status'] == 'FAIL' for v in all_violations)

    print("\n" + "=" * 60)
    if has_errors:
        print("❌ [КОМПЛАЕНС ОШИБКА]: Обнаружены критические уязвимости безопасности!")
        print("🛑 Сборка принудительно заблокирована в конвейере. Код выхода 1.\n")
        sys.exit(1)
    else:
        print("✅ [КОМПЛАЕНС УСПЕХ]: Все файлы конфигураций ИИ полностью безопасны.")
        print("🚀 Скрипт завершается с кодом 0. Деплой в продакшен разрешен.\n")
        sys.exit(0)

if __name__ == "__main__":
    main()
