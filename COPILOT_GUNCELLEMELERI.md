# COPILOT GÜNCELLEMELERİ

Bu dosya, Copilot tarafından projeye yapılan son eklemeleri ve iyileştirmeleri özetler.

## Eklenen/Değiştirilen Özellikler

- `app.py`
  - `GET /export` endpointine `format=json|csv|html` desteği eklendi.
  - `limit=<n>` query parameter ile çıktı sınırlandırma desteği eklendi.

- `performance_test.py`
  - `--interactive` parametresi ile menü tabanlı test çalıştırma eklendi.
  - Test sonuçları JSON rapor olarak kaydedilir.
  - `latency`, `throughput`, `batch`, `stress` testleri ayrı ayrı ve toplu çalıştırılabilir.

- `performance_report_*.json`
  - Her test çalıştırmasında rapor dosyası oluşturulacak şekilde script güncellendi.

## Doğrulanan Gereksinimler

- Anonymization stratejileri: maskleme, hashing, replacement + pattern detection
- Enrichment: risk seviyesi, error sınıflandırması, tag'ler ve transaction analizi
- Strategy Pattern: `OutputFormatter`, `FormatterFactory`, JSON/CSV/HTML formatlama
- Data generator: 5 senaryo desteği
- Docker wrapper: `generator.py` + `Dockerfile.generator`
- Performance tests: latency, throughput, batch, stress + rapor üretimi

## Kullanım

```bash
docker-compose build
docker-compose up -d
python performance_test.py --interactive
```
