#!/usr/bin/env python3
import argparse
import os
import shlex
import subprocess
import sys
import time

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
NETWORK_NAME = "ceng302_network"
MIDDLEWARE_IMAGE = "ceng302-middleware"
GENERATOR_IMAGE = "ceng302-generator"
MIDDLEWARE_CONTAINER = "ceng302_middleware"
GENERATOR_CONTAINER = "ceng302_generator"
MIDDLEWARE_PORT = 5000


def run(cmd, capture=False, check=True):
    args = shlex.split(cmd)
    result = subprocess.run(args, capture_output=capture, text=True)
    if check and result.returncode != 0:
        raise RuntimeError(f"Komut başarısız: {cmd}\n{result.stderr.strip()}")
    return result


def docker_available():
    try:
        run("docker version", capture=True)
        return True
    except Exception:
        return False


def network_exists(name):
    result = run(f"docker network ls --filter name=^{name}$ --format '{{{{.Name}}}}'", capture=True, check=False)
    return name in result.stdout.strip().splitlines()


def create_network(name):
    if network_exists(name):
        print(f"🔧 Network zaten mevcut: {name}")
        return
    print(f"[ADIM 1/5] Network oluşturuluyor...")
    run(f"docker network create {name}")
    print("✅ Network oluşturuldu")


def build_image(dockerfile, tag):
    print(f"[ADIM 2/5] {tag} image'i inşa ediliyor...")
    run(f"docker build -f {dockerfile} -t {tag} .")
    print(f"✅ {tag} image'i inşa edildi")


def container_exists(name):
    result = run(f"docker ps -a --filter name=^{name}$ --format '{{{{.Names}}}}'", capture=True, check=False)
    return name in result.stdout.strip().splitlines()


def stop_container(name):
    if not container_exists(name):
        return
    print(f"Durduruluyor: {name}")
    run(f"docker stop {name}", check=False)


def remove_container(name):
    if not container_exists(name):
        return
    print(f"Siliniyor: {name}")
    run(f"docker rm {name}", check=False)


def cleanup_containers():
    print(f"[ADIM 4/5] Eski container'lar temizleniyor...")
    stop_container(MIDDLEWARE_CONTAINER)
    remove_container(MIDDLEWARE_CONTAINER)
    stop_container(GENERATOR_CONTAINER)
    remove_container(GENERATOR_CONTAINER)
    print("✅ Eski container'lar temizlendi")


def start_middleware():
    print(f"[ADIM 5/5] Middleware container başlatılıyor...")
    run(
        f"docker run -d --name {MIDDLEWARE_CONTAINER} --network {NETWORK_NAME} --network-alias middleware -p {MIDDLEWARE_PORT}:5000 {MIDDLEWARE_IMAGE}"
    )
    print("✅ Middleware container başlatıldı")


def start_generator():
    print(f"[ADIM 5/5] Generator container başlatılıyor...")
    run(
        f"docker run -d --name {GENERATOR_CONTAINER} --network {NETWORK_NAME} --network-alias generator -p 5001:5001 -e TARGET=http://middleware:5000/api/process -e API_KEY=local-api-key -e MODE=server -e PORT=5001 {GENERATOR_IMAGE}"
    )
    print("✅ Generator container başlatıldı")


def status():
    print("Container durumu:")
    run(f"docker ps -a --filter name={MIDDLEWARE_CONTAINER} --filter name={GENERATOR_CONTAINER}")


def health_check():
    print("Middleware health check yapılıyor...")
    for attempt in range(1, 11):
        result = run(f"docker exec {MIDDLEWARE_CONTAINER} curl -s -o /dev/null -w '%{{http_code}}' http://localhost:5000/health", capture=True, check=False)
        status_code = result.stdout.strip()
        if status_code == "200":
            print("✅ Middleware sağlıklı!")
            return True
        print(f"   ⏳ Deneme {attempt}/10: {status_code}")
        time.sleep(3)
    print("❌ Middleware sağlıklı değil ya da çalışmıyor.")
    return False


def logs(name):
    if not container_exists(name):
        print(f"Container bulunamadı: {name}")
        return
    run(f"docker logs --tail 100 -f {name}" if sys.stdin.isatty() else f"docker logs --tail 100 {name}")


def setup():
    if not docker_available():
        print("Docker bulunamadı. Lütfen Docker yüklü olduğundan emin olun.")
        sys.exit(1)

    create_network(NETWORK_NAME)
    build_image("Dockerfile.middleware", MIDDLEWARE_IMAGE)
    build_image("Dockerfile.generator", GENERATOR_IMAGE)
    cleanup_containers()
    start_middleware()
    start_generator()
    print("")
    health_check()
    print("\n✨ KURULUM TAMAMLANDI!")
    print("🚀 Dashboard: http://localhost:5000/dashboard")
    print("❤️ Health Check: curl http://localhost:5000/health")


def stop():
    stop_container(GENERATOR_CONTAINER)
    stop_container(MIDDLEWARE_CONTAINER)
    print("✅ Container'lar durduruldu")


def remove():
    remove_container(GENERATOR_CONTAINER)
    remove_container(MIDDLEWARE_CONTAINER)
    print("✅ Container'lar kaldırıldı")


def main():
    parser = argparse.ArgumentParser(description="Docker container yönetimi için yardımcı script.")
    parser.add_argument("command", choices=["setup", "status", "stop", "remove", "logs"], help="Çalıştırılacak komut")
    parser.add_argument("service", nargs="?", choices=["middleware", "generator"], help="Logs için service seçimi")
    args = parser.parse_args()

    if args.command == "setup":
        setup()
        return
    if args.command == "status":
        status()
        return
    if args.command == "stop":
        stop()
        return
    if args.command == "remove":
        remove()
        return
    if args.command == "logs":
        if not args.service:
            print("Lütfen middleware veya generator belirtin: python3 start_containers.py logs middleware")
            sys.exit(1)
        name = MIDDLEWARE_CONTAINER if args.service == "middleware" else GENERATOR_CONTAINER
        logs(name)
        return


if __name__ == "__main__":
    main()
