import socket
import json
import time
import psutil
import platform
import uuid
import argparse


class MonitoringAgent:
    def __init__(self, server_host='localhost', server_port=8888, agent_id=None):
        self.server_host = server_host
        self.server_port = server_port
        self.agent_id = agent_id or self.get_agent_id()
        self.running = True
    def get_agent_id(self):
        hostname = platform.node()
        return f"{hostname}-{uuid.uuid4().hex[:8]}"
    def collect_metrics(self):
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            ram_percent = memory.percent
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            return {
                'cpu': round(cpu_percent, 2),
                'ram': round(ram_percent, 2),
                'disk': round(disk_percent, 2)
            }
        except Exception as e:
            print(f"Ошибка при сборе метрик: {e}")
            return None
    def send_report(self, metrics):
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((self.server_host, self.server_port))
            message = {
                'type': 'agent_report',
                'data': {
                    'agent_id': self.agent_id,
                    'ip': socket.gethostbyname(socket.gethostname()),
                    **metrics
                }
            }
            client.send(json.dumps(message).encode('utf-8'))
            response = client.recv(1024).decode('utf-8')
            client.close()
            return json.loads(response)
        except Exception as e:
            print(f"Ошибка при отправке отчета: {e}")
            return None
    def run(self, interval=60):
        print(f"Агент мониторинга запущен (ID: {self.agent_id})")
        print(f"Отправка данных на сервер {self.server_host}:{self.server_port}")
        print(f"Интервал отправки: {interval} секунд")
        try:
            while self.running:
                metrics = self.collect_metrics()
                if metrics:
                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] "
                          f"CPU: {metrics['cpu']}%, RAM: {metrics['ram']}%, Disk: {metrics['disk']}%")
                    response = self.send_report(metrics)
                    if response and response.get('status') == 'ok':
                        print("Отчет успешно отправлен")
                    else:
                        print("Ошибка при отправке отчета")
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\nОстановка агента...")
    def stop(self):
        self.running = False
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Агент мониторинга')
    parser.add_argument('--host', default='localhost', help='Сервер мониторинга')
    parser.add_argument('--port', type=int, default=8888, help='Порт сервера')
    parser.add_argument('--interval', type=int, default=60, help='Интервал отправки (секунды)')
    args = parser.parse_args()
    agent = MonitoringAgent(args.host, args.port)
    agent.run(args.interval)