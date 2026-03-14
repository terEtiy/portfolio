import os
from pathlib import Path
import json
import urllib.parse
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import socket
import platform
import subprocess
import webbrowser
import ctypes
import time

class TaskAnalyzer:
    """Класс для анализа структуры папок и файлов задач"""
    
    def __init__(self, root_path):
        self.root_path = Path(root_path)
    
    def analyze(self):
        """Анализирует структуру папок и возвращает данные в формате JSON"""
        result = []
        
        if not self.root_path.exists():
            return {"error": f"Путь {self.root_path} не существует"}
        
        # Сначала проходим по папкам месяцев
        for month_folder in sorted(self.root_path.iterdir()):
            if not month_folder.is_dir():
                continue
            
            month_name = month_folder.name
            
            # Затем проходим по папкам с датами внутри месяца
            for date_folder in sorted(month_folder.iterdir()):
                if not date_folder.is_dir():
                    continue
                
                date_name = date_folder.name
                
                # Проходим по папкам задач внутри каждой даты
                for task_folder in sorted(date_folder.iterdir()):
                    if not task_folder.is_dir():
                        continue
                    
                    task_name = task_folder.name
                    task_data = self._analyze_task_folder(task_folder, f"{month_name} {date_name}", task_name)
                    result.append(task_data)
        
        return result
    
    def _analyze_task_folder(self, task_folder, date_name, task_name):
        """Анализирует конкретную папку задачи"""
        files = list(task_folder.iterdir())
        file_names = [f.name for f in files if f.is_file()]
        
        # Проверка наличия PDF с именем задачи
        task_pdf_name = f"{task_name}.pdf"
        pdf_exists = task_pdf_name in file_names
        
        # Статус БР
        br_status = "Загружено из БР" if pdf_exists else "Не загружено"
        
        # Логика для Геоанализа
        geo_status = self._check_geo_analysis(file_names, task_name)
        
        # Логика для Проекта
        project_status = self._check_project(file_names)
        
        # Логика для Чертежа
        drawing_status = self._check_drawing(file_names)
        
        # Логика для Справки
        reference_status = self._check_reference(file_names)
        
        return {
            "date": date_name,  # Оставляем только дату для сортировки
            "full_date": date_name,  # Полная дата
            "month": date_name.split('.')[1] if '.' in date_name else "",  # Месяц из даты
            "month_folder": date_name,  # Название папки с датой
            "task_number": task_name,
            "br_status": br_status,
            "geo_status": geo_status,
            "project_status": project_status,
            "drawing_status": drawing_status,
            "reference_status": reference_status,
            "task_folder": str(task_folder)
        }
    
    def _check_geo_analysis(self, file_names, task_name):
        """Проверяет статус Геоанализа"""
        geo_prefix = f"ГЕОАНАЛИЗ {task_name}"
        
        for file_name in file_names:
            if file_name.startswith(geo_prefix):
                if "_отказ" in file_name:
                    return "Отказ"
                elif "_на решение" in file_name:
                    return "На решение"
                else:
                    return "В работу"
        
        return "Не составлен"
    
    def _check_project(self, file_names):
        """Проверяет статус Проекта"""
        for file_name in file_names:
            if file_name.endswith(('.qgs', '.qgz')):
                # Извлекаем версию после "Г"
                import re
                match = re.search(r'Г(\d+)', file_name)
                if match:
                    return f"Подготовлен {match.group(1)}"
                return "Подготовлен"
        
        return "Проект не подготовлен"
    
    def _check_drawing(self, file_names):
        """Проверяет статус Чертежа"""
        for file_name in file_names:
            if file_name.endswith('.pdf') and 'Ч' in file_name:
                # Извлекаем версию после "Ч"
                import re
                match = re.search(r'Ч(\d+)', file_name)
                if match:
                    return f"Подготовлен {match.group(1)}"
                return "Подготовлен"
        
        return "Чертеж не подготовлен"
    
    def _check_reference(self, file_names):
        """Проверяет статус Справки"""
        # Приводим имена к нижнему регистру для сравнения
        lower_names = [f.lower() for f in file_names]
        
        has_txt = any(f.endswith('.txt') and f == 'сп.txt' for f in lower_names)
        has_docx = any(f.endswith('.docx') and 'сп' in f for f in lower_names)
        
        if has_txt and not has_docx:
            return "Нужна"
        elif has_txt and has_docx:
            return "Подготовлена"
        
        return ""


class FolderOpener:
    """Класс для открытия папок в файловом менеджере"""
    
    @staticmethod
    def open_folder(folder_path):
        """
        Открывает папку в стандартном файловом менеджере
        Возвращает: (success: bool, message: str)
        """
        try:
            # Проверяем существование папки
            if not os.path.exists(folder_path):
                return False, f"Папка не существует: {folder_path}"
            
            if not os.path.isdir(folder_path):
                return False, f"Указанный путь не является папкой: {folder_path}"
            
            # Открываем папку в зависимости от ОС
            system = platform.system()
            
            if system == 'Windows':
                # Открываем папку
                subprocess.Popen(['explorer', folder_path])
                
                # Даем время на открытие окна
                time.sleep(0.5)
                
                # Находим окно проводника и устанавливаем фокус
                user32 = ctypes.windll.user32
                
                # Ищем окно проводника (класс CabinetWClass)
                hwnd = user32.FindWindowW("CabinetWClass", None)
                
                if hwnd:
                    # Восстанавливаем окно, если оно свернуто
                    user32.ShowWindow(hwnd, 9)  # SW_RESTORE = 9
                    # Устанавливаем фокус
                    user32.SetForegroundWindow(hwnd)
                    
                return True, f"Папка открыта в проводнике Windows поверх других окон"
                
            elif system == 'Darwin':  # macOS
                # Для macOS используем открыть в Finder
                subprocess.run(['open', folder_path], check=True)
                return True, f"Папка открыта в Finder"
                
            else:  # Linux и другие Unix-подобные
                # Пробуем разные файловые менеджеры
                file_managers = ['xdg-open', 'nautilus', 'dolphin', 'thunar', 'pcmanfm']
                
                for fm in file_managers:
                    try:
                        subprocess.run([fm, folder_path], check=True, timeout=5)
                        return True, f"Папка открыта в {fm}"
                    except (subprocess.SubprocessError, FileNotFoundError):
                        continue
                
                return False, "Не удалось найти подходящий файловый менеджер"
                
        except Exception as e:
            return False, f"Ошибка при открытии папки: {str(e)}"
    
    @staticmethod
    def is_path_accessible(folder_path):
        """Проверяет доступность пути"""
        try:
            return os.path.exists(folder_path) and os.access(folder_path, os.R_OK)
        except:
            return False


class RequestHandler(BaseHTTPRequestHandler):
    """Обработчик HTTP запросов"""
    
    def do_GET(self):
        """Обработка GET запросов"""
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        
        # API endpoints
        if path == '/api/tasks':
            self._handle_api_request()
        elif path == '/api/open-folder':
            self._handle_open_folder_request()
        # Статические файлы
        elif path.startswith('/static/'):
            self._serve_static_file(path[1:])  # убираем ведущий слеш
        # Главная страница
        elif path == '/' or path == '/index.html':
            self._serve_static_file('static/index.html')
        else:
            self.send_error(404, "File not found")
    
    def do_POST(self):
        """Обработка POST запросов"""
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        
        if path == '/api/open-folder':
            self._handle_open_folder_post()
        else:
            self.send_error(404, "Endpoint not found")
    
    def _handle_api_request(self):
        """Обработка API запроса для получения задач"""
        # Получаем путь к папке из query параметров
        query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        folder_path = query.get('path', [''])[0]
        
        if not folder_path:
            # Если путь не указан, пытаемся найти стандартный путь
            possible_paths = [
                r'C:\Users\kadymskiy_ns\Desktop\ГПЗУ',
                os.path.expanduser('~/Desktop/ГПЗУ'),
                os.path.expanduser('~/Documents/ГПЗУ')
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    folder_path = path
                    break
        
        if not folder_path or not os.path.exists(folder_path):
            self._send_json_response(400, {
                "error": "Папка не найдена",
                "suggestions": self._find_gpzu_folders()
            })
            return
        
        # Анализируем структуру папок
        analyzer = TaskAnalyzer(folder_path)
        data = analyzer.analyze()
        
        # Отправляем ответ
        self._send_json_response(200, data)
    
    def _handle_open_folder_request(self):
        """Обработка GET запроса для открытия папки"""
        query = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        folder_path = query.get('path', [''])[0]
        
        if not folder_path:
            self._send_json_response(400, {
                "success": False,
                "message": "Не указан путь к папке"
            })
            return
        
        # Декодируем путь
        folder_path = urllib.parse.unquote(folder_path)
        
        # Открываем папку
        success, message = FolderOpener.open_folder(folder_path)
        
        self._send_json_response(200 if success else 400, {
            "success": success,
            "message": message,
            "path": folder_path
        })
    
    def _handle_open_folder_post(self):
        """Обработка POST запроса для открытия папки"""
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8'))
            folder_path = data.get('path', '')
            
            if not folder_path:
                self._send_json_response(400, {
                    "success": False,
                    "message": "Не указан путь к папке"
                })
                return
            
            # Открываем папку
            success, message = FolderOpener.open_folder(folder_path)
            
            self._send_json_response(200 if success else 400, {
                "success": success,
                "message": message,
                "path": folder_path
            })
            
        except json.JSONDecodeError:
            self._send_json_response(400, {
                "success": False,
                "message": "Неверный формат JSON"
            })
    
    def _send_json_response(self, status_code, data):
        """Отправляет JSON ответ"""
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')  # CORS для разработки
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode())
    
    def _find_gpzu_folders(self):
        """Ищет возможные папки ГПЗУ на диске"""
        suggestions = []
        home = os.path.expanduser('~')
        
        # Проверяем типичные места
        check_paths = [
            home,
            os.path.join(home, 'Desktop'),
            os.path.join(home, 'Рабочий стол'),
            os.path.join(home, 'Documents'),
            os.path.join(home, 'Документы'),
            os.path.join(home, 'Downloads'),
            os.path.join(home, 'Загрузки')
        ]
        
        for path in check_paths:
            if os.path.exists(path):
                try:
                    for item in os.listdir(path):
                        if 'ГПЗУ' in item and os.path.isdir(os.path.join(path, item)):
                            full_path = os.path.join(path, item)
                            if FolderOpener.is_path_accessible(full_path):
                                suggestions.append(full_path)
                except PermissionError:
                    continue
        
        # Добавляем также родительские папки, которые могут содержать ГПЗУ
        common_roots = ['C:\\', 'D:\\', 'E:\\'] if platform.system() == 'Windows' else ['/']
        for root in common_roots:
            if os.path.exists(root):
                try:
                    for item in os.listdir(root):
                        if 'ГПЗУ' in item and os.path.isdir(os.path.join(root, item)):
                            full_path = os.path.join(root, item)
                            if FolderOpener.is_path_accessible(full_path):
                                suggestions.append(full_path)
                except PermissionError:
                    continue
        
        return list(set(suggestions))[:5]  # Уникальные значения, не больше 5
    
    def _serve_static_file(self, filepath):
        """Отдает статические файлы"""
        try:
            with open(filepath, 'rb') as f:
                content = f.read()
            
            # Определяем Content-Type по расширению
            if filepath.endswith('.html'):
                content_type = 'text/html'
            elif filepath.endswith('.css'):
                content_type = 'text/css'
            elif filepath.endswith('.js'):
                content_type = 'application/javascript'
            elif filepath.endswith('.json'):
                content_type = 'application/json'
            elif filepath.endswith(('.png', '.jpg', '.jpeg', '.gif', '.ico')):
                content_type = f'image/{filepath.split(".")[-1]}'
            else:
                content_type = 'text/plain'
            
            self.send_response(200)
            self.send_header('Content-type', content_type)
            self.end_headers()
            self.wfile.write(content)
            
        except FileNotFoundError:
            self.send_error(404, "File not found")
        except Exception as e:
            self.send_error(500, str(e))
    
    def log_message(self, format, *args):
        """Переопределяем для тишины в консоли"""
        # Можно раскомментировать для отладки:
        # print(f"{self.log_date_time_string()} - {format % args}")
        pass


def open_browser(url):
    """Открывает браузер с указанным URL"""
    try:
        webbrowser.open(url)
    except:
        pass


def find_free_port(start_port=8000, max_attempts=10):
    """Находит свободный порт для запуска сервера"""
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            result = sock.connect_ex(('localhost', port))
            if result != 0:  # Порт свободен
                return port
    return None


def ensure_static_folder():
    """Проверяет наличие папки static и создает если нужно"""
    static_dir = Path('static')
    if not static_dir.exists():
        static_dir.mkdir()
        print("📁 Создана папка static")
    
    # Проверяем наличие основных файлов
    index_file = static_dir / 'index.html'
    css_file = static_dir / 'index.css'
    js_file = static_dir / 'index.js'
    
    if not index_file.exists():
        print("⚠️  Файл index.html не найден в папке static")
    if not css_file.exists():
        print("⚠️  Файл index.css не найден в папке static")
    if not js_file.exists():
        print("⚠️  Файл index.js не найден в папке static")


def main():
    """Основная функция запуска сервера"""
    # Проверяем структуру папок
    ensure_static_folder()
    
    # Ищем свободный порт
    port = find_free_port(8000)
    if not port:
        print("❌ Не удалось найти свободный порт")
        return
    
    server_address = ('', port)
    httpd = HTTPServer(server_address, RequestHandler)
    
    url = f'http://localhost:{port}'
    
    print("=" * 60)
    print("🚀 Сервер анализа задач ГПЗУ запущен!")
    print(f"📊 Откройте в браузере: {url}")
    print("=" * 60)
    print("\n💡 Доступные функции:")
    print("   ✅ Анализ структуры папок (с поддержкой вложенности месяцев)")
    print("   ✅ Фильтрация и группировка данных")
    print("   ✅ Открытие папок в проводнике")
    print("   ✅ Поиск по номеру задачи")
    print("   ✅ Экспорт в CSV")
    print("\n📁 Папка static должна содержать:")
    print("   • index.html")
    print("   • index.css")
    print("   • index.js")
    print("\n❌ Для остановки сервера нажмите Ctrl+C")
    print("=" * 60)
    
    # Открываем браузер автоматически
    open_browser(url)
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Сервер остановлен")
    except Exception as e:
        print(f"\n❌ Ошибка сервера: {e}")


if __name__ == '__main__':
    main()