import tkinter as tk
from tkinter import ttk
import socket
import threading

def create_input_fields():
    global ip_entry, port_entry, freq1_entry, freq2_entry
    ip_label = ttk.Label(root, text='IP адрес:')
    ip_label.pack()
    ip_entry = ttk.Entry(root)
    ip_entry.pack()

    port_label = ttk.Label(root, text='Порт:')
    port_label.pack()
    port_entry = ttk.Entry(root)
    port_entry.pack()

    freq1_label = ttk.Label(root, text='Частота 1 (Гц):')
    freq1_label.pack()
    freq1_entry = ttk.Entry(root)
    freq1_entry.pack()

    freq2_label = ttk.Label(root, text='Частота 2 (Гц):')
    freq2_label.pack()
    freq2_entry = ttk.Entry(root)
    freq2_entry.pack()

def connect_to_s2vna():
    global client_socket, HOST, PORT
    try:
        HOST = ip_entry.get()
        PORT = int(port_entry.get())

        if not validate_ip(HOST):
            status_label.config(text="Ошибка: некорректный IP адрес.")
            return
        if not (0 <= PORT <= 65535):
            status_label.config(text="Ошибка: некорректный порт (0-65535).")
            return

        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((HOST, PORT))

        connect_button.config(state=tk.DISABLED)
        status_label.config(text="Подключено")
    except ValueError:
        status_label.config(text="Ошибка: Порт должен быть числом.")
    except socket.error as e:
        status_label.config(text=f"Ошибка подключения: {e}")
    except Exception as e:
        status_label.config(text=f"Неизвестная ошибка: {e}")

def validate_ip(ip):
    parts = ip.split('.')
    if len(parts) != 4:
        return False
    for part in parts:
        if not part.isdigit() or not 0 <= int(part) <= 255:
            return False
    return True

def send_command(command):
    try:
        client_socket.sendall((command + "\n").encode())
    except Exception as e:
        status_label.config(text=f"Ошибка отправки команды: {e}")


def receive_data():
    try:
        client_socket.settimeout(5)  # Set a timeout of 5 seconds
        buffer_size = 4096
        data = b""

        while True:
            part = client_socket.recv(buffer_size)
            if not part:  # No more data
                break
            data += part

            # Optional: Check for a specific termination sequence, like a newline
            if b'\n' in part:  # Assuming data ends with a newline
                break

        return data.decode().strip()  # Clean up any surrounding whitespace
    except socket.timeout:
        status_label.config(text="Ошибка: Время ожидания истекло.")
        return None
    except socket.error as e:
        status_label.config(text=f"Ошибка получения данных: {e}")
        return None
    except Exception as e:
        status_label.config(text=f"Ошибка: {e}")
        return None


def request_statistics():
    threading.Thread(target=perform_statistics_request).start()

def perform_statistics_request():
    try:
        freq1 = freq1_entry.get()
        freq2 = freq2_entry.get()

        if not (freq1.isdigit() and freq2.isdigit()):
            status_label.config(text="Ошибка: Частоты должны быть числом.")
            return

        status_label.config(text=f"Запрос маркеров на частотах {freq1} и {freq2}...")
        send_command("CALC:MARK:DEL:ALL")  # Удаляем все маркеры
        send_command(f"CALC:MARK:X {freq1}, 1")  # Устанавливаем первый маркер
        send_command(f"CALC:MARK:X {freq2}, 2")  # Устанавливаем второй маркер

        send_command("CALC:STAT:ALL?")

        status_label.config(text="Получение данных...")
        data = receive_data()
        if data:
            display_statistics(data)
        else:
            status_label.config(text="Ошибка: данные не получены")

    except Exception as e:
        status_label.config(text=f"Ошибка при запросе статистики: {e}")

def display_statistics(data):
    status_label.config(text=f"Получены данные: {data}")
    result_label.config(text=f"Статистика: {data}")

def on_close():
    try:
        if client_socket:
            client_socket.close()  # Закрытие сокета перед завершением программы
        root.destroy()  # Закрытие окна
    except Exception as e:
        print(f"Ошибка при закрытии сокета: {e}")

# Создание главного окна приложения
root = tk.Tk()
root.title("Клиент для S2VNA")

create_input_fields()  # Поля ввода для IP и порта

connect_button = ttk.Button(root, text="Подключиться", command=connect_to_s2vna)
connect_button.pack()

calc_button = ttk.Button(root, text="Запросить статистику", command=request_statistics)
calc_button.pack()

status_label = ttk.Label(root)  # Статус подключения
status_label.pack()

result_label = ttk.Label(root)  # Результат статистики
result_label.pack()

# Обработчик закрытия окна
root.protocol("WM_DELETE_WINDOW", on_close)

root.mainloop()
