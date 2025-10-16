import json
import logging
import os
import subprocess
import sys
from typing import Any, Dict, Optional

import yaml


class EvoCodexShell:
    """
    Продвинутая оболочка для управления архитектурой EVO через Termux
    с глубокой интеграцией в PEAR-процессор и модули EvoPyramid.
    """

    def __init__(self, config_path: str = None):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.config_path = config_path or os.path.join(self.base_dir, "EvoMETA", "evo_config.yaml")
        self._setup_logging()
        self.config = self._load_config()
        self._init_paths()

        logging.info("EvoCodexShell инициализирован")
        self._warm_up_pear_processor()

    def _default_config(self) -> Dict[str, Any]:
        return {"ritual_commands": {}, "integration_modules": []}

    def _load_config(self) -> Dict[str, Any]:
        """Загрузка конфигурации с обработкой ошибок"""

        if not os.path.exists(self.config_path):
            logging.warning(
                "Конфигурация не найдена по пути %s. Использую значения по умолчанию.",
                self.config_path,
            )
            return self._default_config()

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                raw = f.read()
                config = yaml.safe_load(raw) if yaml else json.loads(raw)
                if config is None:
                    config = {}
        except json.JSONDecodeError as exc:
            logging.critical("Ошибка разбора JSON-конфига: %s", exc)
            return self._default_config()
        except Exception as exc:  # pragma: no cover - defensive
            logging.critical("Ошибка загрузки конфига: %s", exc)
            return self._default_config()

        if not isinstance(config, dict):
            logging.error(
                "Некорректный формат конфига (%s). Ожидался словарь верхнего уровня.",
                type(config).__name__,
            )
            return self._default_config()

        for section in ("ritual_commands", "integration_modules"):
            if section not in config:
                logging.error("Отсутствует обязательная секция конфига: %s", section)
                config[section] = [] if section == "integration_modules" else {}
                continue

            value = config[section]
            expected_type = list if section == "integration_modules" else dict
            if not isinstance(value, expected_type):
                logging.error(
                    "Секция %s имеет некорректный тип (%s). Сбрасываю к значению по умолчанию.",
                    section,
                    type(value).__name__,
                )
                config[section] = [] if section == "integration_modules" else {}

        return config

    def _setup_logging(self):
        """Настройка системы логирования с ротацией"""
        log_dir = os.path.join(self.base_dir, "PEAR_logs")
        os.makedirs(log_dir, exist_ok=True)

        logging.basicConfig(
            level=logging.DEBUG,
            format="[%(asctime)s] %(levelname)s [EVO]: %(message)s",
            handlers=[
                logging.FileHandler(os.path.join(log_dir, "evocodex_shell.log")),
                logging.StreamHandler(sys.stdout),
            ],
        )

    def _init_paths(self):
        """Инициализация путей к ключевым модулям EVO"""
        self.paths = {
            "pear_processor": os.path.join(self.base_dir, "Core", "PEAR_Processor"),
            "evo_agi": os.path.join(self.base_dir, "EvoPyramid", "EvoAGI"),
            "evo_chaos": os.path.join(self.base_dir, "Evo_Chaos"),
            "api_integration": os.path.join(self.base_dir, "Evo_EcoSystem", "API_Integration"),
            "quarantine": os.path.join(self.base_dir, "Evo_Chaos", "EvoRepository"),
        }

    def _warm_up_pear_processor(self):
        """Предварительная инициализация PEAR процессора"""
        pear_init = os.path.join(self.paths["pear_processor"], "__init__.py")
        if os.path.exists(pear_init):
            try:
                subprocess.run(
                    [sys.executable, pear_init],
                    cwd=self.paths["pear_processor"],
                    check=True,
                )
                logging.info("PEAR Processor успешно инициализирован")
            except subprocess.CalledProcessError as e:
                logging.error(f"Ошибка инициализации PEAR Processor: {e}")

    def execute_command(self, command: str, module: Optional[str] = None) -> Optional[str]:
        """
        Выполнение команды с учетом контекста EVO
        :param command: Команда для выполнения
        :param module: Целевой модуль EVO (Core, EvoAGI и т.д.)
        :return: Результат выполнения или None при ошибке
        """
        context = self.paths.get(module.lower(), self.base_dir) if module else self.base_dir

        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=context,
                check=True,
                capture_output=True,
                text=True,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logging.error(f"Ошибка выполнения команды: {e.stderr.strip()}")
            return None

    def run_ritual(self, ritual_name: str) -> str:
        """Выполнение ритуала с обработкой PEAR-контекста"""
        if ritual_name not in self.config.get("ritual_commands", {}):
            return f"🌀 Ритуал '{ritual_name}' не найден в хрониках EVO"

        ritual = self.config["ritual_commands"][ritual_name]
        logging.info(f"Инициация ритуала: {ritual.get('description', ritual_name)}")

        if ritual_name.startswith("pear_"):
            return self._handle_pear_ritual(ritual)

        output = self.execute_command(ritual["command"])
        return self._format_response(ritual["command"], output, ritual_name)

    def _handle_pear_ritual(self, ritual: Dict[str, Any]) -> str:
        """Обработка ритуалов, связанных с PEAR-процессором"""
        command = ritual["command"]

        if ".PEAR" in command:
            pear_file = command.split()[-1]
            processed_dir = os.path.join(self.paths["pear_processor"], "processed")
            os.makedirs(processed_dir, exist_ok=True)
            logging.info(f"Выполнение PEAR-ритуала: {pear_file}")

        output = self.execute_command(command)
        return self._format_response(command, output, "PEAR Ритуал")

    def _format_response(self, command: str, output: Optional[str], title: str = "") -> str:
        """Форматирование ответа в стиле EVO"""
        response = []

        if title:
            response.append(f"### 🌀 {title}\n")

        response.append("```bash\n" + command + "\n```")

        if output:
            response.append("\n**Результат:**\n````\n" + output + "\n````")
        else:
            response.append("\n🌀 Команда выполнена, но не вернула результат")

        response.append(self._generate_context_hint(command))

        return "\n".join(response)

    def _generate_context_hint(self, command: str) -> str:
        if "python3" in command and "EvoAGI" in command:
            return "\n> 💡 Совет: Для глубокой диагностики EvoAGI используйте `diagnose_evo.sh`"
        if "PEAR" in command:
            return "\n> 💡 Совет: PEAR-логи доступны в директории PEAR_logs"
        return ""

    def diagnose_system(self) -> str:
        """Комплексная диагностика системы EVO"""
        checks = [
            ("Проверка Core модулей", self._check_core_modules),
            ("Валидация PEAR процессора", self._validate_pear_processor),
            ("Проверка Quarantine", self._check_quarantine),
            ("Тест API интеграции", self._test_api_integration),
        ]

        results = []
        for name, check_func in checks:
            try:
                success, message = check_func()
                results.append(f"- {name}: {'✅' if success else '❌'} {message}")
            except Exception as e:  # pragma: no cover - defensive
                results.append(f"- {name}: ❌ Ошибка: {str(e)}")

        return "## 🔍 Результаты диагностики EVO\n" + "\n".join(results)

    def _check_core_modules(self) -> (bool, str):
        required = ["evo_core.py", "evo_connectors.py", "pear_chain.py"]
        core_dir = os.path.join(self.paths["pear_processor"], "..")
        missing = [f for f in required if not os.path.exists(os.path.join(core_dir, f))]
        if missing:
            return False, f"Отсутствуют файлы: {', '.join(missing)}"
        return True, "Все ключевые модули на месте"

    def _validate_pear_processor(self) -> (bool, str):
        init_file = os.path.join(self.paths["pear_processor"], "__init__.py")
        if not os.path.exists(init_file):
            return False, "PEAR Processor не инициализирован"

        try:
            output = self.execute_command(f"python3 {init_file}")
            if output:
                return True, f"PEAR Processor активен: {output[:50]}..."
            return True, "PEAR Processor готов"
        except Exception as e:  # pragma: no cover - defensive
            return False, f"Ошибка инициализации: {str(e)}"

    def _check_quarantine(self) -> (bool, str):
        quarantine_dir = self.paths["quarantine"]
        if not os.path.exists(quarantine_dir):
            return False, "Quarantine репозиторий не найден"
        contents = os.listdir(quarantine_dir)
        if not contents:
            return False, "Quarantine пуст"
        return True, f"Найдено {len(contents)} артефактов в Quarantine"

    def _test_api_integration(self) -> (bool, str):
        api_dir = self.paths["api_integration"]
        if not os.path.exists(api_dir):
            return False, "API Integration модуль отсутствует"
        connectors = [f for f in os.listdir(api_dir) if f.endswith(".py")]
        if not connectors:
            return False, "Не найдено ни одного Python-коннектора"
        return True, f"Доступно {len(connectors)} API коннектора"

    def interactive_shell(self):
        print(
            f"""
        🌀 EvoCodexShell [v2.0] | PEAR Integration
        Базовая директория: {self.base_dir}
        Доступные команды:
          - diagnose: Полная диагностика системы
          - rituals: Список доступных ритуалов
          - exit: Выход из оболочки
        """
        )

        while True:
            try:
                cmd = input("EVO/PEAR> ").strip()

                if not cmd:
                    continue
                if cmd.lower() == "exit":
                    break
                if cmd.lower() == "diagnose":
                    print(self.diagnose_system())
                elif cmd.lower() == "rituals":
                    print(self._list_rituals())
                elif cmd in self.config.get("ritual_commands", {}):
                    print(self.run_ritual(cmd))
                else:
                    output = self.execute_command(cmd)
                    print(self._format_response(cmd, output or "Команда выполнена"))

            except KeyboardInterrupt:
                print("\nДля выхода введите 'exit'")
            except Exception as e:  # pragma: no cover - defensive
                logging.error(f"Ошибка выполнения: {str(e)}")

    def _list_rituals(self) -> str:
        rituals = self.config.get("ritual_commands", {})
        if not rituals:
            return "🌀 В хрониках не найдено ни одного ритуала"

        return "## 🌀 Доступные ритуалы EVO:\n" + "\n".join(
            f"- {name}: {desc.get('description', 'Без описания')}"
            for name, desc in rituals.items()
        )


def main():
    shell = EvoCodexShell()
    shell.interactive_shell()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # pragma: no cover - defensive
        logging.critical(f"Критическая ошибка: {str(e)}")
        sys.exit(1)
