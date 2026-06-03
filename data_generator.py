import argparse
import os
import random
import threading
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests
from flask import Flask, jsonify, request

BASE_TEMPLATES = [
    {
        "sender_id": "BANK_A",
        "sender_email": "kullanici@bank-a.com",
        "transaction_type": "TRANSFER",
        "currency": "USD",
        "credit_card": "4532-1234-5678-9012",
        "tc_id": "12345678901",
        "message": "Kullanıcı para transferi",
    },
    {
        "sender_id": "MARKETPLACE_X",
        "sender_email": "alisveris@marketplace.com",
        "transaction_type": "PAYMENT",
        "currency": "EUR",
        "credit_card": "5400-0000-0000-0000",
        "tc_id": "98765432109",
        "message": "Sipariş ödendi",
    },
    {
        "sender_id": "BANK_B",
        "sender_email": "test@bank-b.com",
        "transaction_type": "REFUND",
        "currency": "USD",
        "credit_card": "4111-1111-1111-1111",
        "tc_id": "11223344556",
        "message": "İade işlemi",
    },
]

SCENARIO_CONFIG = {
    "normal": {"count": 20, "delay": 0.5, "burst": False},
    "high_load": {"count": 80, "delay": 0.1, "burst": False},
    "burst": {"count": 50, "delay": 0.05, "burst": True, "burst_size": 10, "pause": 2},
    "sustained": {"count": 120, "delay": 0.2, "burst": False},
    "extreme": {"count": 200, "delay": 0.05, "burst": False},
}

ERROR_LEVELS = ["INFO", "WARNING", "ERROR", "CRITICAL"]
TRANSACTION_TYPES = ["TRANSFER", "PAYMENT", "REFUND", "WITHDRAWAL"]
CURRENCIES = ["USD", "EUR", "TRY", "GBP", "CHF"]

DEFAULT_TARGET = os.environ.get("TARGET", "http://middleware:5000/api/process")
DEFAULT_SCENARIO = os.environ.get("SCENARIO", "normal")
DEFAULT_COUNT = int(os.environ.get("COUNT", "100"))
DEFAULT_API_KEY = os.environ.get("API_KEY", "")
DEFAULT_HOST = os.environ.get("HOST", "0.0.0.0")
DEFAULT_PORT = int(os.environ.get("PORT", "5001"))
DEFAULT_MODE = os.environ.get("MODE", "run")
DEFAULT_AUTO_GENERATE = os.environ.get("AUTO_GENERATE", "true").lower() in ("1", "true", "yes")
DEFAULT_AUTO_GENERATE_LOOP = os.environ.get("AUTO_GENERATE_LOOP", "false").lower() in ("1", "true", "yes")
DEFAULT_AUTO_GENERATE_DELAY = float(os.environ.get("AUTO_GENERATE_DELAY", "5"))

app = Flask(__name__)


def build_event(template: Dict[str, Any]) -> Dict[str, Any]:
    amount = round(random.uniform(10, 75000), 2)
    event = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "transaction_id": f"TX-{random.randint(100000, 999999)}",
        "sender_id": template["sender_id"],
        "sender_email": template["sender_email"],
        "transaction_type": template["transaction_type"],
        "amount": amount,
        "currency": random.choice(CURRENCIES),
        "credit_card": template["credit_card"],
        "tc_id": template["tc_id"],
        "error_level": random.choice(ERROR_LEVELS),
        "message": template["message"],
        "status": random.choice(["SUCCESS", "PENDING", "FAILED"]),
        "order_id": f"ORD-{random.randint(1000, 9999)}",
    }
    return event


def build_scenario_events(scenario: str, count: Optional[int] = None) -> List[Dict[str, Any]]:
    events: List[Dict[str, Any]] = []
    template = random.choice(BASE_TEMPLATES)
    config = SCENARIO_CONFIG.get(scenario, SCENARIO_CONFIG["normal"]).copy()

    if count is not None:
        config["count"] = count

    for index in range(config["count"]):
        event = build_event(template)
        event["risk_label"] = "low" if event["amount"] < 1000 else "high"
        if scenario == "high_load":
            event["error_level"] = random.choice(["INFO", "WARNING", "ERROR"])
        elif scenario == "burst":
            event["error_level"] = random.choice(["WARNING", "ERROR"])
        elif scenario == "extreme":
            event["amount"] = round(random.uniform(50000, 120000), 2)
            event["risk_label"] = "extreme"
        events.append(event)

    return events


def send_event(url: str, event: Dict[str, Any], api_key: Optional[str] = None) -> Dict[str, Any]:
    headers = {}
    if api_key:
        headers["X-API-KEY"] = api_key

    response = requests.post(url, json=event, headers=headers, timeout=15)
    response.raise_for_status()
    return response.json()


def run_scenario(target: str, scenario: str, count: Optional[int] = None, api_key: Optional[str] = None):
    config = SCENARIO_CONFIG.get(scenario, SCENARIO_CONFIG["normal"]).copy()
    if count is not None:
        config["count"] = count
    api_key = api_key or DEFAULT_API_KEY
    events = build_scenario_events(scenario, count)
    sent = 0
    failures = 0

    print(f"Senaryo: {scenario} | Toplam event: {len(events)} | delay: {config['delay']}s")

    if config.get("burst"):
        burst_size = config.get("burst_size", 10)
        pause = config.get("pause", 2)
        for start in range(0, len(events), burst_size):
            block = events[start:start + burst_size]
            for index, event in enumerate(block, start=1):
                try:
                    send_event(target, event, api_key=api_key)
                    sent += 1
                    print(f"  [burst {start // burst_size + 1}] {sent}/{len(events)} gönderildi")
                except Exception as exc:
                    failures += 1
                    print(f"  Hata: {exc}")
            time.sleep(pause)
    else:
        for index, event in enumerate(events, start=1):
            try:
                send_event(target, event, api_key=api_key)
                sent += 1
                print(f"  [{index}/{len(events)}] gönderildi")
            except Exception as exc:
                failures += 1
                print(f"  Hata: {exc}")
            time.sleep(config["delay"])

    print(f"Senaryo tamamlandı. Başarılı: {sent}, Hatalı: {failures}")


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"service": "generator", "status": "ready", "timestamp": datetime.utcnow().isoformat() + "Z"})


@app.route("/api/generate", methods=["POST"])
def api_generate():
    payload = request.get_json(silent=True) or {}
    target = payload.get("target", DEFAULT_TARGET)
    scenario = payload.get("scenario", DEFAULT_SCENARIO)
    count = payload.get("count", None)
    api_key = payload.get("api_key", DEFAULT_API_KEY)

    run_target = target or DEFAULT_TARGET
    run_scenario_target = run_scenario
    thread = threading.Thread(target=run_scenario_target, args=(run_target, scenario, count, api_key), daemon=True)
    thread.start()

    return jsonify({
        "status": "started",
        "target": run_target,
        "scenario": scenario,
        "count": count if count is not None else DEFAULT_COUNT,
    }), 202


def start_auto_generation(target: str, scenario: str, count: Optional[int], api_key: Optional[str], loop: bool, delay: float):
    if loop:
        print("Auto-generation loop enabled. Starting continuous generation.")
        while True:
            run_scenario(target, scenario, count=count, api_key=api_key)
            time.sleep(delay)
    else:
        print("Auto-generation enabled. Running one batch on startup.")
        run_scenario(target, scenario, count=count, api_key=api_key)


def parse_args():
    parser = argparse.ArgumentParser(description="Middleware için senaryo tabanlı veri üretici.")
    parser.add_argument("--target", default=os.environ.get("TARGET", DEFAULT_TARGET), help="Middleware API hedef URL")
    parser.add_argument("--scenario", default=os.environ.get("SCENARIO", DEFAULT_SCENARIO), choices=list(SCENARIO_CONFIG.keys()), help="Gönderim senaryosu")
    parser.add_argument("--count", type=int, default=os.environ.get("COUNT"), help="Üretilmesi gereken log sayısı")
    parser.add_argument("--api-key", default=os.environ.get("API_KEY", DEFAULT_API_KEY), help="Middleware API anahtarı")
    parser.add_argument("--mode", choices=["run", "server"], default=os.environ.get("MODE", DEFAULT_MODE), help="Çalışma modu: run veya server")
    parser.add_argument("--host", default=os.environ.get("HOST", DEFAULT_HOST), help="Sunucu host adresi")
    parser.add_argument("--port", type=int, default=os.environ.get("PORT", DEFAULT_PORT), help="Sunucu portu")
    parser.add_argument("--auto-generate", action="store_true", help="Enable auto-generation on server startup.")
    parser.add_argument("--auto-generate-loop", action="store_true", help="Keep auto-generating batches continuously.")
    parser.add_argument("--auto-generate-delay", type=float, default=DEFAULT_AUTO_GENERATE_DELAY, help="Delay between auto-generate batches in seconds.")
    return parser.parse_args()


def main():
    args = parse_args()
    if args.mode == "server":
        if DEFAULT_AUTO_GENERATE or args.auto_generate:
            auto_thread = threading.Thread(
                target=start_auto_generation,
                args=(args.target, args.scenario, args.count, args.api_key, DEFAULT_AUTO_GENERATE_LOOP or args.auto_generate_loop, args.auto_generate_delay),
                daemon=True,
            )
            auto_thread.start()

        print(f"Generator HTTP server starting on {args.host}:{args.port}")
        app.run(host=args.host, port=args.port)
    else:
        run_scenario(args.target, args.scenario, count=args.count, api_key=args.api_key)


if __name__ == "__main__":
    main()
