from datetime import datetime

from anonymizer import anonymize_event
from enricher import enrich_event


def scenario_happy_path():
    event = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "transaction_id": "TEST-10001",
        "sender_id": "BANK_A",
        "sender_email": "normal@customer.com",
        "transaction_type": "TRANSFER",
        "amount": 1500.75,
        "currency": "USD",
        "credit_card": "4532-1234-5678-9012",
        "tc_id": "12345678901",
        "error_level": "INFO",
        "message": "Normal transfer işlemi",
        "status": "SUCCESS",
    }
    return process_event(event)


def scenario_fraud_detection():
    event = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "transaction_id": "TEST-20002",
        "sender_id": "BANK_B",
        "sender_email": "fraud@customer.com",
        "transaction_type": "TRANSFER",
        "amount": 22000.00,
        "currency": "EUR",
        "credit_card": "5400-1234-5678-9010",
        "tc_id": "98765432109",
        "error_level": "ERROR",
        "message": "Büyük tutarlı transfer",
        "status": "PENDING",
    }
    return process_event(event)


def scenario_anonymization():
    event = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "transaction_id": "TEST-30003",
        "sender_id": "STORE_Y",
        "sender_email": "user@store.com",
        "transaction_type": "PAYMENT",
        "amount": 85.50,
        "currency": "TRY",
        "credit_card": "4111-1111-1111-1111",
        "tc_id": "11223344556",
        "error_level": "WARNING",
        "message": "Küçük değerli ödeme",
        "status": "SUCCESS",
    }
    return process_event(event)


def process_event(event):
    event = anonymize_event(event)
    event = enrich_event(event)
    return event


def run_all():
    return {
        "happy_path": scenario_happy_path(),
        "fraud_detection": scenario_fraud_detection(),
        "anonymization": scenario_anonymization(),
    }


if __name__ == "__main__":
    import json

    results = run_all()
    print(json.dumps(results, indent=2, ensure_ascii=False))
