"""Master Live Ingestion Validation, Stress Testing, and Benchmarking Suite."""

import os
import sys
import time
import json
import numpy as np
from datetime import datetime, timezone

# Ensure src is discoverable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from spectraguard_core_infra.ingestion.enums import SourceType, SourceState
from spectraguard_core_infra.ingestion.models import SourceConfig
from spectraguard_core_infra.ingestion.base import FrameSource
from spectraguard_core_infra.ingestion.scheduler import FrameScheduler
from spectraguard_core_infra.ingestion.supervisor import IngestionSupervisor


class BenchmarkSource(FrameSource):
    """High-speed synthetic source for maximizing pipeline throughput tests."""

    def __init__(self, config: SourceConfig):
        super().__init__(config)
        self.frame_data = np.zeros((1080, 1920, 3), dtype=np.uint8)
        self.frame_count = 0

    def connect(self):
        self._state = SourceState.STREAMING

    def disconnect(self):
        self._state = SourceState.STOPPED

    def read_frame(self):
        if self._state != SourceState.STREAMING:
            return False, None, 0
        self.frame_count += 1
        return True, self.frame_data, time.time_ns()


def run_ingestion_benchmark() -> dict:
    print("\n[BENCHMARK] Executing Live Ingestion Pipeline Stress Test (1080p)...")

    # Configure for maximum throughput using a high valid FPS bound (e.g., 1000 FPS)
    config = SourceConfig(
        source_id="BENCHMARK_SRC",
        source_type=SourceType.SIMULATOR,
        uri="benchmark://stream",
        target_fps=1000.0,  # Pass strict validation while maxing out throughput
    )

    def factory():
        return FrameScheduler(BenchmarkSource(config), max_queue_size=100)

    supervisor = IngestionSupervisor(factory, check_interval_s=0.5)

    # Start pipeline
    supervisor.start()
    time.sleep(0.5)  # Warmup

    test_duration_s = 3.0
    start_time = time.perf_counter()
    frames_acquired = 0

    # Stress test extraction loop
    while (time.perf_counter() - start_time) < test_duration_s:
        success, frame, ts = supervisor.get_next_frame(timeout=0.1)
        if success:
            frames_acquired += 1

    total_time = time.perf_counter() - start_time
    throughput_fps = frames_acquired / total_time

    metrics = supervisor.get_metrics()
    supervisor.stop()

    print(
        f"BENCHMARK RESULT: Total Frames = {frames_acquired} | Throughput = {throughput_fps:.2f} FPS"
    )
    print(
        f"PIPELINE METRICS: Processed = {metrics['frames_processed']} | Dropped = {metrics['frames_dropped']}"
    )

    return {
        "duration_seconds": float(f"{total_time:.4f}"),
        "frames_acquired_by_consumer": frames_acquired,
        "frames_processed_by_source": metrics["frames_processed"],
        "frames_dropped_by_queue": metrics["frames_dropped"],
        "throughput_fps": float(f"{throughput_fps:.2f}"),
        "final_source_state": metrics["source_state"],
    }


def main():
    print("================================================================")
    print(" SPECTRAGUARD PHASE 5: LIVE INGESTION VALIDATION & BENCHMARKING ")
    print("================================================================")

    try:
        bench_results = run_ingestion_benchmark()
        status = (
            "PASS" if bench_results["throughput_fps"] > 30.0 else "FAIL_PERFORMANCE"
        )
    except Exception as e:
        print(f"\n[ERROR] Ingestion validation failed: {str(e)}")
        bench_results = {"error": str(e)}
        status = "FAIL_EXECUTION"

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "phase": "PHASE 5",
        "subsystem": "spectraguard-core-infra-ingestion",
        "benchmarks": bench_results,
        "overall_status": "READY" if status == "PASS" else status,
    }

    report_path = os.path.normpath("data/reports/ingestion_validation_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"\nReport successfully generated at: {report_path}")
    print("================================================================")

    if report["overall_status"] == "READY":
        print("PHASE 5 STATUS: PASSED. Live Ingestion System READY for Phase 6.")
        sys.exit(0)
    else:
        print(
            f"PHASE 5 STATUS: FAILED ({status}). Performance or execution errors detected."
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
