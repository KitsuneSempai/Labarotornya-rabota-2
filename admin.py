import socket
import json
import argparse
class MonitoringClient:
    def __init__(self, server_host='localhost', server_port=8888):
        self.server_host = server_host
        self.server_port = server_port
    def request_report(self):
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((self.server_host, self.server_port))
            message = {'type': 'monitor_request'}
            client.send(json.dumps(message).encode('utf-8'))
            data = client.recv(65536).decode('utf-8')
            client.close()
            return json.loads(data)
        except Exception as e:
            print(f"Ошибка при запросе отчета: {e}")
            return None
    def format_report(self, report):
        if not report:
            return "Не удалось получить отчет от сервера"
        print("\n" + "=" * 80)
        print(f"ОТЧЕТ О СОСТОЯНИИ СЕРВИСОВ")
        print(f"Время формирования: {report['timestamp']}")
        print(f"Всего агентов: {report['total_agents']}")
        print("=" * 80)
        if report['total_agents'] == 0:
            print("Нет активных агентов")
            return
        print(f"{'Агент':<20} {'IP':<15} {'CPU':<8} {'RAM':<8} {'Disk':<8} {'Статус':<10} {'Последнее обновление':<20}")
        print("-" * 80)
        for agent in report['agents']:
            status = agent['status']
            if status == 'OK':
                status_display = f"\033[92m{status}\033[0m"  # Зеленый
            elif status == 'WARNING':
                status_display = f"\033[93m{status}\033[0m"  # Желтый
            else:
                status_display = f"\033[91m{status}\033[0m"  # Красный
            print(f"{agent['agent_id']:<20} {agent['ip']:<15} "
                  f"{agent['cpu']:>6}% {agent['ram']:>6}% {agent['disk']:>6}% "
                  f"{status_display:<10} {agent['last_update']:<20}")
        print("=" * 80)
        status_counts = {'OK': 0, 'WARNING': 0, 'CRITICAL': 0}
        for agent in report['agents']:
            status_counts[agent['status']] += 1
        print(f"\nСтатистика:")
        print(f"OK: {status_counts['OK']} агентов")
        print(f"WARNING: {status_counts['WARNING']} агентов")
        print(f"CRITICAL: {status_counts['CRITICAL']} агентов")
        print(f"\nРекомендации:")
        critical_agents = [a for a in report['agents'] if a['status'] == 'CRITICAL']
        if critical_agents:
            for agent in critical_agents:
                print(f"Требуется внимание: {agent['agent_id']}")
                if agent['cpu'] > 90:
                    print(f"     - Высокая загрузка CPU: {agent['cpu']}%")
                if agent['ram'] > 90:
                    print(f"     - Высокое использование RAM: {agent['ram']}%")
                if agent['disk'] > 90:
                    print(f"     - Мало свободного места на диске: {100 - agent['disk']}% свободно")
        else:
            print("Все системы работают в штатном режиме")
    def run(self):
        report = self.request_report()
        self.format_report(report)
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Клиент мониторинга')
    parser.add_argument('--host', default='localhost', help='Сервер мониторинга')
    parser.add_argument('--port', type=int, default=8888, help='Порт сервера')

    args = parser.parse_args()

    client = MonitoringClient(args.host, args.port)
    client.run()