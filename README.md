# Data Middleware Projesi

Bu proje, bir e-ticaret uygulamasına yönelik veri middleware mimarisinin örnek implementasyonunu içerir. Aşağıdaki katmanlar yer alır:

- `middleware` servisi: Gelen logları işler, anonimleştirir, zenginleştirir ve depolar.
- `generator` servisi: Test verisi üretir ve middleware API'sine gönderir.
- `dashboard` ve `API` endpointleri: sistem durumunu ve kayıtlı logları görüntüler.

## Hızlı Başlangıç

1. Proje klasörüne geçin:
   ```bash
   cd /home/miela/FinalProje
   ```
2. `QUICKSTART.sh` çalıştırılabilir hale getirin:
   ```bash
   chmod +x QUICKSTART.sh
   ```
3. Otomatik başlangıcı başlatın:
   ```bash
   ./QUICKSTART.sh
   ```

Proje başlarken Docker ve Docker Compose kurulu olmalıdır.

## Servisler

### Middleware

`app.py` içinde tanımlanan Flask uygulaması aşağıdaki endpointleri sağlar:

- `GET /health` - servis sağlığını kontrol eder
- `GET /dashboard` - basit bir dashboard sunar
- `POST /process` - tek bir log kaydı işler
- `POST /batch` - birden fazla log kaydını toplu işler
- `GET /stats` - işlenmiş loglara ait istatistikleri döner
- `GET /export` - tüm işlenmiş logları indirir (`?format=json|csv|html` ve `?limit=<n>`)
- `GET /logs/critical` - kritik seviyedeki logları listeler
- `GET /logs/errors` - hata ve uyarı seviyesindeki logları listeler
- `GET /logs/by-risk` - risk seviyesine göre gruplama yapar

### Generator

`generator.py`, senaryoya dayalı test logları üretir ve middleware API'sine POST eder. Bu sayede sistemin işleyişini test etmek kolaylaşır.
Kullanım örneği:
```bash
python generator.py --scenario normal
python generator.py --scenario burst
python generator.py --target http://localhost:5000/process --scenario extreme
```
## Dosya Açıklamaları

- `app.py` - Flask API uygulaması
- `anonymizer.py` - hassas alanları anonimleştirme işlevleri
- `enricher.py` - log kayıtlarını risk ve meta verilerle zenginleştirme
- `formatters.py` - JSON, CSV ve HTML formatlama stratejileri
- `generator.py` - senaryo tabanlı test logu üretici
- `data_generator.py` - veri üretim desteği ve olay şablonları
- `scenarios.py` - senaryo bazlı test verisi ve işleme
- `performance_test.py` - performans testi için istek üretici
- `Dockerfile.middleware` - middleware servisi için Dockerfile
- `Dockerfile.generator` - generator servisi için Dockerfile
- `docker-compose.yml` - servis orkestrasyonu
- `requirements_middleware.txt` - middleware bağımlılıkları
- `requirements_generator.txt` - generator bağımlılıkları
- `README.md` - proje rehberi ve kullanım talimatları
- `FILE_MANIFEST.md` - dosya açıklamaları
- `COPILOT_PROMPT.txt` - proje için Copilot prompt
- `QUICKSTART.sh` - başlangıç otomasyon scripti
- `BASLAMA_REHBERI.txt` - hızlı başlangıç adımları
- `00_OKU_BENI_FIRST.txt` - öncelikli okunması gereken dosya

## Docker ile Çalıştırma

### Manuel Başlatma

```bash
docker-compose build
docker-compose up -d
```

### Docker Compose Olmazsa

Eğer `docker-compose` veya `docker compose` yüklenemiyorsa, alternatif olarak `start_containers.py` scriptini kullanabilirsiniz.

```bash
python3 start_containers.py setup
```

### Start Containers Yardımcı Scripti

- `python3 start_containers.py setup` - network, image ve container kurulumu
- `python3 start_containers.py status` - container durumu
- `python3 start_containers.py stop` - container'ları durdur
- `python3 start_containers.py remove` - container'ları sil
- `python3 start_containers.py logs middleware` - middleware loglarını göster
- `python3 start_containers.py logs generator` - generator loglarını göster

### Durum Kontrol

```bash
docker ps --filter "name=ceng302_"
curl http://localhost:5000/health
```

### Container'ları Durdurma

```bash
python3 start_containers.py stop
```

## Test ve Performans

### Performans Testi

```bash
python performance_test.py --target http://localhost:5000/process --count 50 --workers 10 --batch-size 20 --batch-count 5
```

Bu script aşağıdaki testleri çalıştırır:
- Latency testi
- Throughput testi
- Batch işleme testi
- Stress testi

Ayrıca interaktif menü ile çalıştırmak için:

```bash
python performance_test.py --interactive
```

Bu seçenekten sonra menüde aşağıdakiler seçilebilir:
1. Latency Test
2. Throughput Test
3. Batch Test
4. Stress Test
5. Tüm Testleri Çalıştır

Rapor JSON olarak `performance_report_YYYYMMDD_HHMMSS.json` formatında kaydedilir.

### Senaryolar

```bash
python scenarios.py
```

### Formatlama

`app.py` üzerinde eklenen `/format/<mode>` endpointi ile JSON, CSV ve HTML çıktısı alınabilir.

## Katkı ve Geliştirme

- `anonymizer.py` alanları daha baştan sona maskeler.
- `enricher.py` risk skorları üretir ve davranışsal zenginleştirme ekler.
- `formatters.py` strateji desenini kullanarak farklı çıktı formatları sağlar.

Dokümantasyonu ve komponentleri genişletmek isterseniz, `README.md` içinde yer alan yapılandırma adımlarını kullanabilirsiniz.

---

## Notlar

`QUICKSTART.sh` ile otomatik kurulum yaparken, proje dosyalarının tamamının aynı dizinde olduğundan emin olun.

Bu proje modüler bir veri middleware örneğidir ve gerçek bir üretim ortamına hazır hale getirilmeden önce ek güvenlik, hata yönetimi ve servis izleme katmanları eklenmelidir.
