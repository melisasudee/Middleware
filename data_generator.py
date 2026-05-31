import argparse
import random
import time
from datetime import datetime
from typing import Any, Dict, List

import requests

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


def build_scenario_events(scenario: str) -> List[Dict[str, Any]]:
    events: List[Dict[str, Any]] = []
    template = random.choice(BASE_TEMPLATES)
    config = SCENARIO_CONFIG.get(scenario, SCENARIO_CONFIG["normal"])

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


def send_event(url: str, event: Dict[str, Any]) -> Dict[str, Any]:
    response = requests.post(url, json=event, timeout=15)
    response.raise_for_status()
    return response.json()


def run_scenario(target: str, scenario: str):
    config = SCENARIO_CONFIG.get(scenario, SCENARIO_CONFIG["normal"])
    events = build_scenario_events(scenario)
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
                    send_event(target, event)
                    sent += 1
                    print(f"  [burst {start // burst_size + 1}] {sent}/{len(events)} gönderildi")
                except Exception as exc:
                    failures += 1
                    print(f"  Hata: {exc}")
            time.sleep(pause)
    else:
        for index, event in enumerate(events, start=1):
            try:
                send_event(target, event)
                sent += 1
                print(f"  [{index}/{len(events)}] gönderildi")
            except Exception as exc:
                failures += 1
                print(f"  Hata: {exc}")
            time.sleep(config["delay"])

    print(f"Senaryo tamamlandı. Başarılı: {sent}, Hatalı: {failures}")


def parse_args():
    parser = argparse.ArgumentParser(description="Middleware için senaryo tabanlı veri üretici.")
    parser.add_argument("--target", default="http://middleware:5000/process", help="Middleware API hedef URL")
    parser.add_argument("--scenario", default="normal", choices=list(SCENARIO_CONFIG.keys()), help="Gönderim senaryosu")
    return parser.parse_args()


def main():
    args = parse_args()
    run_scenario(args.target, args.scenario)


if __name__ == "__main__":
    main()
