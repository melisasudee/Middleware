# FILE_MANIFEST.md

Bu dosya, projede bulunan ana dosyaların kısa açıklamalarını içerir.

## Başlangıç Dosyaları

- `00_OKU_BENI_FIRST.txt`
  - Projeye başlamadan önce mutlaka okunması gereken talimatları içerir.
- `BASLAMA_REHBERI.txt`
  - Projenin adım adım nasıl başlatılacağını açıklar.
- `QUICKSTART.sh`
  - Docker kurulumu, servis başlatma ve sağlık kontrolleri için otomatik script.

## Python Kod Dosyaları

- `app.py`
  - Flask tabanlı middleware API uygulaması.
  - Log işleme, batch gönderim, istatistik, export ve dashboard endpointleri sağlar.
- `anonymizer.py`
  - Hassas verileri maskeler ve anonimleştirir.
- `enricher.py`
  - Gönderilen logları risk skorları ve meta verilerle zenginleştirir.
- `formatters.py`
  - JSON, CSV ve HTML formatlama stratejilerini içerir.
- `generator.py`
  - Senaryo tabanlı test logu üretici.
- `data_generator.py`
  - Veri üretim desteği ve olay şablonları.
- `start_containers.py`
  - Docker Compose olmadan container yönetimi sağlar.
- `scenarios.py`
  - Örnek kullanım senaryolarını çalıştırır.
- `performance_test.py`
  - API performansını ölçmek için seri istekte bulunur.

## Docker Konfigürasyonu

- `Dockerfile.middleware`
  - Middleware hizmeti için görüntü oluşturur.
- `Dockerfile.generator`
  - Veri üretici hizmeti için görüntü oluşturur.
- `docker-compose.yml`
  - Middleware ve generator servislerini birlikte çalıştırmak için yapılandırma.

## Gereksinimler

- `requirements_middleware.txt`
  - Middleware için Python bağımlılıklarını listeler.
- `requirements_generator.txt`
  - Generator için Python bağımlılıklarını listeler.

## Dokümantasyon

- `README.md`
  - Projenin kullanımını, mimarisini ve teste yönelik bilgileri detaylı anlatır.
- `COPILOT_PROMPT.txt`
  - Copilot veya benzeri AI asistanları için proje özelinde kullanılacak prompt.
