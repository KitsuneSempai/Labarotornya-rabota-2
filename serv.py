import socket
import json
import threading
from datetime import datetime

class ServiceMonitorServer:
    def __init__(self, host='localhost', port=8888):
        self.host = host
        self.port = port
        self.agents_data = {}
        self.lock = threading.Lock()
        self.running = True
    def handle_client(self, client_socket, address):
        try:
            while self.running:
                data = client_socket.recv(4096)
                if not data:
                    break
                message = json.loads(data.decode('utf-8'))
                if message['type'] == 'agent_report':
                    self.process_agent_report(message['data'])
                    client_socket.send(json.dumps({'status': 'ok'}).encode('utf-8'))
                elif message['type'] == 'monitor_request':
                    report = self.generate_report()
                    client_socket.send(json.dumps(report).encode('utf-8'))
        except Exception as e:
            print(f"Ошибка при обработке клиента {address}: {e}")
        finally:
            client_socket.close()
    def process_agent_report(self, data):
        with self.lock:
            agent_id = data['agent_id']
            self.agents_data[agent_id] = {
                'cpu': data['cpu'],
                'ram': data['ram'],
                'disk': data['disk'],
                'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'ip': data.get('ip', 'unknown')
            }
            self.cleanup_old_data()
    def cleanup_old_data(self):
        current_time = datetime.now()
        stale_agents = []
        for agent_id, data in self.agents_data.items():
            last_update = datetime.strptime(data['last_update'], '%Y-%m-%d %H:%M:%S')
            if (current_time - last_update).seconds > 300:  # 5 минут
                stale_agents.append(agent_id)
        for agent_id in stale_agents:
            del self.agents_data[agent_id]
    def generate_report(self):
        with self.lock:
            report = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'total_agents': len(self.agents_data),
                'agents': []
            }
            for agent_id, data in self.agents_data.items():
                status = self.determine_status(data)
                agent_info = {
                    'agent_id': agent_id,
                    'ip': data['ip'],
                    'cpu': data['cpu'],
                    'ram': data['ram'],
                    'disk': data['disk'],
                    'status': status,
                    'last_update': data['last_update']
                }
                report['agents'].append(agent_info)
            return report
    def determine_status(self, data):
        """Определение статуса агента на основе метрик"""
        if data['cpu'] > 90:
            return 'CRITICAL'
        elif data['cpu'] > 70:
            return 'WARNING'
        elif data['ram'] > 90:
            return 'CRITICAL'
        elif data['ram'] > 70:
            return 'WARNING'
        elif data['disk'] > 90:
            return 'CRITICAL'
        elif data['disk'] > 70:
            return 'WARNING'
        else:
            return 'OK'
    def start(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((self.host, self.port))
        server.listen(5)

        print(f"Сервер мониторинга запущен на {self.host}:{self.port}")

        try:
            while self.running:
                client_socket, address = server.accept()
                print(f"Подключен клиент: {address}")
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, address)
                )
                client_thread.daemon = True
                client_thread.start()
        except KeyboardInterrupt:
            print("\nОстановка сервера...")
        finally:
            self.running = False
            server.close()
if __name__ == "__main__":
    server = ServiceMonitorServer()
    server.start()