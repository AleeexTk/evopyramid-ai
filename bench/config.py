"""Конфигурация для MultiAgentBench сценариев."""

from __future__ import annotations

from pydantic_settings import BaseSettings


class BenchConfig(BaseSettings):
    """Конфигурация бенчмарков."""

    multiagent_bench_path: str = "./bench/multiagent_bench"
    eval_datasets_path: str = "./bench/datasets"
    coherence_threshold: float = 0.7
    novelty_threshold: float = 0.6

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


__all__ = ["BenchConfig"]
