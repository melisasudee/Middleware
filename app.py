import json
import os
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string
from flask_jwt_extended import create_access_token

import config
from anonymizer import anonymize_event
from auth import require_auth
from enricher import enrich_event
from extensions import db, jwt, migrate, limiter
from formatters import FormatterFactory
from models import LogEntry, ApiKey


def create_app(config_name: str = None):
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "production")
    
    cfg = config.config_by_name.get(config_name, config.ProductionConfig)
    
    app = Flask(__name__)
    app.config.from_object(cfg)
    
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    limiter.init_app(app)
    
    with app.app_context():
        db.create_all()
    
    return app


app = create_app()

# Keep LOG_STORE for backwards compatibility with existing endpoints
LOG_STORE = []

DASHBOARD_HTML = """
<!doctype html>
<html lang="tr">
<head>
  <meta charset="utf-8">
  <title>Middleware Dashboard</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 32px; background: #f4f6fb; }
    h1, h2 { color: #223a5e; }
    .card { background: white; border-radius: 10px; padding: 24px; margin-bottom: 18px; box-shadow: 0 6px 18px rgba(0,0,0,.08); }
    pre { background: #eef2fa; padding: 12px; border-radius: 8px; overflow-x: auto; }
    a { color: #1552f0; text-decoration: none; }
  </style>
</head>
<body>
  <h1>Middleware Dashboard</h1>
  <p>Bu servis üzerinde log işleme, zenginleştirme ve anonimleştirme işlemleri yapılır.</p>
  <div class="card">
    <h2>Canlı istatistikler</h2>
    <p>Toplam işlem: <strong>{{ total }}</strong></p>
    <p>Kritik log sayısı: <strong>{{ critical }}</strong></p>
    <p>Tehlike düzeyi dağılımı:</p>
    <pre>{{ by_risk }}</pre>
  </div>
  <div class="card">
    <h2>Önemli Endpoints</h2>
    <ul>
      <li><a href="/health">/health</a></li>
      <li><a href="/stats">/stats</a></li>
      <li><a href="/export">/export</a></li>
      <li><a href="/logs/critical">/logs/critical</a></li>
      <li><a href="/logs/errors">/logs/errors</a></li>
      <li><a href="/logs/by-risk">/logs/by-risk</a></li>
    </ul>
  </div>
</body>
</html>
"""


def create_response(data=None, message=None, status=200):
    payload = {"status": "ok" if status == 200 else "error"}
    if message:
        payload["message"] = message
    if data is not None:
        payload["data"] = data
    return jsonify(payload), status


@app.route("/auth/login", methods=["POST"])
@limiter.limit("5 per minute")
def login():
    payload = request.get_json(silent=True)
    if not payload:
        return create_response(message="Geçerli JSON gönderin.", status=400)
    
    username = payload.get("username")
    password = payload.get("password")
    
    if not (username and password):
        return create_response(message="Username ve password gerekli.", status=400)
    
    if username == app.config.get("ADMIN_USERNAME") and password == app.config.get("ADMIN_PASSWORD"):
        access_token = create_access_token(identity=username)
        return create_response({"access_token": access_token})
    
    return create_response(message="Geçersiz kimlik bilgileri.", status=401)


@app.route("/", methods=["GET"])
def root():
    total_in_db = LogEntry.query.count()
    critical_count = LogEntry.query.filter(LogEntry.error_level.in_(["CRITICAL", "ERROR"])).count()
    by_risk = {}
    for log in LogEntry.query.all():
        level = log.risk_level or "UNKNOWN"
        by_risk[level] = by_risk.get(level, 0) + 1
    
    return render_template_string(
        DASHBOARD_HTML, 
        total=total_in_db, 
        critical=critical_count, 
        by_risk=json.dumps(by_risk, indent=2)
    )


@app.route("/dashboard", methods=["GET"])
def dashboard():
    return root()


@app.route("/health", methods=["GET"])
def health():
    return create_response({"service": "middleware", "uptime": datetime.utcnow().isoformat() + "Z"})


@app.route("/process", methods=["POST"])
@require_auth
@limiter.limit("100 per minute")
def process():
    event = request.get_json(silent=True)
    if not event:
        return create_response(message="Geçerli JSON gönderin.", status=400)

    event = anonymize_event(event)
    event = enrich_event(event)
    event["processed_at"] = datetime.utcnow().isoformat() + "Z"
    
    # Persist to database
    log_entry = LogEntry.from_payload(event)
    db.session.add(log_entry)
    db.session.commit()
    
    # Also keep in-memory for stats
    LOG_STORE.append(event)

    return create_response(event)


@app.route("/batch", methods=["POST"])
@require_auth
@limiter.limit("50 per minute")
def batch():
    payload = request.get_json(silent=True)
    if not payload or not isinstance(payload, list):
        return create_response(message="JSON dizi formatında gönderim gerekli.", status=400)

    results = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        item = anonymize_event(item)
        item = enrich_event(item)
        item["processed_at"] = datetime.utcnow().isoformat() + "Z"
        
        log_entry = LogEntry.from_payload(item)
        db.session.add(log_entry)
        LOG_STORE.append(item)
        results.append(item)
    
    db.session.commit()

    return create_response({"processed": len(results)})


@app.route("/stats", methods=["GET"])
def stats():
    total_in_db = LogEntry.query.count()
    critical_count = LogEntry.query.filter(LogEntry.error_level.in_(["CRITICAL", "ERROR"])).count()
    warnings_count = LogEntry.query.filter_by(error_level="WARNING").count()
    
    by_risk = {}
    for log in LogEntry.query.all():
        level = log.risk_level or "UNKNOWN"
        by_risk[level] = by_risk.get(level, 0) + 1
    
    return create_response({
        "total_logs": total_in_db,
        "critical": critical_count,
        "warnings": warnings_count,
        "by_risk": by_risk,
    })


@app.route("/export", methods=["GET"])
def export():
    fmt = request.args.get("format", "json").lower()
    limit = request.args.get("limit")
    
    query = LogEntry.query
    
    if limit is not None:
        try:
            limit_value = int(limit)
            if limit_value >= 0:
                query = query.limit(limit_value)
        except ValueError:
            return create_response(message="limit parametresi pozitif bir tam sayı olmalıdır.", status=400)
    
    events = [log.to_dict() for log in query.all()]
    
    if fmt == "json":
        return create_response(events)

    formatter = FormatterFactory.get_formatter(fmt)
    payload = formatter.format(events)
    content_type = "text/plain"
    if fmt == "html":
        content_type = "text/html"

    return app.response_class(payload, mimetype=content_type)


@app.route("/logs/critical", methods=["GET"])
def logs_critical():
    events = LogEntry.query.filter(LogEntry.error_level.in_(["CRITICAL", "ERROR"])).all()
    return create_response([log.to_dict() for log in events])


@app.route("/logs/errors", methods=["GET"])
def logs_errors():
    events = LogEntry.query.filter(LogEntry.error_level.in_(["ERROR", "WARNING"])).all()
    return create_response([log.to_dict() for log in events])


@app.route("/logs/by-risk", methods=["GET"])
def logs_by_risk():
    by_risk = {}
    for log in LogEntry.query.all():
        level = log.risk_level or "UNKNOWN"
        by_risk[level] = by_risk.get(level, 0) + 1
    return create_response(by_risk)


@app.route("/format/<string:mode>", methods=["GET"])
def format_logs(mode):
    all_logs = LogEntry.query.all()
    events = [log.to_dict() for log in all_logs]
    
    try:
        formatter = FormatterFactory.get_formatter(mode)
    except ValueError:
        return create_response(message="Format json, csv veya html olabilir.", status=400)

    payload = formatter.format(events)
    mimetype = "text/html" if mode == "html" else "text/plain"
    return app.response_class(payload, mimetype=mimetype)


@app.errorhandler(429)
def rate_limit_handler(e):
    return create_response(message="Çok fazla istek gönderdiniz. Lütfen bekleyin.", status=429)


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return create_response(message="İç sunucu hatası.", status=500)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)

