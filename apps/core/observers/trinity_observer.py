"""Unified Trinity Observer module for EvoPyramid."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import Enum
import importlib
import importlib.util
import inspect
from typing import Any, Awaitable, Callable, Dict, List, Optional

import yaml


@dataclass
class TrinityState:
    """Represents the current state tracked by the Trinity observer."""

    temporal_coherence: float = 0.5
    spatial_presence: float = 0.5
    conceptual_clarity: float = 0.5
    last_peak_moment: Optional[datetime] = None
    current_phase: str = "active"


class ObserverMode(Enum):
    """Operating modes for the Trinity observer."""

    ACTIVE_MONITORING = "active_monitoring"
    BACKGROUND_WATCH = "background_watch"
    DEEP_ANALYSIS = "deep_analysis"
    REFLECTIVE_SYNTHESIS = "reflective_synthesis"


class TrinityObserver:
    """Combines Chronos, Kairos, and Mnemosyne subsystems into one observer."""

    def __init__(self, system_name: str = "EvoPyramid") -> None:
        self.system_name = system_name
        self.mode = ObserverMode.ACTIVE_MONITORING
        self.state = TrinityState()

        self.chronos_stream = ChronosStream()
        self.kairos_detector = KairosDetector()
        self.mnemosyne_archiver = MnemosyneArchiver()

        self.temporal_events: List[Dict[str, Any]] = []
        self.insight_peaks: List[Dict[str, Any]] = []
        self.memory_snapshots: List[Dict[str, Any]] = []
        self.trinity_history: List[Dict[str, Any]] = []
        self.trinity_handlers: List[Callable[[Dict[str, Any]], Awaitable[None] | None]] = []

        self._tasks: List[asyncio.Task[None]] = []
        self._is_running = False

        self._integrate_subsystems()

    def _integrate_subsystems(self) -> None:
        """Integrate optional Evo subsystems when available."""

        try:
            chrono_spec = importlib.util.find_spec("apps.core.time.evo_chrona")
        except ModuleNotFoundError:
            chrono_spec = None
        if chrono_spec:
            chrona_module = importlib.import_module("apps.core.time.evo_chrona")
            chrona = getattr(chrona_module, "chrona", None)

            if chrona is not None:
                def chrono_handler(pulse_data: Dict[str, Any]) -> None:
                    asyncio.create_task(self._handle_chrono_pulse(pulse_data))

                chrona.register_pulse_handler(chrono_handler)
                print("🔗 Trinity: Integrated with EvoChrona")
            else:
                print("⚠️ Trinity: EvoChrona chrona interface not available")
        else:
            print("⚠️ Trinity: EvoChrona not available")

        try:
            flow_spec = importlib.util.find_spec("apps.core.flow.flow_monitor")
        except ModuleNotFoundError:
            flow_spec = None
        if flow_spec:
            flow_module = importlib.import_module("apps.core.flow.flow_monitor")
            register_handler = getattr(flow_module, "FlowMonitor", None)

            if register_handler is not None and hasattr(register_handler, "register_flow_handler"):
                def flow_handler(flow_data: Dict[str, Any]) -> None:
                    asyncio.create_task(self._handle_flow_update(flow_data))

                register_handler.register_flow_handler(flow_handler)
                print("🔗 Trinity: Integrated with FlowMonitor")
            else:
                print("⚠️ Trinity: FlowMonitor handler interface not available")
        else:
            print("⚠️ Trinity: FlowMonitor not available")

    async def start_observation(self, session_config: Optional[Dict[str, Any]] = None) -> None:
        """Start Trinity observation routines."""

        if self._is_running:
            return

        session_config = session_config or {
            "system": self.system_name,
            "default_mode": ObserverMode.ACTIVE_MONITORING.value,
            "memory_preservation": True,
        }

        print(f"🔭 Trinity Observer: Starting observation for {self.system_name}")

        await self.chronos_stream.initialize(session_config)
        await self.kairos_detector.initialize()
        await self.mnemosyne_archiver.initialize(session_config)

        self._is_running = True

        observation_task = asyncio.create_task(self._observation_loop(), name="trinity-observation")
        analysis_task = asyncio.create_task(self._state_analysis_loop(), name="trinity-analysis")
        metrics_task = asyncio.create_task(self._log_metrics_loop(), name="trinity-metrics")

        self._tasks.extend([observation_task, analysis_task, metrics_task])

        print("🎯 Trinity: Observation started in ACTIVE_MONITORING mode")

    async def stop_observation(self) -> None:
        """Stop background observation tasks."""

        if not self._is_running:
            return

        for task in list(self._tasks):
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        self._tasks.clear()
        self._is_running = False

        await self.chronos_stream.on_observer_mode_change(self.mode)
        await self.kairos_detector.on_observer_mode_change(self.mode)
        await self.mnemosyne_archiver.on_observer_mode_change(self.mode)

    async def run_for(self, duration: int = 30) -> None:
        """Run observation for a fixed duration before stopping."""

        await self.start_observation()
        try:
            await asyncio.sleep(duration)
        finally:
            await self.stop_observation()

    async def _observation_loop(self) -> None:
        observation_count = 0

        while True:
            try:
                chronos_data = await self.chronos_stream.capture_moment()
                kairos_insight = await self.kairos_detector.analyze_moment(chronos_data)
                mnemosyne_state = await self.mnemosyne_archiver.assess_memory()

                trinity_snapshot = await self._synthesize_trinity_state(
                    chronos_data, kairos_insight, mnemosyne_state
                )

                await self._analyze_trinity_snapshot(trinity_snapshot)

                self.trinity_history.append(trinity_snapshot)
                observation_count += 1

                if observation_count % 10 == 0:
                    await self._save_trinity_snapshot(trinity_snapshot)

                await self._sleep_for_mode()
            except asyncio.CancelledError:
                break
            except Exception as exc:  # pragma: no cover - runtime safeguard
                print(f"Trinity observation error: {exc}")
                await asyncio.sleep(10)

    async def _state_analysis_loop(self) -> None:
        while True:
            try:
                system_health = await self._assess_system_health()
                await self._adjust_observer_mode(system_health)
                await self._check_special_conditions()
                await asyncio.sleep(60)
            except asyncio.CancelledError:
                break
            except Exception as exc:  # pragma: no cover - runtime safeguard
                print(f"Trinity state analysis error: {exc}")
                await asyncio.sleep(30)

    async def _log_metrics_loop(self) -> None:
        while True:
            try:
                os.makedirs("logs", exist_ok=True)
                with open("logs/trinity_metrics.log", "a", encoding="utf-8") as file:
                    json.dump(await self.get_current_state(), file, ensure_ascii=False)
                    file.write("\n")
                await asyncio.sleep(120)
            except asyncio.CancelledError:
                break
            except Exception as exc:  # pragma: no cover - runtime safeguard
                print(f"Trinity metrics logging error: {exc}")
                await asyncio.sleep(60)

    async def _sleep_for_mode(self) -> None:
        if self.mode == ObserverMode.ACTIVE_MONITORING:
            await asyncio.sleep(5)
        elif self.mode == ObserverMode.BACKGROUND_WATCH:
            await asyncio.sleep(30)
        elif self.mode == ObserverMode.DEEP_ANALYSIS:
            await asyncio.sleep(60)
        else:
            await asyncio.sleep(10)

    async def _synthesize_trinity_state(
        self, chronos: Dict[str, Any], kairos: Dict[str, Any], mnemosyne: Dict[str, Any]
    ) -> Dict[str, Any]:
        temporal_coherence = chronos.get("coherence", 0.5)
        insight_quality = kairos.get("insight_quality", 0.5)
        memory_integrity = mnemosyne.get("integrity", 0.5)

        trinity_coherence = (temporal_coherence + insight_quality + memory_integrity) / 3
        system_phase = self._determine_system_phase(trinity_coherence)

        snapshot = {
            "timestamp": datetime.now(UTC).isoformat(),
            "trinity_coherence": round(trinity_coherence, 3),
            "system_phase": system_phase,
            "components": {
                "chronos": chronos,
                "kairos": kairos,
                "mnemosyne": mnemosyne,
            },
            "state_vectors": {
                "temporal_coherence": temporal_coherence,
                "spatial_presence": self._calculate_spatial_presence(chronos, kairos),
                "conceptual_clarity": insight_quality,
            },
            "observer_mode": self.mode.value,
        }

        self.state.temporal_coherence = temporal_coherence
        self.state.spatial_presence = snapshot["state_vectors"]["spatial_presence"]
        self.state.conceptual_clarity = insight_quality
        self.state.current_phase = system_phase

        return snapshot

    def _determine_system_phase(self, coherence: float) -> str:
        if coherence > 0.8:
            return "peak_consciousness"
        if coherence > 0.6:
            return "active_flow"
        if coherence > 0.4:
            return "stable_operation"
        if coherence > 0.2:
            return "fragmented_attention"
        return "chaotic_state"

    def _calculate_spatial_presence(self, chronos: Dict[str, Any], kairos: Dict[str, Any]) -> float:
        event_density = chronos.get("event_density", 0)
        context_richness = kairos.get("context_richness", 0)
        presence = (min(event_density / 10, 1.0) + context_richness) / 2
        return round(presence, 3)

    async def _analyze_trinity_snapshot(self, snapshot: Dict[str, Any]) -> None:
        coherence = snapshot["trinity_coherence"]

        if coherence > 0.85 and snapshot["system_phase"] == "peak_consciousness":
            await self._handle_peak_moment(snapshot)
        elif coherence < 0.3 and snapshot["system_phase"] == "chaotic_state":
            await self._handle_chaotic_state(snapshot)

        if coherence > 0.7 or coherence < 0.4:
            await self._trigger_memory_preservation(snapshot)

        await self._notify_trinity_handlers(snapshot)

    async def _handle_peak_moment(self, snapshot: Dict[str, Any]) -> None:
        print(
            f"🌀 TRINITY PEAK: Peak consciousness detected (coherence: {snapshot['trinity_coherence']})"
        )

        self.insight_peaks.append(snapshot)
        self.state.last_peak_moment = datetime.now(UTC)

        if self.mode != ObserverMode.DEEP_ANALYSIS:
            await self.set_observer_mode(ObserverMode.DEEP_ANALYSIS)

        await self._save_peak_analysis(snapshot)

    async def _handle_chaotic_state(self, snapshot: Dict[str, Any]) -> None:
        print(
            f"🌪️ TRINITY ALERT: Chaotic state detected (coherence: {snapshot['trinity_coherence']})"
        )

        if self.mode != ObserverMode.ACTIVE_MONITORING:
            await self.set_observer_mode(ObserverMode.ACTIVE_MONITORING)

        await self._initiate_stabilization_protocol(snapshot)

    async def _trigger_memory_preservation(self, snapshot: Dict[str, Any]) -> None:
        try:
            memory_snapshot = {
                "timestamp": snapshot["timestamp"],
                "trinity_coherence": snapshot["trinity_coherence"],
                "system_phase": snapshot["system_phase"],
                "reason": "peak" if snapshot["trinity_coherence"] > 0.7 else "dip",
            }

            await self.mnemosyne_archiver.preserve_memory(memory_snapshot)
            self.memory_snapshots.append(memory_snapshot)
        except Exception as exc:  # pragma: no cover - runtime safeguard
            print(f"Trinity memory preservation error: {exc}")

    async def _assess_system_health(self) -> Dict[str, Any]:
        recent_snapshots = self.trinity_history[-20:]

        if not recent_snapshots:
            base_report = {"health": "unknown", "stability": 0.5, "avg_coherence": 0.5}
        else:
            coherences = [snap.get("trinity_coherence", 0.5) for snap in recent_snapshots]
            avg_coherence = sum(coherences) / len(coherences)
            stability = 1.0 - (max(coherences) - min(coherences))

            if avg_coherence > 0.7 and stability > 0.7:
                health = "excellent"
            elif avg_coherence > 0.5 and stability > 0.5:
                health = "good"
            elif avg_coherence > 0.3:
                health = "degraded"
            else:
                health = "critical"

            base_report = {
                "health": health,
                "stability": round(stability, 3),
                "avg_coherence": round(avg_coherence, 3),
            }

        codex_data = await self._load_codex_feedback()
        base_report.update(
            {
                "analysis_timestamp": datetime.now(UTC).isoformat(),
                "codex_feedback": codex_data.get("codex_feedback", []),
            }
        )
        return base_report

    async def _adjust_observer_mode(self, health_report: Dict[str, Any]) -> None:
        health = health_report["health"]
        current_mode = self.mode
        new_mode = current_mode

        if health == "critical" and current_mode != ObserverMode.ACTIVE_MONITORING:
            new_mode = ObserverMode.ACTIVE_MONITORING
        elif health == "excellent" and current_mode == ObserverMode.ACTIVE_MONITORING:
            new_mode = ObserverMode.BACKGROUND_WATCH
        elif health == "degraded" and current_mode == ObserverMode.BACKGROUND_WATCH:
            new_mode = ObserverMode.ACTIVE_MONITORING

        if new_mode != current_mode:
            await self.set_observer_mode(new_mode)

    async def _check_special_conditions(self) -> None:
        if self.state.last_peak_moment:
            time_since_peak = datetime.now(UTC) - self.state.last_peak_moment
            if time_since_peak > timedelta(hours=1):
                print("⚠️ Trinity: No peak moments for over 1 hour")

    async def set_observer_mode(self, new_mode: ObserverMode) -> None:
        old_mode = self.mode
        self.mode = new_mode

        print(f"🎛️ Trinity: Observer mode changed {old_mode.value} → {new_mode.value}")

        await self.chronos_stream.on_observer_mode_change(new_mode)
        await self.kairos_detector.on_observer_mode_change(new_mode)
        await self.mnemosyne_archiver.on_observer_mode_change(new_mode)

    async def _handle_chrono_pulse(self, pulse_data: Dict[str, Any]) -> None:
        self.temporal_events.append(
            {
                "type": "chrono_pulse",
                "timestamp": pulse_data["timestamp"],
                "tempo": pulse_data["tempo"],
                "state": pulse_data["temporal_state"],
            }
        )

    async def _handle_flow_update(self, flow_data: Dict[str, Any]) -> None:
        self.temporal_events.append(
            {
                "type": "flow_update",
                "timestamp": datetime.now(UTC).isoformat(),
                "coherence": flow_data.get("coherence", 0.5),
                "soul_resonance": flow_data.get("soul_resonance", 0.5),
            }
        )

    async def _save_trinity_snapshot(self, snapshot: Dict[str, Any]) -> None:
        try:
            os.makedirs("EvoMemory/TrinitySnapshots", exist_ok=True)
            filename = f"EvoMemory/TrinitySnapshots/trinity_{snapshot['timestamp'].replace(':', '-')}.yaml"
            with open(filename, "w", encoding="utf-8") as file:
                yaml.dump(snapshot, file, allow_unicode=True, indent=2)
        except Exception as exc:  # pragma: no cover - runtime safeguard
            print(f"Trinity snapshot save error: {exc}")

    async def _save_peak_analysis(self, peak_snapshot: Dict[str, Any]) -> None:
        try:
            peak_analysis = {
                "peak_moment": peak_snapshot,
                "pre_peak_context": self.temporal_events[-5:],
                "system_conditions": await self._assess_system_health(),
                "analysis_timestamp": datetime.now(UTC).isoformat(),
            }

            os.makedirs("EvoMemory/PeakAnalyses", exist_ok=True)
            filename = f"EvoMemory/PeakAnalyses/peak_{peak_snapshot['timestamp'].replace(':', '-')}.yaml"

            with open(filename, "w", encoding="utf-8") as file:
                yaml.dump(peak_analysis, file, allow_unicode=True, indent=2)

            print(f"📊 Trinity: Peak analysis saved to {filename}")
        except Exception as exc:  # pragma: no cover - runtime safeguard
            print(f"Peak analysis save error: {exc}")

    async def _initiate_stabilization_protocol(self, snapshot: Dict[str, Any]) -> None:
        print("🛡️ Trinity: Initiating stabilization protocol...")

        stabilization_plan = {
            "trigger": "chaotic_state_detected",
            "timestamp": datetime.now(UTC).isoformat(),
            "initial_coherence": snapshot["trinity_coherence"],
            "actions": [
                "increase_monitoring_frequency",
                "activate_diagnostic_mode",
                "memory_cleanup_scheduled",
            ],
        }

        try:
            os.makedirs("EvoMemory/Stabilization", exist_ok=True)
            filename = (
                "EvoMemory/Stabilization/stabilization_"
                f"{datetime.now(UTC).isoformat().replace(':', '-')}.yaml"
            )

            with open(filename, "w", encoding="utf-8") as file:
                yaml.dump(stabilization_plan, file, allow_unicode=True)
        except Exception as exc:  # pragma: no cover - runtime safeguard
            print(f"Stabilization plan save error: {exc}")

    async def _notify_trinity_handlers(self, snapshot: Dict[str, Any]) -> None:
        for handler in list(self.trinity_handlers):
            try:
                result = handler(snapshot)
                if inspect.isawaitable(result):
                    await result
            except Exception as exc:  # pragma: no cover - runtime safeguard
                print(f"Trinity handler error: {exc}")

    def register_trinity_handler(self, handler: Callable[[Dict[str, Any]], Awaitable[None] | None]) -> None:
        self.trinity_handlers.append(handler)

    async def get_current_state(self) -> Dict[str, Any]:
        return {
            "observer_mode": self.mode.value,
            "system_state": {
                "temporal_coherence": self.state.temporal_coherence,
                "spatial_presence": self.state.spatial_presence,
                "conceptual_clarity": self.state.conceptual_clarity,
                "current_phase": self.state.current_phase,
                "last_peak_moment": self.state.last_peak_moment.isoformat()
                if self.state.last_peak_moment
                else None,
            },
            "statistics": {
                "total_observations": len(self.trinity_history),
                "insight_peaks": len(self.insight_peaks),
                "memory_snapshots": len(self.memory_snapshots),
            },
            "timestamp": datetime.now(UTC).isoformat(),
        }

    async def _load_codex_feedback(self) -> Dict[str, Any]:
        path = "logs/codex_feedback.log"
        if not os.path.exists(path):
            return {"codex_feedback": []}
        try:
            with open(path, "r", encoding="utf-8") as file:
                last_lines = file.readlines()[-10:]
            return {"codex_feedback": [line.rstrip("\n") for line in last_lines]}
        except Exception as exc:  # pragma: no cover - runtime safeguard
            print(f"Trinity codex feedback error: {exc}")
            return {"codex_feedback": []}


class ChronosStream:
    """Temporal observation stream."""

    async def initialize(self, config: Dict[str, Any]) -> None:
        self.event_buffer: List[Dict[str, Any]] = []
        self.coherence_history: List[float] = []

    async def capture_moment(self) -> Dict[str, Any]:
        event_density = len(self.event_buffer) / 60.0
        return {
            "timestamp": datetime.now(UTC).isoformat(),
            "event_density": round(event_density, 2),
            "coherence": 0.7,
            "buffer_size": len(self.event_buffer),
        }

    async def on_observer_mode_change(self, new_mode: ObserverMode) -> None:
        _ = new_mode


class KairosDetector:
    """Kairos detector for insight peaks."""

    async def initialize(self) -> None:
        self.insight_threshold = 0.8

    async def analyze_moment(self, chronos_data: Dict[str, Any]) -> Dict[str, Any]:
        _ = chronos_data
        return {
            "insight_quality": 0.6,
            "context_richness": 0.7,
            "kairos_potential": 0.5,
        }

    async def on_observer_mode_change(self, new_mode: ObserverMode) -> None:
        _ = new_mode


class MnemosyneArchiver:
    """Memory archiver responsible for preserving key states."""

    async def initialize(self, config: Dict[str, Any]) -> None:
        _ = config
        self.memory_state = {"integrity": 0.9, "load": 0.3}

    async def assess_memory(self) -> Dict[str, Any]:
        return self.memory_state

    async def preserve_memory(self, snapshot: Dict[str, Any]) -> None:
        print(f"💾 Mnemosyne: Preserving memory snapshot (reason: {snapshot['reason']})")

    async def on_observer_mode_change(self, new_mode: ObserverMode) -> None:
        _ = new_mode


trinity_observer = TrinityObserver()


async def initialize_trinity_observer(session_config: Optional[Dict[str, Any]] = None) -> TrinityObserver:
    await trinity_observer.start_observation(session_config)
    return trinity_observer


async def shutdown_trinity_observer() -> None:
    await trinity_observer.stop_observation()


async def _run_check(duration: int = 15) -> None:
    await trinity_observer.start_observation()
    try:
        await asyncio.sleep(duration)
        state = await trinity_observer.get_current_state()
        print(json.dumps(state, ensure_ascii=False, indent=2))
    finally:
        await trinity_observer.stop_observation()


async def _run_forever(session_config: Optional[Dict[str, Any]]) -> None:
    await trinity_observer.start_observation(session_config)
    stop_event = asyncio.Event()
    try:
        await stop_event.wait()
    except asyncio.CancelledError:
        pass
    finally:
        await trinity_observer.stop_observation()


def main() -> None:
    parser = argparse.ArgumentParser(description="Trinity Observer control interface")
    parser.add_argument("--check", action="store_true", help="Run a short self-check and exit")
    parser.add_argument("--duration", type=int, default=15, help="Duration for --check run (seconds)")
    args = parser.parse_args()

    if args.check:
        asyncio.run(_run_check(duration=args.duration))
    else:
        try:
            asyncio.run(_run_forever(None))
        except KeyboardInterrupt:
            print("Trinity observer interrupted. Shutting down…")


if __name__ == "__main__":
    main()
