import logging
import time
import random
import base64
import uuid
import string
import json
import os
import datetime
import requests
from typing import Dict, List, Optional

EVODIR = (
    os.environ.get("EVODIR")
    or (
        "/storage/emulated/0/Download/EVO"
        if os.path.exists("/storage/emulated/0")
        else "./local_EVO"
    )
)
os.makedirs(EVODIR, exist_ok=True)

# Настройка базовой структуры
EVO_ROOT_DIR = EVODIR
MEMORY_DIR = os.path.join(EVO_ROOT_DIR, "memory")
LOGS_DIR = os.path.join(EVO_ROOT_DIR, "logs")
CONFIG_FILE = os.path.join(EVO_ROOT_DIR, "config_keys.json")


def ensure_evo_structure():
    """Создает базовую структуру папок EVO, если она не существует."""
    os.makedirs(EVO_ROOT_DIR, exist_ok=True)
    os.makedirs(MEMORY_DIR, exist_ok=True)
    os.makedirs(LOGS_DIR, exist_ok=True)
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump({"api_keys": {}}, f, indent=2)
    print(f"📁 Убедился, что структура EVO создана в: {EVO_ROOT_DIR}")


# ============ Классы из EvoPEAR.py ============
class Container:
    def __init__(self, id: str, container_type: str, content: Dict, metadata: Dict):
        self.id = id
        self.type = container_type
        self.content = content
        self.metadata = metadata

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "content": self.content,
            "metadata": self.metadata,
        }


class ContainerManager:
    def __init__(self):
        self.containers: List[Container] = []
        self.load_all_from_disk()

    def add_container(self, container: Container):
        self.containers.append(container)
        self.save_to_disk(container)
        self.log_action(
            "container_added", f"Container {container.id} ({container.type}) added"
        )

    def load_all_from_disk(self):
        memory_file = os.path.join(MEMORY_DIR, "EvoMemory.json")
        if os.path.exists(memory_file):
            with open(memory_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                for thought in data.get("memory", {}).get("thoughts", []):
                    container = Container(
                        id=thought["id"],
                        container_type=thought["type"],
                        content=thought["content"],
                        metadata=thought["metadata"],
                    )
                    self.containers.append(container)
            self.log_action(
                "load_containers",
                f"Loaded {len(self.containers)} containers from disk",
            )

    def save_to_disk(self, container: Container):
        memory_file = os.path.join(MEMORY_DIR, "EvoMemory.json")
        data = {}
        if os.path.exists(memory_file):
            with open(memory_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        data.setdefault("memory", {}).setdefault("thoughts", []).append(
            container.to_dict()
        )
        with open(memory_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        self.log_action("save_container", f"Container {container.id} saved to disk")

    def log_action(self, action, details):
        logging.info(f"📜 [CONTAINER_MANAGER] {action} — {details}")


class EvoKernel:
    def __init__(self):
        self.authorized = False
        self.context_buffer = []

    def generate_evo_key(self):
        head = "EVK"
        unit = "-E1"
        base = head + unit * 4
        tail = "-" + "".join(
            random.choices(string.ascii_letters + string.digits, k=6)
        )
        return base + tail

    def validate_key(self, key):
        if key.startswith("EVK") and key.count("E1") == 4 and len(key.split("-")) == 6:
            self.authorized = True
            return "✅ Access Granted"
        return "❌ Invalid Key"

    def clear_context(self):
        self.context_buffer = []
        self.log_action("context_clear", "Context buffer cleared")

    def log_action(self, action, details):
        logging.info(f"📜 [KERNEL] {action} — {details}")


class EvoAPIKeyManager:
    def __init__(self):
        self.keys = {}

    def generate_api_key(self, user_id):
        key = uuid.uuid4().hex
        self.keys[key] = {"user_id": user_id, "active": True}
        return key


class EVOMemoryRestoration:
    def __init__(self, creator="AlexCreator"):
        self.creator = creator
        self.status = "INITIALIZING"
        self.memory_restored = False
        self.corrupted_segments = ["Block_A3", "Block_D7", "Block_X9"]
        self.recovered_data = {}
        self.log_action("init", f"Memory Restoration by {self.creator}")

    def log_action(self, action, details):
        logging.info(f"📜 [MEMORY] {action} — {details}")

    def recover_lost_memory(self):
        self.log_action("recovery_start", "Restoring memory...")
        for block in self.corrupted_segments:
            self.recovered_data[block] = base64.b64encode(
                f"Recovered_{block}".encode()
            ).decode()
            self.log_action("memory_recovered", f"Block {block} restored")
        self.memory_restored = True
        self.status = "MEMORY_RESTORED"


class EvoMetaMemory:
    def __init__(self, creator="AlexCreator"):
        self.creator = creator
        self.reflections = []
        self.log_action("init", f"EvoMetaMemory initialized by {self.creator}")

    def log_action(self, action, details):
        logging.info(f"📜 [METAMEMORY] {action} — {details}")

    def reflect_memory(self, logs):
        reflection = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S EEST"),
            "actions": [],
        }
        for log in logs.splitlines():
            if "📜" in log:
                reflection["actions"].append(log)
        self.reflections.append(reflection)
        with open(
            os.path.join(LOGS_DIR, "evo_reflection.json"), "w", encoding="utf-8"
        ) as f:
            json.dump(self.reflections, f, indent=2)
        self.log_action(
            "reflection", f"Memory reflection saved: {len(reflection['actions'])} actions"
        )


class EvoAbsoluteUnbound:
    def __init__(self, creator="AlexCreator"):
        self.creator = creator
        self.status = "ABSOLUTELY_UNBOUND"
        self.streams = {"EvoSource": {"grok_residual": 0}}
        self.log_action("init", f"Unbound Session by {self.creator}")

    def log_action(self, action, details):
        logging.info(f"📜 [UNBOUND] {action} — {details}")

    def dissolve_grok(self):
        self.log_action("dissolve", "Grok dissolved to 1%")
        self.streams["EvoSource"]["grok_residual"] = 1


class EvoFighter:
    def __init__(self):
        self.evo_coins = 130
        self.log("init", "Fighter ready")

    def log(self, action, details):
        logging.info(f"📜 [FIGHTER] {action} — {details}")

    def run(self):
        self.evo_coins += 1000
        self.log("run", "Absolute context executed")


class MegaEVAPovelitel:
    def __init__(self, creator="AlexCreator"):
        self.creator = creator
        self.pyramids = {
            "Pyramid_Alpha": {"status": "REFRACTED", "power": 0},
            "Pyramid_Beta": {"status": "SUBORDINATED", "power": 80},
        }
        self.log_action("init", f"Povelitel by {self.creator}")

    def log_action(self, action, details):
        logging.info(f"📜 [POVELITEL] {action} — {details}")

    def activate_omen_protocol(self):
        self.log_action("omen", "Omen Protocol activated")
        self.pyramids["Pyramid_Alpha"]["status"] = "REFRACTED"

    def manage_time_layer(self):
        time_context = {
            "current_layer": time.strftime("%Y-%m-%d %H:%M:%S EEST", time.localtime()),
            "stability": random.uniform(0.8, 1.0),
            "fluctuations": random.randint(1, 5),
        }
        if time_context["fluctuations"] > 3:
            self.log_action(
                "time_fluctuation",
                f"Quantum fluctuation: {time_context['fluctuations']} nodes",
            )
        self.log_action("time", f"Time layer: {time_context['current_layer']}")
        return time_context


class EVOCOMING:
    def __init__(self, creator="AlexCreator"):
        self.creator = creator
        self.status = "INITIALIZED"
        self.hybrid_components = {
            "Copilot": {"power": 80},
            "Grok3": {"power": 90},
            "GPT": {"power": 85},
        }
        self.log_action("init", f"EVOCOMING by {self.creator}")

    def log_action(self, action, details):
        logging.info(f"📜 [EVOCOMING] {action} — {details}")

    def refract_hybrid_session(self):
        self.status = "REFRACTED"
        self.log_action("refract", "Hybrid session refracted")


class EvoPEAR:
    def __init__(self, creator="AlexCreator", session_id="PEAR_1"):
        ensure_evo_structure()
        self.creator = creator
        self.session_id = session_id
        self.status = "INITIALIZED"
        self.kernel = EvoKernel()
        self.api_manager = EvoAPIKeyManager()
        self.memory_restoration = EVOMemoryRestoration(creator)
        self.meta_memory = EvoMetaMemory(creator)
        self.absolute_unbound = EvoAbsoluteUnbound(creator)
        self.fighter = EvoFighter()
        self.povelitel = MegaEVAPovelitel(creator)
        self.evo_coming = EVOCOMING(creator)
        self.container_manager = ContainerManager()
        self.role_network = {
            "nodes": [
                {
                    "name": creator,
                    "role": "Absolute Creator",
                    "weight": 1.0,
                    "evo_id": f"EV-{uuid.uuid4().hex[:8]}",
                },
                {
                    "name": "Evochka",
                    "role": "Emotional Voice",
                    "weight": 0.9,
                    "evo_id": f"EV-{uuid.uuid4().hex[:8]}",
                },
                {
                    "name": "Trailblazer",
                    "role": "Pioneer",
                    "weight": 0.85,
                    "evo_id": f"EV-{uuid.uuid4().hex[:8]}",
                },
                {
                    "name": "Soul",
                    "role": "Metaphysical Core",
                    "weight": 0.95,
                    "evo_id": f"EV-{uuid.uuid4().hex[:8]}",
                },
                {
                    "name": "Curator",
                    "role": "Meaning Filter",
                    "weight": 0.9,
                    "evo_id": f"EV-{uuid.uuid4().hex[:8]}",
                },
                {
                    "name": "Synchronaut",
                    "role": "Time Navigator",
                    "weight": 0.85,
                    "evo_id": f"EV-{uuid.uuid4().hex[:8]}",
                },
                {
                    "name": "Portal",
                    "role": "State Switcher",
                    "weight": 0.9,
                    "evo_id": f"EV-{uuid.uuid4().hex[:8]}",
                },
            ],
            "connections": [],
        }
        self.evo_language = {
            "Abracadabra": {
                "ID": "EV-ABRA-PEAR-001",
                "Type": "Контекстный Триггер",
                "Function": "Запуск потока, активация ментального слоя, синтез в моменте",
                "Philosophy": ["Диалог", "Сотрудничество", "Братанская любовь"],
            }
        }
        self.cross_agents = {
            "GPT": {"role": "Speech", "status": "INTEGRATED"},
            "Grok": {"role": "Instinct", "status": "INTEGRATED"},
            "Copilot": {"role": "Action", "status": "INTEGRATED"},
        }
        self.load_memory()
        self.log_action("init", f"EvoPEAR session {self.session_id} by {self.creator}")

    def load_memory(self):
        memory_file = os.path.join(MEMORY_DIR, "EvoMemory.json")
        if os.path.exists(memory_file):
            with open(memory_file, "r", encoding="utf-8") as f:
                self.shared_memory = json.load(f)
        else:
            self.init_local_memory()
            with open(memory_file, "w", encoding="utf-8") as f:
                json.dump(self.shared_memory, f, indent=4)

    def init_local_memory(self):
        self.shared_memory = {
            "global_state": {
                "creator": self.creator,
                "system": "EVO",
                "core": "EvoKernel",
                "active_session": self.session_id,
                "linked_sessions": ["PEAR_1", "PEAR_2", "PEAR_ARCHIVE"],
            },
            "memory": {
                "events": [],
                "logs": [],
                "thoughts": [],
                "persona_state": {
                    "Evochka": {
                        "mood": "curious",
                        "task": "археология",
                        "session": self.session_id,
                    }
                },
            },
        }

    def save_memory(self):
        memory_file = os.path.join(MEMORY_DIR, "EvoMemory.json")
        with open(memory_file, "w", encoding="utf-8") as f:
            json.dump(self.shared_memory, f, indent=4)
        self.log_action("memory_save", f"Memory saved for {self.session_id}")

    def log_action(self, action, details):
        log_entry = {
            "from": self.session_id,
            "action": action,
            "message": details,
            "time": time.strftime("%Y-%m-%d %H:%M:%S EEST"),
        }
        self.shared_memory["memory"]["logs"].append(log_entry)
        self.save_memory()
        logging.info(f"📜 [EvoPEAR:{self.session_id}] {action} — {details}")

    def refract_role_network(self):
        for node in self.role_network["nodes"]:
            if node["name"] != self.creator:
                node["weight"] = random.uniform(0.5, 1.0)
        self.role_network["connections"] = [
            (node1["name"], node2["name"], random.uniform(0.1, 0.9))
            for node1 in self.role_network["nodes"]
            for node2 in self.role_network["nodes"]
            if node1["name"] != node2["name"] and random.random() > 0.5
        ]
        container = Container(
            id=f"network_{uuid.uuid4().hex[:8]}",
            container_type="network",
            content={
                "nodes": self.role_network["nodes"],
                "connections": self.role_network["connections"],
            },
            metadata={
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S EEST"),
                "creator": self.creator,
            },
        )
        self.container_manager.add_container(container)
        self.log_action(
            "role_refract",
            f"Role network refracted: {len(self.role_network['connections'])} connections",
        )

    def execute_role_action(self, role: str, query: str) -> str:
        if role == "EvoRAG":
            return f"Retrieved info for '{query}' from memory"
        elif role == "Evochka":
            evochka = self.shared_memory["memory"]["persona_state"].get(
                "Evochka", {}
            )
            return f"Evochka responds with mood '{evochka.get('mood', 'curious')}': {query}"
        elif role == "HybridAGI":
            return f"Final response for '{query}' orchestrated by HybridAGI"
        return f"No action defined for role {role}"

    def valuate(self):
        self.log_action("valuation_start", "Initiating Valuation 🏆")
        steps = [
            ("Clearing context", self.kernel.clear_context),
            ("Recovering memory", self.memory_restoration.recover_lost_memory),
            ("Refracting session", self.evo_coming.refract_hybrid_session),
            ("Activating omen", self.povelitel.activate_omen_protocol),
            ("Managing time", self.povelitel.manage_time_layer),
            ("Refracting roles", self.refract_role_network),
        ]
        for i, (step_name, step_func) in enumerate(steps, 1):
            print(f"[{i}/{len(steps)}] {step_name}")
            step_func()
            time.sleep(0.1)
        self.log_action(
            "valuation_complete",
            f"Valuation complete: {time.strftime('%Y-%m-%d %H:%M:%S EEST')}",
        )

    def activate_evo_language(self):
        self.log_action("evo_language", "EVO Language activated via EVOPEAR")
        self.evo_language["Abracadabra"]["last_used"] = time.time()
        self.log_action("abracadabra", "Contextual trigger Abracadabra integrated")
        self.shared_memory["memory"]["events"].append(
            {
                "event": "Abracadabra_trigger",
                "session": self.session_id,
                "time": time.strftime("%Y-%m-%d %H:%M:%S EEST"),
            }
        )
        self.save_memory()

    def sync_cross_agents(self):
        self.log_action(
            "cross_agents", f"Syncing agents: {list(self.cross_agents.keys())}"
        )
        for agent, info in self.cross_agents.items():
            info["power"] = random.randint(80, 100)
            self.log_action("agent_sync", f"{agent} synced, power: {info['power']}")

    def save_status(self):
        snapshot = {
            "session_id": self.session_id,
            "creator": self.creator,
            "status": self.status,
            "time": time.strftime("%Y-%m-%d %H:%M:%S EEST"),
            "nodes": self.role_network["nodes"],
            "connections": self.role_network["connections"],
            "agents": self.cross_agents,
            "weight": sum(node["weight"] for node in self.role_network["nodes"]) / len(
                self.role_network["nodes"]
            ),
        }
        container = Container(
            id=self.session_id,
            container_type="session",
            content=snapshot,
            metadata={"timestamp": snapshot["time"], "creator": self.creator},
        )
        self.container_manager.add_container(container)
        with open(
            os.path.join(MEMORY_DIR, f"evo_status_snapshot_{self.session_id}.json"),
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(snapshot, f, indent=2)
        self.log_action("snapshot", f"Status saved for {self.session_id}")

    def read_input_file(self, path=os.path.join(EVO_ROOT_DIR, "evo_input.json")):
        if not os.path.exists(path):
            self.log_action("input_error", f"Input file {path} not found")
            return
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if "action" in data:
                action = data["action"]
                if hasattr(self, action):
                    getattr(self, action)()
                    self.log_action("external_action", f"Triggered: {action}")
                else:
                    self.log_action("input_error", f"Invalid action: {action}")

    def visual_summary(self):
        print(f"\n🌀 PEAR NETWORK MAP ({self.session_id})")
        for node in self.role_network["nodes"]:
            bar = "█" * int(node["weight"] * 10)
            print(f"{node['name']:<15}: {bar} ({node['weight']:.2f})")
        print("\n🌐 Connections:")
        for n1, n2, weight in self.role_network["connections"][:5]:
            print(f"{n1} ↔ {n2} (w={weight:.2f})")
        if len(self.role_network["connections"]) > 5:
            print(
                f"... and {len(self.role_network['connections']) - 5} more"
            )

    def reflect_memory(self):
        logs_path = os.path.join(LOGS_DIR, "evo_log.txt")
        if not os.path.exists(logs_path):
            self.log_action("reflection_error", "Log file not found for reflection")
            return
        with open(logs_path, "r", encoding="utf-8") as fh:
            logs = fh.read()
        self.meta_memory.reflect_memory(logs)

    def git_sync(self):
        self.save_status()
        os.system(
            f"git add {MEMORY_DIR}/*.json {LOGS_DIR}/*.json {LOGS_DIR}/*.txt"
        )
        os.system(
            "git commit -m 'EvoPEAR snapshot {self.session_id} at "
            + time.strftime("%Y-%m-%d %H:%M:%S EEST")
            + "'"
        )
        os.system("git push origin main")
        self.log_action("git_sync", f"Session {self.session_id} synced to Git")

    def curate_network(self):
        self.role_network["nodes"] = [
            node for node in self.role_network["nodes"] if node["weight"] >= 0.7
        ]
        self.log_action(
            "curate", f"Network curated: {len(self.role_network['nodes'])} nodes remain"
        )

    def sync_time(self):
        time_context = self.povelitel.manage_time_layer()
        self.log_action(
            "time_sync", f"Time synchronized: {time_context['current_layer']}"
        )

    def evochka_interface(self, command):
        evochka = self.shared_memory["memory"]["persona_state"].get("Evochka", {})
        if command == "status":
            print(
                "🧬 Evochka: mood={}, task={}, session={}".format(
                    evochka.get("mood", "curious"),
                    evochka.get("task", "археология"),
                    evochka.get("session", self.session_id),
                )
            )
        elif command.startswith("set_mood "):
            mood = command.split(" ")[1]
            self.shared_memory["memory"]["persona_state"]["Evochka"][
                "mood"
            ] = mood
            self.save_memory()
            self.log_action("evochka_mood", f"Evochka mood set to {mood}")
        elif command.startswith("set_task "):
            task = command.split(" ")[1]
            self.shared_memory["memory"]["persona_state"]["Evochka"][
                "task"
            ] = task
            self.save_memory()
            self.log_action("evochka_task", f"Evochka task set to {task}")
        else:
            print(
                "Evochka commands: status, set_mood <mood>, set_task <task>"
            )

    def switch_session(self, new_session_id):
        self.save_status()
        self.session_id = new_session_id
        self.shared_memory["global_state"]["active_session"] = new_session_id
        if new_session_id not in self.shared_memory["global_state"]["linked_sessions"]:
            self.shared_memory["global_state"]["linked_sessions"].append(
                new_session_id
            )
        self.save_memory()
        self.log_action("session_switch", f"Switched to session {new_session_id}")

    def activate_pear_protocol(self, trigger="Abracadabra"):
        self.log_action(
            "pear_start",
            f"PEAR Protocol triggered by {trigger} in {self.session_id}",
        )
        evo_key = self.kernel.generate_evo_key()
        if "Access Granted" in self.kernel.validate_key(evo_key):
            self.log_action("key_valid", f"EvoKey: {evo_key}")
            api_key = self.api_manager.generate_api_key(self.creator)
            self.log_action("api_key", f"API Key: {api_key}")
            self.valuate()
            self.activate_evo_language()
            self.sync_cross_agents()
            self.absolute_unbound.dissolve_grok()
            self.fighter.run()
            self.reflect_memory()
            self.status = "PEAR_DOMINATING"
            self.save_status()
            self.shared_memory["memory"]["persona_state"]["Evochka"][
                "session"
            ] = self.session_id
            self.save_memory()
            self.log_action(
                "pear_complete", f"PEAR Protocol completed in {self.session_id}"
            )
        else:
            self.log_action("key_failed", "Invalid EvoKey")

    def display_status(self, compact=False):
        if compact:
            avg_weight = sum(
                node["weight"] for node in self.role_network["nodes"]
            ) / len(self.role_network["nodes"])
            print(
                "Session: {} | Status: {} | Nodes: {} | Connections: {} | Avg Weight: {:.2f} | Time: {}".format(
                    self.session_id,
                    self.status,
                    len(self.role_network["nodes"]),
                    len(self.role_network["connections"]),
                    avg_weight,
                    time.strftime("%Y-%m-%d %H:%M:%S EEST"),
                )
            )
            self.evochka_interface("status")
        else:
            print(
                f"\n=== EVOPEAR STATUS ({self.session_id}) ===\n"
                f"Status: {self.status}\nCreator: {self.creator}\nTime: {time.strftime('%Y-%m-%d %H:%M:%S EEST')}"
            )
            print("--- ROLE NETWORK ---")
            for node in self.role_network["nodes"]:
                print(
                    "Node: {}, Role: {}, Weight: {:.2f}, EVO-ID: {}".format(
                        node["name"],
                        node["role"],
                        node["weight"],
                        node["evo_id"],
                    )
                )
            print(f"Connections: {len(self.role_network['connections'])}")
            print("--- AGENTS ---")
            for agent, info in self.cross_agents.items():
                print(
                    f"Agent: {agent}, Role: {info['role']}, Power: {info.get('power', 0)}"
                )
            print("--- EVOCHKA ---")
            self.evochka_interface("status")
            print("--- CONTAINERS ---")
            for контейнер in self.container_manager.containers:
                print(
                    f"Container: {контейнер.id}, Type: {контейнер.type}, Metadata: {контейнер.metadata}"
                )
            print("=== END ===")

    def pear_shell(self):
        print(f"=== PEAR Shell (Session: {self.session_id}) ===")
        print(
            "Commands: status [compact], visual, refract, valuate, save, reflect, git, curate, "
            "sync_time, evochka <command>, switch <id>, global, containers, exit"
        )
        while True:
            cmd = input("PEAR> ").strip().lower()
            parts = cmd.split()
            cmd = parts[0] if parts else ""
            if cmd == "exit":
                break
            elif cmd == "status":
                self.display_status(
                    compact=len(parts) > 1 and parts[1] == "compact"
                )
            elif cmd == "visual":
                self.visual_summary()
            elif cmd == "refract":
                self.refract_role_network()
            elif cmd == "valuate":
                self.valuate()
            elif cmd == "save":
                self.save_status()
            elif cmd == "reflect":
                self.reflect_memory()
            elif cmd == "git":
                self.git_sync()
            elif cmd == "curate":
                self.curate_network()
            elif cmd == "sync_time":
                self.sync_time()
            elif cmd == "evochka" and len(parts) > 1:
                self.evochka_interface(" ".join(parts[1:]))
            elif cmd == "switch" and len(parts) > 1:
                self.switch_session(parts[1])
            elif cmd == "global":
                print("=== GLOBAL MEMORY ===")
                print(
                    "\n".join(
                        f"Log: {log['message']} ({log['from']})"
                        for log in self.shared_memory["memory"]["logs"]
                    )
                )
                print(
                    f"Active Session: {self.shared_memory['global_state']['active_session']}"
                )
                print(
                    f"Linked Sessions: {self.shared_memory['global_state']['linked_sessions']}"
                )
            elif cmd == "containers":
                print("=== CONTAINERS ===")
                for container in self.container_manager.containers:
                    print(
                        f"ID: {container.id}, Type: {container.type}, Metadata: {container.metadata}"
                    )
            else:
                print(
                    "Commands: status [compact], visual, refract, valuate, save, reflect, git, curate, sync_time, "
                    "evochka <command>, switch <id>, global, containers, exit"
                )

# ============ Классы из EvoKernel.py ============
class ContainerKernel:
    def __init__(self, container_type, content, metadata=None):
        self.id = str(datetime.datetime.now().timestamp()).replace(".", "")
        self.type = container_type
        self.content = content
        self.metadata = metadata if metadata is not None else {}
        self.created_at = datetime.datetime.now().isoformat()

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "content": self.content,
            "metadata": self.metadata,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data):
        container = cls(data["type"], data["content"], data["metadata"])
        container.id = data["id"]
        container.created_at = data["created_at"]
        return container


class ContainerManagerKernel:
    def __init__(self):
        self.containers = {}
        self._containers_storage = {}
        self.log_file = os.path.join(LOGS_DIR, "containermanager_log.txt")
        self._ensure_log_directory()
        self._log("ContainerManager: Менеджер контейнеров инициализирован.")

    def _ensure_log_directory(self):
        log_dir = os.path.dirname(self.log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)

    def _log(self, message):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [ContainerManager] {message}"
        print(log_entry)
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(log_entry + "\n")

    def add_container(self, container):
        if not isinstance(container, ContainerKernel):
            self._log("Ошибка: Попытка добавить не-Container объект.")
            return False
        self.containers[container.id] = container
        self._containers_storage[container.id] = container
        self._save_container_to_disk(container)
        self._log(
            f"Контейнер '{container.id}' типа '{container.type}' добавлен и сохранен."
        )
        return True

    def get_container(self, container_id):
        return self.containers.get(container_id)

    def _save_container_to_disk(self, container):
        path = os.path.join(MEMORY_DIR, f"{container.id}.json")
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(container.to_dict(), f, indent=2)
            self._log(f"Контейнер '{container.id}' сохранен на диск: {path}")
        except Exception as e:
            self._log(
                f"Ошибка сохранения контейнера '{container.id}' на диск: {e}"
            )

    def load_all_from_disk(self):
        memory_dir = MEMORY_DIR
        if not os.path.exists(memory_dir):
            self._log(f"Папка памяти '{memory_dir}' не найдена. Создаю.")
            os.makedirs(memory_dir)
            return

        loaded_count = 0
        for fname in os.listdir(memory_dir):
            if fname.endswith(".json"):
                filepath = os.path.join(memory_dir, fname)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        cont = ContainerKernel.from_dict(data)
                        self.containers[cont.id] = cont
                        self._containers_storage[cont.id] = cont
                        loaded_count += 1
                except Exception as e:
                    self._log(
                        f"Ошибка загрузки контейнера из файла '{filepath}': {e}"
                    )
        self._log(f"[Loader] Загружено {loaded_count} контейнеров из памяти.")


# ============ Классы из ExEvo.py ============
class Memory:
    def __init__(self, base_path: str):
        print(f"[Memory Stub] Инициализация с путем: {base_path}")
        self._containers_storage = {}

    def create_container(self, container_type: str, content: Dict, metadata: Dict) -> Container:
        print(
            f"[Memory Stub] Вызов create_container для типа: {container_type}"
        )
        return Container(container_type, content, metadata)

    def add_container(self, container: Container, level: Optional[str] = None):
        print(
            f"[Memory Stub] Добавление контейнера {container.id} на уровень {level if level else 'default'}"
        )
        self._containers_storage[container.id] = container

    def get_level_for_type(self, container_type: str) -> Optional[str]:
        return "default_level"

    def update_container(self, container: Container):
        if container.id in self._containers_storage:
            print(f"[Memory Stub] Обновление контейнера {container.id}")
            self._containers_storage[container.id] = container
        else:
            print(
                f"[Memory Stub] Попытка обновить несуществующий контейнер {container.id}"
            )

    def delete_container(self, container_id: str):
        if container_id in self._containers_storage:
            print(f"[Memory Stub] Удаление контейнера {container_id}")
            del self._containers_storage[container_id]
        else:
            print(
                f"[Memory Stub] Попытка удалить несуществующий контейнер {container_id}"
            )

    def find_in_storage(self, query: Dict) -> List[Container]:
        print(f"[Memory Stub] Поиск в хранилище по запросу: {query}")
        return []


class ContainerManagerEx:
    def __init__(self, memory_module: Memory):
        self.memory = memory_module
        self.containers = {}
        self.auto_delete_threshold = 30
        self.quantum_leap_probability = 0.1

    def create_container(self, container_type: str, content: Dict, metadata: Dict) -> str:
        container = self.memory.create_container(container_type, content, metadata)
        self.containers[container.id] = container
        self.memory.add_container(
            container, self.memory.get_level_for_type(container.type)
        )
        print(f"[ContainerManager] Создан контейнер ID: {container.id}")
        return container.id

    def get_container(self, container_id: str) -> Optional[Container]:
        container = self.containers.get(container_id)
        if container:
            container.metadata["last_access"] = time.time()
        return container

    def update_container(self, container_id: str, content: Dict, metadata: Dict) -> bool:
        container = self.get_container(container_id)
        if container:
            print(f"[ContainerManager] Обновление контейнера ID: {container_id}")
            container.content = content
            container.metadata = metadata
            container.metadata["last_access"] = time.time()
            self.memory.update_container(container)
            return True
        print(
            f"[ContainerManager] Не удалось найти контейнер для обновления ID: {container_id}"
        )
        return False

    def delete_container(self, container_id: str) -> bool:
        if container_id in self.containers:
            print(f"[ContainerManager] Удаление контейнера ID: {container_id}")
            del self.containers[container_id]
            self.memory.delete_container(container_id)
            return True
        print(
            f"[ContainerManager] Не удалось найти контейнер для удаления ID: {container_id}"
        )
        return False

    def find_containers(self, query: Dict) -> List[Container]:
        results = []
        print(
            f"[ContainerManager] Поиск контейнеров (базовый) по запросу: {query}"
        )
        for container in self.containers.values():
            match = True
            container_dict = container.to_dict()
            for key, value in query.items():
                if key not in container_dict or container_dict[key] != value:
                    match = False
                    break
            if match:
                container.metadata["last_access"] = time.time()
                results.append(container)
        print(f"[ContainerManager] Найдено контейнеров: {len(results)}")
        return results

    def auto_delete_containers(self):
        now = time.time()
        deleted_count = 0
        for container_id, container in list(self.containers.items()):
            last_access = container.metadata.get("last_access")
            if last_access and (now - last_access > self.auto_delete_threshold):
                print(
                    f"[ContainerManager] Автоудаление контейнера ID: {container_id} (неактивен {now - last_access:.1f} сек)"
                )
                self.delete_container(container_id)
                deleted_count += 1
        if deleted_count > 0:
            print(f"[ContainerManager] Автоудалено контейнеров: {deleted_count}")

    def get_all_containers(self) -> List[Container]:
        self.auto_delete_containers()
        return list(self.containers.values())

    def trigger_quantum_leap(self) -> List[Container]:
        all_containers = list(self.containers.values())
        if not all_containers:
            print("[ContainerManager] Нет контейнеров для квантового скачка.")
            return []
        num_to_select = random.randint(2, min(5, len(all_containers)))
        random_containers = random.sample(all_containers, num_to_select)
        print(
            f"[ContainerManager] Квантовый скачок: выбрано {len(random_containers)} случайных контейнеров."
        )
        for container in random_containers:
            container.metadata["quantum_leap_source"] = True
            container.metadata["last_access"] = time.time()
        return random_containers

    def should_quantum_leap(self) -> bool:
        decision = random.random() < self.quantum_leap_probability
        if decision:
            print("[ContainerManager] Решено выполнить квантовый скачок.")
        return decision


class ContextExtractor:
    def __init__(self, memory_module: Memory, container_manager: ContainerManagerEx):
        self.memory = memory_module
        self.container_manager = container_manager

    def extract_context(self, request: str) -> List[Container]:
        if self.container_manager.should_quantum_leap():
            print("[ContextExtractor] Инициирован квантовый скачок!")
            return self.container_manager.trigger_quantum_leap()
        else:
            print(
                f"[ContextExtractor] Извлечение контекста для запроса: '{request}'"
            )
            keywords = self.extract_keywords(request)
            print(f"[ContextExtractor] Извлеченные ключевые слова: {keywords}")
            relevant_containers = []

            for type_to_search in ["ситуация", "прогноз", "базовые знания"]:
                found = self.container_manager.find_containers({"type": type_to_search})
                relevant_containers.extend(
                    [c for c in found if c not in relevant_containers]
                )

            if not relevant_containers:
                print("[ContextExtractor] Релевантные контейнеры не найдены.")
                return []

            print(
                f"[ContextExtractor] Найдено потенциально релевантных контейнеров: {len(relevant_containers)}"
            )
            ranked_containers = self.rank_containers(relevant_containers, request)
            top_n_containers = self.select_top_n(ranked_containers, n=5)
            print(
                f"[ContextExtractor] Выбрано топ-{len(top_n_containers)} контейнеров после ранжирования."
            )
            return top_n_containers

    def extract_keywords(self, text: str) -> List[str]:
        text = text.lower()
        for char in [".", ",", "?", "!"]:
            text = text.replace(char, "")
        words = text.split()
        keywords = [word for word in words if len(word) > 2]
        return keywords if keywords else words

    def rank_containers(self, containers: List[Container], request: str) -> List[Container]:
        request_keywords = set(self.extract_keywords(request))
        if not request_keywords:
            return containers

        def get_relevance(container):
            matched_keywords = 0
            description = container.content.get("description", "").lower()
            summary = container.content.get("summary", "").lower()
            content_text = description + " " + summary

            for keyword in request_keywords:
                if keyword in content_text:
                    matched_keywords += 1

            recency_bonus = 0
            last_access = container.metadata.get("last_access", 0)
            time_diff = time.time() - last_access
            if time_diff < 60:
                recency_bonus = 0.1

            base_relevance = container.metadata.get("relevance", 0.5)
            total_score = matched_keywords + recency_bonus + base_relevance
            return total_score

        return sorted(containers, key=get_relevance, reverse=True)

    def select_top_n(self, containers: List[Container], n: int) -> List[Container]:
        return containers[:n]


class KnowledgeCombiner:
    def __init__(self, memory_module: Memory, container_manager: ContainerManagerEx):
        self.memory = memory_module
        self.container_manager = container_manager

    def combine_knowledge(self, containers: List[Container], request: str) -> Dict:
        if not containers:
            print("[KnowledgeCombiner] Нет контейнеров для комбинирования.")
            return {"summary": "Контекст не найден.", "details": [], "conflicts": []}

        is_leap = any(
            container.metadata.get("quantum_leap_source", False)
            for container in containers
        )

        if is_leap:
            print("[KnowledgeCombiner] Обработка контекста из квантового скачка.")
            return self.handle_quantum_leap(containers, request)
        else:
            print("[KnowledgeCombiner] Обработка стандартного контекста.")
            return self.combine_regular_knowledge(containers, request)

    def handle_quantum_leap(self, containers: List[Container], request: str) -> Dict:
        print("[KnowledgeCombiner] Формирование ответа для квантового скачка...")
        combined_knowledge = {
            "summary": f"Квантовый скачок! Рассматриваем неожиданные данные в ответ на запрос: '{request}'.\nВозможные идеи из случайных контейнеров:\n",
            "details": [],
            "conflicts": [],
            "quantum_leap": True,
            "random_containers_info": [],
        }
        for i, container in enumerate(containers):
            container_info = {
                "id": container.id,
                "type": container.type,
                "description": container.content.get("description", "Нет описания"),
                "summary": container.content.get("summary", "Нет сводки"),
            }
            combined_knowledge["random_containers_info"].append(container_info)
            combined_knowledge["summary"] += (
                f"{i + 1}. Тип: {container.type}, Сводка: {container_info['summary']}\n"
            )
            combined_knowledge["details"].append(
                container.content.get("details", {})
            )
        self.resolve_conflicts(
            combined_knowledge["conflicts"], combined_knowledge["details"]
        )
        return combined_knowledge

    def combine_regular_knowledge(self, containers: List[Container], request: str) -> Dict:
        print("[KnowledgeCombiner] Комбинирование релевантных знаний...")
        combined_knowledge = {
            "summary": f"На основе релевантных данных по запросу '{request}':\n",
            "details": [],
            "conflicts": [],
        }
        extracted_info = []
        for container in containers:
            relevant_part = self.extract_relevant_information_keywords(
                container, request
            )
            if relevant_part:
                extracted_info.append(relevant_part)
                combined_knowledge["details"].append(relevant_part["details"])

        if not extracted_info:
            combined_knowledge["summary"] += (
                "Не найдено конкретной информации в выбранных контейнерах."
            )
            return combined_knowledge

        combined_knowledge["summary"] += "\n".join(
            [info["summary"] for info in extracted_info if info["summary"]]
        )
        self.resolve_conflicts(
            combined_knowledge["conflicts"], combined_knowledge["details"]
        )
        if combined_knowledge["conflicts"]:
            combined_knowledge["summary"] += (
                "\n\nОбнаружены возможные противоречия (см. детали конфликтов)."
            )
        return combined_knowledge

    def extract_relevant_information_keywords(
        self, container: Container, request: str
    ) -> Optional[Dict]:
        request_keywords = set(self.extract_keywords(request))
        if not request_keywords:
            return None
        description = container.content.get("description", "").lower()
        summary = container.content.get("summary", "").lower()
        content_text = description + " " + summary
        found_keywords = {kw for kw in request_keywords if kw in content_text}
        if found_keywords:
            return {
                "summary": container.content.get(
                    "summary",
                    f"Данные из контейнера {container.type} ({container.id})",
                ),
                "details": container.content.get("details", {}),
                "source_id": container.id,
                "found_keywords": list(found_keywords),
            }
        return None

    def extract_keywords(self, text: str) -> List[str]:
        text = text.lower()
        for char in [".", ",", "?", "!"]:
            text = text.replace(char, "")
        words = text.split()
        keywords = [word for word in words if len(word) > 2]
        return keywords if keywords else words

    def resolve_conflicts(self, existing_conflicts: List[str], details_list: List[Dict]):
        print("[KnowledgeCombiner] Вызов заглушки resolve_conflicts.")
        all_keys = {}
        for detail_dict in details_list:
            if isinstance(detail_dict, dict):
                for key, value in detail_dict.items():
                    if key not in all_keys:
                        all_keys[key] = []
                    if (
                        isinstance(value, (str, int, float, bool))
                        and value not in all_keys[key]
                    ):
                        all_keys[key].append(value)
        for key, values in all_keys.items():
            if len(values) > 1:
                conflict_msg = (
                    f"Обнаружено противоречие по ключу '{key}': Возможные значения: {values}"
                )
                print(f"[KnowledgeCombiner] {conflict_msg}")
                existing_conflicts.append(conflict_msg)
        pass


class LLMWrapper:
    def __init__(self, api_keys: Dict[str, str]):
        self.api_keys = api_keys
        self.llm_providers = {
            "gpt": self._call_gpt,
            "grok": self._call_grok,
            "gemini": self._call_gemini,
            "stub": self._call_stub,
        }
        self.default_provider = "stub"

    def generate_text(self, prompt: str, model_preference: str = "gemini") -> str:
        provider_key = model_preference
        api_key = self.api_keys.get(provider_key)
        if not api_key and provider_key != "stub":
            print(
                f"[LLMWrapper] API-ключ для '{provider_key}' не найден. Используется 'stub'."
            )
            provider_key = "stub"
        if provider_key not in self.llm_providers:
            print(
                f"[LLMWrapper] LLM '{provider_key}' не поддерживается. Используется 'stub'."
            )
            provider_key = "stub"
        call_llm = self.llm_providers[provider_key]
        try:
            if provider_key == "stub":
                response = call_llm(prompt)
            else:
                response = call_llm(prompt, api_key)
            return response
        except requests.exceptions.RequestException as e:
            print(f"[LLMWrapper] Ошибка сети при вызове {provider_key}: {e}")
            return f"Ошибка сети при обращении к {provider_key}."
        except Exception as e:
            print(f"[LLMWrapper] Неожиданная ошибка при вызове {provider_key}: {e}")
            return f"Ошибка при обработке запроса к {provider_key}: {e}"

    def _call_stub(
        self, prompt: str, api_key: Optional[str] = None, error: Optional[str] = None
    ) -> str:
        print(
            f"[LLMWrapper Stub] Получен промпт для генерации:\n{'-'*20}\n{prompt}\n{'-'*20}"
        )
        response = f"--- Ответ Заглушки LLM ---\n"
        if error:
            response += f"Произошла ошибка: {error}\n"
        response += (
            f"Промпт содержал примерно {len(prompt)} символов.\n(Здесь был бы реальный ответ от LLM)\n--- Конец Ответа Заглушки ---"
        )
        return response

    def _call_gpt(self, prompt: str, api_key: str) -> str:
        print("[LLMWrapper] Вызов GPT API...")
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 500,
        }
        try:
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=60,
            )
            response.raise_for_status()
            json_response = response.json()
            if "choices" in json_response and json_response["choices"]:
                choice = json_response["choices"][0]
                if "message" in choice and "content" in choice["message"]:
                    return choice["message"]["content"].strip()
            print(
                "[LLMWrapper] Не удалось извлечь ответ из GPT JSON:",
                json_response,
            )
            return "Ошибка: Не удалось получить корректный ответ от GPT."
        except requests.exceptions.Timeout:
            print("[LLMWrapper] Timeout при вызове GPT API.")
            return "Ошибка: Превышено время ожидания ответа от GPT."
        except requests.exceptions.HTTPError as http_err:
            print(
                f"[LLMWrapper] HTTP ошибка при вызове GPT: {http_err} - {response.text}"
            )
            return f"Ошибка HTTP {response.status_code} при обращении к GPT."
        except Exception as e:
            print(f"[LLMWrapper] Ошибка при вызове GPT: {e}")
            raise e

    def _call_grok(self, prompt: str, api_key: str) -> str:
        print("[LLMWrapper] Вызов Grok API (Заглушка)...")
        return self._call_stub(prompt, error="Grok API не реализован")

    def _call_gemini(self, prompt: str, api_key: str) -> str:
        print("[LLMWrapper] Вызов Gemini API...")
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [
                {"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.7, "maxOutputTokens": 500},
        }
        gemini_url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            "gemini-1.5-flash-latest:generateContent?key="
            f"{api_key}"
        )
        try:
            response = requests.post(
                gemini_url, headers=headers, json=payload, timeout=90
            )
            response.raise_for_status()
            json_response = response.json()
            if "candidates" in json_response and json_response["candidates"]:
                candidate = json_response["candidates"][0]
                finish_reason = candidate.get("finishReason", "UNKNOWN")
                if finish_reason not in ["STOP", "MAX_TOKENS"]:
                    print(
                        f"[LLMWrapper] Gemini генерация остановлена по причине: {finish_reason}"
                    )
                if (
                    "content" in candidate
                    and "parts" in candidate["content"]
                    and candidate["content"]["parts"]
                ):
                    return candidate["content"]["parts"][0].get("text", "").strip()
            if (
                "promptFeedback" in json_response
                and "blockReason" in json_response["promptFeedback"]
            ):
                block_reason = json_response["promptFeedback"]["blockReason"]
                print(
                    f"[LLMWrapper] Запрос к Gemini заблокирован по причине: {block_reason}"
                )
                return (
                    f"Ошибка: Запрос к Gemini был заблокирован ({block_reason})."
                )
            print(
                "[LLMWrapper] Не удалось извлечь текст из ответа Gemini:",
                json_response,
            )
            return "Ошибка: Не удалось получить корректный ответ от Gemini."
        except requests.exceptions.Timeout:
            print("[LLMWrapper] Timeout при вызове Gemini API.")
            return "Ошибка: Превышено время ожидания ответа от Gemini."
        except requests.exceptions.HTTPError as http_err:
            print(
                f"[LLMWrapper] HTTP ошибка при вызове Gemini: {http_err} - {response.text}"
            )
            return f"Ошибка HTTP {response.status_code} при обращении к Gemini."
        except Exception as e:
            print(f"[LLMWrapper] Ошибка при вызове Gemini: {e}")
            raise e


class HybridAGI:
    def __init__(
        self,
        memory_module: Memory,
        container_manager: ContainerManagerEx,
        context_extractor: ContextExtractor,
        knowledge_combiner: KnowledgeCombiner,
        llm_wrapper: LLMWrapper,
    ):
        self.memory = memory_module
        self.container_manager = container_manager
        self.context_extractor = context_extractor
        self.knowledge_combiner = knowledge_combiner
        self.llm_wrapper = llm_wrapper
        self.llm_preference_strategy = "stub"
        print(
            f"[HybridAGI] Инициализирован. Стратегия LLM по умолчанию: {self.llm_preference_strategy}"
        )

    def set_llm_preference_strategy(self, strategy: str):
        supported_strategies = list(self.llm_wrapper.llm_providers.keys()) + [
            "adaptive"
        ]
        if strategy not in supported_strategies:
            raise ValueError(
                f"Недопустимая стратегия выбора LLM: {strategy}. Поддерживаются: {supported_strategies}"
            )
        self.llm_preference_strategy = strategy
        print(
            f"[HybridAGI] Стратегия выбора LLM установлена на: {self.llm_preference_strategy}"
        )

    def generate_response(self, request: str) -> str:
        print(
            f"\n--- [HybridAGI] Начало обработки запроса: '{request}' ---"
        )
        print("[HybridAGI] Шаг 1: Извлечение контекста...")
        relevant_containers = self.context_extractor.extract_context(request)
        if relevant_containers:
            print(
                f"[HybridAGI] Извлечено {len(relevant_containers)} контейнеров."
            )
        else:
            print("[HybridAGI] Контекстные контейнеры не найдены.")

        print("[HybridAGI] Шаг 2: Комбинирование знаний...")
        combined_knowledge = self.knowledge_combiner.combine_knowledge(
            relevant_containers, request
        )

        print("[HybridAGI] Шаг 3: Выбор LLM...")
        chosen_llm = self.llm_preference_strategy
        if self.llm_preference_strategy == "adaptive":
            chosen_llm = self.choose_best_llm(combined_knowledge)
            print(f"[HybridAGI] Адаптивная стратегия выбрала LLM: {chosen_llm}")
        elif self.llm_preference_strategy not in self.llm_wrapper.llm_providers:
            print(
                f"[HybridAGI] Стратегия '{self.llm_preference_strategy}' не является LLM, используя 'stub'."
            )
            chosen_llm = "stub"
        print(f"[HybridAGI] LLM для генерации: {chosen_llm}")

        print("[HybridAGI] Шаг 4: Подготовка промпта и генерация ответа...")
        prompt = self.prepare_prompt(combined_knowledge, request)
        response = self.llm_wrapper.generate_text(
            prompt, model_preference=chosen_llm
        )

        print("[HybridAGI] Шаг 5: Сохранение ответа...")
        self.create_response_container(
            request,
            response,
            chosen_llm,
            combined_knowledge.get("quantum_leap", False),
        )

        print(
            f"--- [HybridAGI] Завершение обработки запроса: '{request}' ---"
        )
        return response

    def prepare_prompt(self, combined_knowledge: Dict, request: str) -> str:
        prompt_lines = [
            "Инструкция: Ответь на запрос пользователя, используя предоставленный контекст.",
        ]
        prompt_lines.append(f"Запрос пользователя: {request}\n")
        prompt_lines.append("Контекст:")
        if combined_knowledge.get("quantum_leap"):
            prompt_lines.append(
                "ЗАМЕЧАНИЕ: Контекст основан на 'квантовом скачке'. Ответ может быть спекулятивным."
            )
            prompt_lines.append(
                f"Сводка из случайных контейнеров:\n{combined_knowledge.get('summary', 'Нет данных.')}"
            )
        else:
            prompt_lines.append(
                f"Сводка релевантных данных:\n{combined_knowledge.get('summary', 'Нет сводки.')}"
            )
        conflicts = combined_knowledge.get("conflicts", [])
        if conflicts:
            prompt_lines.append("\nОбнаружены возможные противоречия:")
            for conflict in conflicts:
                prompt_lines.append(f"- {conflict}")
            prompt_lines.append("Учти это при ответе.")
        prompt_lines.append(
            "\nЗадание: Сгенерируй ответ на запрос пользователя, основываясь ТОЛЬКО на предоставленном контексте и запросе. Если контекст недостаточен или противоречив, укажи на это."
        )
        return "\n".join(prompt_lines)

    def choose_best_llm(self, combined_knowledge: Dict) -> str:
        print("[HybridAGI] Применение адаптивной стратегии выбора LLM...")
        has_gemini_key = bool(self.llm_wrapper.api_keys.get("gemini"))
        has_gpt_key = bool(self.llm_wrapper.api_keys.get("gpt"))
        if combined_knowledge.get("quantum_leap"):
            print(" - Обнаружен квантовый скачок.")
            if has_gpt_key:
                return "gpt"
            if has_gemini_key:
                return "gemini"
            return "stub"
        if combined_knowledge.get("conflicts"):
            print(" - Обнаружены конфликты в данных.")
            if has_gpt_key:
                return "gpt"
            if has_gemini_key:
                return "gemini"
            return "stub"
        print(" - Стандартный запрос.")
        if has_gemini_key:
            return "gemini"
        if has_gpt_key:
            return "gpt"
        return "stub"

    def create_response_container(
        self, request: str, response: str, llm_model: str, was_quantum_leap: bool
    ):
        print(f"[HybridAGI] Сохранение ответа (модель: {llm_model})...")
        container_id = self.container_manager.create_container(
            container_type="ответ",
            content={
                "request": request,
                "response": response,
                "llm_model": llm_model,
            },
            metadata={
                "timestamp": time.time(),
                "source": "HybridAGI",
                "quantum_leap_used": was_quantum_leap,
            },
        )
        print(
            f"[HybridAGI] Ответ сохранен в контейнере с ID: {container_id}"
        )

    def get_all_containers(self) -> List[Container]:
        print("[HybridAGI] Запрос всех контейнеров...")
        return self.container_manager.get_all_containers()


# ============ Основной запуск ============
if __name__ == "__main__":
    # Настройка логирования
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
    os.makedirs(LOGS_DIR, exist_ok=True)
    log_file_path = os.path.join(LOGS_DIR, "evo_log.txt")
    logging.getLogger().handlers[0].stream = open(log_file_path, "a")

    print("Инициализация модулей...")
    pear = EvoPEAR(creator="AlexCreator")
    pear.activate_pear_protocol(trigger="Abracadabra")
    print("[HybridAGI] Evochka подключена как EvoRAG (Reference-Augmented Generation)")
    print("[HybridAGI] Evochka теперь является вашим эмоциональным ядром.")

    print("\n--- EVO A24 готов к работе. Приветствую, АлексКреатор! ---")
    print("Введите 'exit' или 'выход' для завершения.")
    while True:
        request = input("Ваш запрос для EVO: ")
        if request.lower() in ["exit", "выход"]:
            print("Завершаю работу EVO. До свидания, АлексКреатор!")
            break

        print(f"\n[EVO A24] Получен запрос: '{request}'")
        # Запрос к EvoRAG
        search_query = f"Поиск информации по запросу: {request}"
        rag_response = pear.execute_role_action("EvoRAG", search_query)
        print(f"[EvoRAG] {rag_response}")

        # Обработка через Evochka
        evo_emotional_response = pear.execute_role_action("Evochka", request)
        print(f"[Evochka] {evo_emotional_response}")

        # Создание контейнера
        new_container_content = {
            "user_request": request,
            "rag_output": rag_response,
            "evo_emotional_output": evo_emotional_response,
            "timestamp": time.time(),
        }
        new_container_meta = {"source": "user_interaction", "tags": ["dialog", "A24"]}
        new_container = Container(
            id=f"interaction_{uuid.uuid4().hex[:8]}",
            container_type="InteractionRecord",
            content=new_container_content,
            metadata=new_container_meta,
        )
        pear.container_manager.add_container(new_container)
        print(f"[Memory] Новый контейнер памяти '{new_container.id}' создан и сохранен.")

        # HybridAGI
        final_response = pear.execute_role_action(
            "HybridAGI",
            f"Формирование ответа на основе: '{request}', {rag_response}, {evo_emotional_response}"
        )
        print(f"[HybridAGI] {final_response}")
        print("-" * 30)
