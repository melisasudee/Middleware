import argparse
import json
import statistics
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Dict, List, Tuple

import requests


def build_payload(index: int) -> Dict[str, object]:
    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "transaction_id": f"PERF-{index + 1:06d}",
        "sender_id": f"PERF_{index % 10}",
        "sender_email": f"perf{index}@test.com",
        "transaction_type": "TRANSFER",
        "amount": 1000 + index * 25,
        "currency": "USD",
        "credit_card": "4000-0000-0000-0000",
        "tc_id": "20030040050",
        "error_level": "INFO",
        "message": "Performance test transaction",
        "status": "SUCCESS",
    }


def send_request(target: str, payload: Dict[str, object], timeout: int = 15, api_key: str = "local-api-key") -> Tuple[bool, float]:
    start = time.time()
    try:
        headers = {"X-API-KEY": api_key} if api_key else {}
        response = requests.post(target, json=payload, headers=headers, timeout=timeout)
        response.raise_for_status()
        latency = time.time() - start
        return True, latency
    except Exception:
        return False, time.time() - start


def print_report(name: str, latencies: List[float], success_count: int, failure_count: int):
    total = success_count + failure_count
    print(f"\n{name} sonuçları")
    print("--------------------------")
    print(f"Toplam istek: {total}")
    print(f"Başarılı: {success_count}")
    print(f"Hatalı: {failure_count}")
    if latencies:
        print(f"Min gecikme: {min(latencies):.3f}s")
        print(f"Max gecikme: {max(latencies):.3f}s")
        print(f"Ortalama gecikme: {statistics.mean(latencies):.3f}s")
        print(f"Medyan gecikme: {statistics.median(latencies):.3f}s")
        duration = sum(latencies)
        throughput = success_count / duration if duration > 0 else 0
        print(f"Throughput: {throughput:.2f} req/s")


def run_throughput_test(target: str, count: int, workers: int):
    print(f"Throughput testi başlatılıyor: {count} istek, {workers} işçi")
    latencies: List[float] = []
    success = 0
    failure = 0

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(send_request, target, build_payload(i), 15) for i in range(count)]
        for future in as_completed(futures):
            ok, latency = future.result()
            latencies.append(latency)
            if ok:
                success += 1
            else:
                failure += 1

    print_report("Throughput Testi", latencies, success, failure)


def run_latency_test(target: str, count: int):
    print(f"Latency testi başlatılıyor: {count} ardışık istek")
    latencies: List[float] = []
    success = 0
    failure = 0

    for i in range(count):
        ok, latency = send_request(target, build_payload(i), 15)
        latencies.append(latency)
        if ok:
            success += 1
        else:
            failure += 1

    print_report("Latency Testi", latencies, success, failure)


def run_batch_test(target: str, batch_size: int, batch_count: int):
    print(f"Batch testi başlatılıyor: {batch_count} batch, her biri {batch_size} olay")
    latencies: List[float] = []
    success = 0
    failure = 0

    for batch_index in range(batch_count):
        payloads = [build_payload(batch_index * batch_size + j) for j in range(batch_size)]
        start = time.time()
        try:
            response = requests.post(target.replace("/process", "/batch"), json=payloads, timeout=30)
            response.raise_for_status()
            latency = time.time() - start
            latencies.append(latency)
            success += 1
        except Exception:
            latency = time.time() - start
            latencies.append(latency)
            failure += 1

    print_report("Batch Testi", latencies, success, failure)


def run_stress_test(target: str, levels: List[int]):
    print(f"Stress testi başlatılıyor: seviyeler {levels}")
    for level in levels:
        count = level
        latencies: List[float] = []
        success = 0
        failure = 0
        start = time.time()

        for i in range(count):
            ok, latency = send_request(target, build_payload(i), 15)
            latencies.append(latency)
            if ok:
                success += 1
            else:
                failure += 1

        duration = time.time() - start
        print(f"\nStress seviye {level}: toplam süre {duration:.2f}s")
        print_report(f"Stress Testi {level}", latencies, success, failure)


def create_summary(name: str, latencies: List[float], success_count: int, failure_count: int) -> Dict[str, object]:
    summary: Dict[str, object] = {
        "name": name,
        "total_requests": success_count + failure_count,
        "successful_requests": success_count,
        "failed_requests": failure_count,
    }
    if latencies:
        summary.update({
            "min_latency": min(latencies),
            "max_latency": max(latencies),
            "avg_latency": statistics.mean(latencies),
            "median_latency": statistics.median(latencies),
            "throughput_rps": success_count / sum(latencies) if sum(latencies) > 0 else 0,
        })
    return summary


def run_throughput_test(target: str, count: int, workers: int) -> Dict[str, object]:
    print(f"Throughput testi başlatılıyor: {count} istek, {workers} işçi")
    latencies: List[float] = []
    success = 0
    failure = 0

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(send_request, target, build_payload(i), 15) for i in range(count)]
        for future in as_completed(futures):
            ok, latency = future.result()
            latencies.append(latency)
            if ok:
                success += 1
            else:
                failure += 1

    print_report("Throughput Testi", latencies, success, failure)
    return create_summary("Throughput Testi", latencies, success, failure)


def run_latency_test(target: str, count: int) -> Dict[str, object]:
    print(f"Latency testi başlatılıyor: {count} ardışık istek")
    latencies: List[float] = []
    success = 0
    failure = 0

    for i in range(count):
        ok, latency = send_request(target, build_payload(i), 15)
        latencies.append(latency)
        if ok:
            success += 1
        else:
            failure += 1

    print_report("Latency Testi", latencies, success, failure)
    return create_summary("Latency Testi", latencies, success, failure)


def run_batch_test(target: str, batch_size: int, batch_count: int) -> Dict[str, object]:
    print(f"Batch testi başlatılıyor: {batch_count} batch, her biri {batch_size} olay")
    latencies: List[float] = []
    success = 0
    failure = 0

    for batch_index in range(batch_count):
        payloads = [build_payload(batch_index * batch_size + j) for j in range(batch_size)]
        start = time.time()
        try:
            response = requests.post(target.replace("/process", "/batch"), json=payloads, timeout=30)
            response.raise_for_status()
            latency = time.time() - start
            latencies.append(latency)
            success += 1
        except Exception:
            latency = time.time() - start
            latencies.append(latency)
            failure += 1

    print_report("Batch Testi", latencies, success, failure)
    return create_summary("Batch Testi", latencies, success, failure)


def run_stress_test(target: str, levels: List[int]) -> Dict[str, object]:
    print(f"Stress testi başlatılıyor: seviyeler {levels}")
    stress_summary: Dict[str, object] = {"name": "Stress Testi", "levels": []}

    for level in levels:
        latencies: List[float] = []
        success = 0
        failure = 0
        start = time.time()

        for i in range(level):
            ok, latency = send_request(target, build_payload(i), 15)
            latencies.append(latency)
            if ok:
                success += 1
            else:
                failure += 1

        duration = time.time() - start
        print(f"\nStress seviye {level}: toplam süre {duration:.2f}s")
        print_report(f"Stress Testi {level}", latencies, success, failure)
        stress_summary["levels"].append({
            "level": level,
            **create_summary(f"Stress Testi {level}", latencies, success, failure),
            "duration_seconds": duration,
        })

    return stress_summary


def write_report(report: Dict[str, object], filename: str) -> None:
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"Rapor kaydedildi: {filename}")


def select_menu() -> str:
    print("\nPerformans testi menüsü")
    print("1. Latency Test")
    print("2. Throughput Test")
    print("3. Batch Test")
    print("4. Stress Test")
    print("5. Tüm Testleri Çalıştır")
    choice = input("Seçiminiz (1-5): ").strip()
    mapping = {
        "1": "latency",
        "2": "throughput",
        "3": "batch",
        "4": "stress",
        "5": "all",
    }
    return mapping.get(choice, "all")


def interactive_mode(target: str, args: argparse.Namespace):
    choice = select_menu()
    report = {"target": target, "executed_at": datetime.utcnow().isoformat() + "Z", "results": {}}

    if choice in {"latency", "all"}:
        report["results"]["latency"] = run_latency_test(target, args.count)
    if choice in {"throughput", "all"}:
        report["results"]["throughput"] = run_throughput_test(target, args.count, args.workers)
    if choice in {"batch", "all"}:
        report["results"]["batch"] = run_batch_test(target, args.batch_size, args.batch_count)
    if choice in {"stress", "all"}:
        report["results"]["stress"] = run_stress_test(target, args.stress_levels)

    if args.save_report:
        filename = args.save_report
    else:
        filename = f"performance_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    write_report(report, filename)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Middleware performans testi.")
    parser.add_argument("--target", default="http://localhost:5000/process", help="Middleware API hedef URL")
    parser.add_argument("--count", type=int, default=50, help="Toplam istek sayısı")
    parser.add_argument("--workers", type=int, default=10, help="Eş zamanlı işçi sayısı")
    parser.add_argument("--batch-size", type=int, default=20, help="Batch boyutu")
    parser.add_argument("--batch-count", type=int, default=5, help="Batch sayısı")
    parser.add_argument("--stress-levels", nargs="*", type=int, default=[25, 50, 100], help="Stress test seviyeleri")
    parser.add_argument("--interactive", action="store_true", help="Menü tabanlı interaktif test çalıştır")
    parser.add_argument("--save-report", help="JSON rapor dosya adı")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    print(f"Performans testi başlatılıyor: target={args.target}")
    if args.interactive:
        interactive_mode(args.target, args)
    else:
        report = {
            "target": args.target,
            "executed_at": datetime.utcnow().isoformat() + "Z",
            "results": {
                "latency": run_latency_test(args.target, args.count),
                "throughput": run_throughput_test(args.target, args.count, args.workers),
                "batch": run_batch_test(args.target, args.batch_size, args.batch_count),
                "stress": run_stress_test(args.target, args.stress_levels),
            },
        }
        filename = args.save_report if args.save_report else f"performance_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        write_report(report, filename)
