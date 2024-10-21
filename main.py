import tkinter as tk
from tkinter import ttk
import socket
import pyvisa
import numpy as np

# Глобальные переменные для VISA
visa_resource_manager = None
instrument = None
client_socket = None  # Глобальная переменная для сокета

# Создание главного окна приложения
root = tk.Tk()
root.title("Клиент для S2VNA и VISA")

def create_input_fields():
    global freq1_entry, freq2_entry, visa_entry
    freq1_label = ttk.Label(root, text='Частота 1 (Гц):')
    freq1_label.grid(row=2, column=0, sticky="w")
    freq1_entry = ttk.Entry(root)
    freq1_entry.grid(row=2, column=1)

    freq2_label = ttk.Label(root, text='Частота 2 (Гц):')
    freq2_label.grid(row=3, column=0, sticky="w")
    freq2_entry = ttk.Entry(root)
    freq2_entry.grid(row=3, column=1)

def validate_ip(ip):
    parts = ip.split('.')
    if len(parts) != 4:
        return False
    for part in parts:
        if not part.isdigit() or not 0 <= int(part) <= 255:
            return False
    return True

def connect_to_visa():
    global visa_resource_manager, instrument
    try:
        visa_address = "TCPIP::127.0.0.1::5025::SOCKET"

        # Подключение через VISA
        visa_resource_manager = pyvisa.ResourceManager()
        instrument = visa_resource_manager.open_resource(visa_address)
        instrument.timeout = 5000
        instrument.write_termination = '\n'
        instrument.read_termination = '\n'

        # Получение *IDN? для проверки подключения
        idn_response = instrument.query("*IDN?")
        status_label.config(text=f"Подключено к VISA, IDN: {idn_response}")

        connect_visa_button.config(state=tk.DISABLED)
    except pyvisa.VisaIOError as e:
        status_label.config(text=f"Ошибка VISA: {e}")
    except Exception as e:
        status_label.config(text=f"Ошибка: {e}")

def send_command(command):
    try:
        client_socket.sendall((command + "\n").encode())
    except Exception as e:
        status_label.config(text=f"Ошибка отправки команды: {e}")

def receive_data():
    try:
        client_socket.settimeout(10)  # Увеличен таймаут до 10 секунд
        buffer_size = 4096
        data = b""

        while True:
            part = client_socket.recv(buffer_size)
            if not part:  # No more data
                break
            data += part

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

def perform_visa_measurement():
    try:
        if instrument is None:
            status_label.config(text="Ошибка: подключение VISA не установлено.")
            return

        NOP = 21  # Number of points
        instrument.write("SYST:PRES")  # Preset the instrument
        instrument.write(f"SENS1:SWE:POIN {NOP}")  # Set number of points
        instrument.write("CALC1:PAR1:DEF S21")  # Set parameter S21
        instrument.write("CALC1:PAR1:SEL")  # Select parameter
        instrument.write("CALC1:FORM MLOG")  # Set format to MLOG
        instrument.write("SENS1:BAND 100")  # Set bandwidth
        instrument.write("SENS1:FREQ:STAR")  # Set start frequency
        instrument.write("SENS1:FREQ:STOP")  # Set stop frequency

        instrument.write(":TRIG:SOUR BUS")
        instrument.write(":TRIG:SING")
        opc = instrument.query("*OPC?")
        print(f"Measurement completed (OPC status: {opc})")

        data = instrument.query_ascii_values("CALC:DATA:FDAT?", container=np.array)
        freq = instrument.query_ascii_values("SENS:FREQ:DATA?", container=np.array)

        status_label.config(text="Данные получены:")
        result_text = f"{'Frequency (GHz)':>20} {'Magnitude':>20} {'Phase':>20}\n"
        for i in range(NOP):
            result_text += f"{freq[i] / 1e9:>20.6f} {data[2 * i]:>20.6f} {data[2 * i + 1]:>20.6f}\n"

        result_label.config(text=result_text)
    except pyvisa.VisaIOError as e:
        status_label.config(text=f"Ошибка получения данных: {e}")

def on_close():
    try:
        if client_socket:
            client_socket.close()  # Закрытие TCP сокета
        if instrument:
            instrument.close()  # Закрытие VISA соединения
        root.destroy()  # Закрытие окна
    except Exception as e:
        print(f"Ошибка при закрытии сокета: {e}")

create_input_fields()



# Кнопка для подключения по VISA
connect_visa_button = ttk.Button(root, text="Подключиться (VISA)", command=connect_to_visa)
connect_visa_button.grid(row=5, column=1)

# Кнопка для запроса статистики
calc_button = ttk.Button(root, text="Запросить статистику (VISA)", command=perform_visa_measurement)
calc_button.grid(row=6, column=0, columnspan=2)

status_label = ttk.Label(root)
status_label.grid(row=7, column=0, columnspan=2)

result_label = ttk.Label(root)
result_label.grid(row=8, column=0, columnspan=2)

# Обработчик закрытия окна
root.protocol("WM_DELETE_WINDOW", on_close)

root.mainloop()
