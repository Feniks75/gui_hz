import tkinter as tk
from tkinter import ttk
import socket


def create_input_fields():
    global ip_entry, port_entry
    ip_label = ttk.Label(root, text='IP адрес:')
    ip_label.pack()
    ip_entry = ttk.Entry(root)
    ip_entry.pack()
    port_label = ttk.Label(root, text='Порт:')
    port_label.pack()
    port_entry = ttk.Entry(root)
    port_entry.pack()

def connect_to_s2vna():
    global client_socket, HOST, PORT
    try:
        HOST = ip_entry.get()
        PORT = int(port_entry.get())
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((HOST, PORT))

        connect_button.config(state=tk.DISABLED)
        status_label.config(text="Подключено")
    except Exception as e:
        status_label.config(text=f"Ошибка подключения: {e}")




def send_command(command): # komanda na serv
       client_socket.sendall(command)

def receive_data(): # dannie s serva bydyt  vrode
    data = client_socket.recv(1024)
    return data

def calculate_stats(data): # schitalka
        result_label.config(text=f"Среднее: {mean}")


root = tk.Tk()
root.title("Клиент для S2VNA") # tyt okno i knopki dalshe


create_input_fields() # mesta kyda pisat' ip i port
connect_button = ttk.Button(root, text="Подключиться", command=connect_to_s2vna)
connect_button.pack()
calc_button = ttk.Button(root, text="Вычислить статистику", command=calculate_stats)
calc_button.pack()


status_label = ttk.Label(root) # status podkluchenia
status_label.pack()

result_label = ttk.Label(root) # resultat schitalki
result_label.pack()

root.mainloop()