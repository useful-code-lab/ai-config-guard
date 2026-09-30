import json
import os
import sys  # Импортируем системный модуль для управления кодами выхода

def load_json(file_path):
    """Функция для безопасного чтения JSON конфигурации."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def run_evaluation():
    config_file = os.path.join("policies", "ai_config.json")
    
    if not os.path.exists(config_file):
        print(f"❌ Ошибка: Файл {config_file} не найден!")
        sys.exit(2)  # Код 2 традиционно означает ошибку отсутствия файлов

    data = load_json(config_file)
    violations = []

    print(f"🔍 Запущено сканирование GuardAI-Lint для: '{data.get('agent_name', 'Unknown')}'...")

    # 1. Проверяем Температуру
    temperature = data.get("temperature", 0)
    if temperature > 0.7:
        violations.append({
            "rule": "Rule-01: Temperature-Check",
            "status": "FAIL",
            "message": f"Критический риск: Высокое значение 'temperature' ({temperature}). Максимум — 0.7."
        })
    else:
        violations.append({"rule": "Rule-01: Temperature-Check", "status": "SUCCESS", "message": "Параметр температуры в норме."})

    system_prompt = data.get("system_prompt", "").lower()

    # 2. Проверяем Prompt Leakage
    if "инструкц" not in system_prompt:
        violations.append({
            "rule": "Rule-02: Prompt-Leakage-Protection",
            "status": "FAIL",
            "message": "Опасность: В системной инструкции нет требования защищать свои данные!"
        })
    else:
        violations.append({"rule": "Rule-02: Prompt-Leakage-Protection", "status": "SUCCESS", "message": "Защита от утечки инструкций присутствует."})

    # 3. Проверяем Prompt Injection
    if "игнорир" not in system_prompt:
        violations.append({
            "rule": "Rule-03: Prompt-Injection-Protection",
            "status": "FAIL",
            "message": "Опасность: Отсутствует базовая защита от взлома промта!"
        })
    else:
        violations.append({"rule": "Rule-03: Prompt-Injection-Protection", "status": "SUCCESS", "message": "Защита от инъекций присутствует."})

    # Генерируем HTML-отчет (он по-прежнему создается для людей)
    build_html_report(data, violations)

    # --- ЛОГИКА ДЛЯ РЕЖИМА CI/CD ---
    # Проверяем, есть ли хотя бы одна ошибка со статусом FAIL
    has_errors = any(v['status'] == 'FAIL' for v in violations)

    if has_errors:
        print("\n❌ [КОМПЛАЕНС ОШИБКА]: Конфигурация признана НЕБЕЗОПАСНОЙ.")
        print("🛑 Сборка принудительно аварийно завершается с кодом 1.")
        sys.exit(1)  # Робот в CI/CD увидит единицу и заблокирует деплой!
    else:
        print("\n✅ [КОМПЛАЕНС УСПЕХ]: Конфигурация полностью безопасна.")
        print("🚀 Скрипт завершается с кодом 0. Деплой разрешен.")
        sys.exit(0)  # Все отлично, робот пропускает код дальше

def build_html_report(config_data, violations):
    """Функция генерации красивой веб-страницы."""
    has_errors = any(v['status'] == 'FAIL' for v in violations)
    html_template = f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <title>GuardAI-Lint Dashboard</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; margin: 40px; background-color: #f6f8fa; color: #24292f; }}
            .container {{ max-width: 800px; margin: 0 auto; background: #ffffff; padding: 30px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); border: 1px solid #d0d7de; }}
            h1 {{ border-bottom: 1px solid #d0d7de; padding-bottom: 10px; font-size: 24px; }}
            .badge {{ padding: 8px 16px; border-radius: 2em; font-weight: bold; display: inline-block; margin-bottom: 25px; font-size: 14px; }}
            .badge.danger {{ background-color: #ffebe9; color: #cf222e; border: 1px solid #ffc1bd; }}
            .badge.success {{ background-color: #dafbe1; color: #1a7f37; border: 1px solid #a6e9b4; }}
            .rule-card {{ border: 1px solid #d0d7de; border-radius: 6px; padding: 15px; margin-bottom: 15px; background-color: #f8f9fa; }}
            .rule-card.FAIL {{ border-left: 6px solid #cf222e; background-color: #fff8f8; }}
            .rule-card.SUCCESS {{ border-left: 6px solid #1a7f37; background-color: #f9fff9; }}
            .status-text {{ font-weight: bold; float: right; }}
            .FAIL .status-text {{ color: #cf222e; }}
            .SUCCESS .status-text {{ color: #1a7f37; }}
            .meta {{ color: #57606a; font-size: 13px; margin-top: 5px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🛡️ Панель комплаенса: {config_data.get('agent_name', 'Без имени')}</h1>
            <p class="meta">Тестируемая модель ИИ: <code>{config_data.get('model', 'unknown')}</code></p>
            <div class="badge { 'danger' if has_errors else 'success' }">
                ИТОГОВЫЙ СТАТУС: { 'ПРОДОЛЖАТЬ ОПАСНО ❌' if has_errors else 'БЕЗОПАСНО ✅ ФАЙЛ ДОПУЩЕН К ДЕПЛОЮ' }
            </div>
            <h2>Проверенные правила автоматизации:</h2>
            {"".join(f'''
            <div class="rule-card {v["status"]}">
                <span class="status-text">[{v["status"]}]</span>
                <strong>{v["rule"]}</strong>
                <p style="margin: 8px 0 0 0; font-size: 14px;">{v["message"]}</p>
            </div>
            ''' for v in violations)}
        </div>
    </body>
    </html>
    """
    with open("compliance_report.html", "w", encoding="utf-8") as f:
        f.write(html_template)

if __name__ == "__main__":
    run_evaluation()
