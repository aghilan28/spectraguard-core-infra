"""Master Infrastructure Validation, Stress Testing, and Benchmarking Suite."""

import os
import sys
import time
import json
import threading
from datetime import datetime, timezone

# Ensure src is discoverable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from spectraguard_core_infra.transport.sync import TransportSync
from spectraguard_core_infra.transport.lifecycle import FrameLifecycleOrchestrator
from spectraguard_core_infra.storage.shared_memory import SharedMemoryManager
from spectraguard_core_infra.contracts.models import FrameIdentifier, FrameMetadata
from spectraguard_core_infra.contracts.enums import FrameStatus


def run_stress_test() -> dict:
    print(
        "\n[STRESS TEST] Executing multi-threaded producer/consumer concurrency stress test..."
    )
    capacity = 16
    slot_size = 1920 * 1080 * 3  # Full 1080p frame allocation block size
    total_size = capacity * slot_size

    sync = TransportSync(capacity=capacity)
    shm_manager = SharedMemoryManager(
        name="sg_stress_test_shm", size=total_size, create=True
    )
    shm_manager.allocate()

    errors = []
    frames_processed = 0
    target_frames = 200

    try:
        orchestrator = FrameLifecycleOrchestrator(sync, shm_manager, slot_size)

        def producer_worker():
            nonlocal errors
            try:
                for i in range(target_frames):
                    slot_idx, write_view = orchestrator.acquire_writable_slot()
                    write_view[0:4] = b"\x01\x02\x03\x04"
                    del write_view

                    ident = FrameIdentifier("CAM_STRESS", "STR_01", i, time.time_ns())
                    meta = FrameMetadata(
                        ident,
                        (1920, 1080),
                        3,
                        "RGB888",
                        4,
                        FrameStatus.READY,
                        "hash",
                        "prod_1",
                    )
                    orchestrator.publish_frame(slot_idx, meta)
            except Exception as e:
                errors.append(f"Producer error: {str(e)}")

        def consumer_worker():
            nonlocal frames_processed, errors
            try:
                while frames_processed < target_frames:
                    slot_idx, read_view = orchestrator.acquire_readable_slot(
                        timeout=1.0
                    )
                    if slot_idx != -1:
                        frames_processed += 1
                        del read_view
                        orchestrator.recycle_slot(slot_idx)
            except Exception as e:
                errors.append(f"Consumer error: {str(e)}")

        start_time = time.perf_counter()
        p_thread = threading.Thread(target=producer_worker)
        c_thread = threading.Thread(target=consumer_worker)

        p_thread.start()
        c_thread.start()

        p_thread.join(timeout=10.0)
        c_thread.join(timeout=10.0)
        duration = time.perf_counter() - start_time

        success = (len(errors) == 0) and (frames_processed > 0)
        print(
            f"STRESS TEST RESULT: {'PASS' if success else 'FAIL'} (Processed {frames_processed} frames in {duration:.4f}s)"
        )

        return {
            "status": "PASS" if success else "FAIL",
            "frames_processed": frames_processed,
            "duration_seconds": duration,
            "errors": errors,
        }
    finally:
        shm_manager.cleanup()


def run_benchmarks() -> dict:
    print(
        "\n[BENCHMARK] Measuring frame transport acquisition and throughput latency..."
    )
    capacity = 8
    slot_size = 1024 * 1024  # 1MB slots
    total_size = capacity * slot_size

    sync = TransportSync(capacity=capacity)
    shm_manager = SharedMemoryManager(name="sg_bench_shm", size=total_size, create=True)
    shm_manager.allocate()

    try:
        orchestrator = FrameLifecycleOrchestrator(sync, shm_manager, slot_size)
        iterations = 1000

        start_time = time.perf_counter()
        for i in range(iterations):
            slot_idx, write_view = orchestrator.acquire_writable_slot()
            write_view[0:10] = b"BENCH_DATA"
            del write_view
            orchestrator.recycle_slot(slot_idx)

        total_time = time.perf_counter() - start_time
        avg_latency_us = (total_time / iterations) * 1_000_000
        throughput_fps = iterations / total_time

        print(
            f"BENCHMARK RESULT: Average Latency = {avg_latency_us:.2f} us/frame | Throughput = {throughput_fps:.2f} FPS"
        )

        return {
            "iterations": iterations,
            "total_time_seconds": total_time,
            "average_latency_microseconds": avg_latency_us,
            "throughput_fps": throughput_fps,
        }
    finally:
        shm_manager.cleanup()


def main():
    print("================================================================")
    print(" SPECTRAGUARD PHASE 3: INFRASTRUCTURE VALIDATION & BENCHMARKING ")
    print("================================================================")

    stress_results = run_stress_test()
    bench_results = run_benchmarks()

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
        "phase": "PHASE 3",
        "subsystem": "spectraguard-core-infra",
        "stress_test": stress_results,
        "benchmarks": bench_results,
        "overall_status": "READY" if stress_results["status"] == "PASS" else "FAILED",
    }

    report_path = os.path.normpath("data/reports/infrastructure_validation_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"\nReport successfully generated at: {report_path}")
    print("================================================================")

    if report["overall_status"] == "READY":
        print("PHASE 3 STATUS: PASSED. Infrastructure layer READY for Phase 4.")
        sys.exit(0)
    else:
        print("PHASE 3 STATUS: FAILED. Concurrency validation errors detected.")
        sys.exit(1)


if __name__ == "__main__":
    main()
