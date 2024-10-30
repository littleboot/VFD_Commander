import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import serial.tools.list_ports
from pymodbus.client.serial import ModbusSerialClient
from pymodbus.pdu import ExceptionResponse
import struct

class SerialTool:
    def __init__(self, root):
        self.root = root
        self.root.title("Serial Modbus RTU Tool")
        
        # Serial connection variables
        self.client = None
        self.connected = False
        
        # Initialize UI components
        self.setup_ui()

    def setup_ui(self):
        # COM Port Section
        self.com_frame = ttk.LabelFrame(self.root, text="Serial Connection")
        self.com_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        self.com_label = ttk.Label(self.com_frame, text="COM Port:")
        self.com_label.grid(row=0, column=0, padx=5, pady=5)
        
        self.com_var = tk.StringVar()
        self.com_dropdown = ttk.Combobox(self.com_frame, textvariable=self.com_var)
        self.com_dropdown.grid(row=0, column=1, padx=5, pady=5)
        self.refresh_com_ports()
        
        self.refresh_button = ttk.Button(self.com_frame, text="Refresh", command=self.refresh_com_ports)
        self.refresh_button.grid(row=0, column=2, padx=5, pady=5)
        
        self.connect_button = ttk.Button(self.com_frame, text="Connect", command=self.connect_disconnect)
        self.connect_button.grid(row=0, column=3, padx=5, pady=5)

        # UART Settings
        self.baud_label = ttk.Label(self.com_frame, text="Baud Rate:")
        self.baud_label.grid(row=1, column=0, padx=5, pady=5)
        
        self.baud_var = tk.StringVar(value="9600")
        self.baud_entry = ttk.Entry(self.com_frame, textvariable=self.baud_var, width=10)
        self.baud_entry.grid(row=1, column=1, padx=5, pady=5)

        self.stop_bits_var = tk.StringVar(value="1")
        ttk.Label(self.com_frame, text="Stop Bits:").grid(row=1, column=2, padx=5, pady=5)
        self.stop_bits_dropdown = ttk.Combobox(self.com_frame, textvariable=self.stop_bits_var, values=["1", "1.5", "2"], width=5)
        self.stop_bits_dropdown.grid(row=1, column=3, padx=5, pady=5)

        # Modbus Parameters
        self.modbus_frame = ttk.LabelFrame(self.root, text="Modbus Settings")
        self.modbus_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

        self.slave_label = ttk.Label(self.modbus_frame, text="Slave Address (hex):")
        self.slave_label.grid(row=0, column=0, padx=5, pady=5)
        
        self.slave_var = tk.StringVar(value="8")
        self.slave_entry = ttk.Entry(self.modbus_frame, textvariable=self.slave_var, width=10)
        self.slave_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # Function Code with description in dropdown
        self.func_label = ttk.Label(self.modbus_frame, text="Function Code:")
        self.func_label.grid(row=0, column=2, padx=5, pady=5)
        
        # Function code with description
        self.func_var = tk.StringVar(value="0x06")
        self.func_dropdown = ttk.Combobox(self.modbus_frame, textvariable=self.func_var, values=["0x03 Read Holding Registers", "0x04 Read Input Registers", "0x06 Write Single Register"], width=25)
        self.func_dropdown.grid(row=0, column=3, padx=5, pady=5)
        
        self.start_address_label = ttk.Label(self.modbus_frame, text="Parameter Pxx:")
        self.start_address_label.grid(row=1, column=0, padx=5, pady=5)
        
        self.start_address_var = tk.StringVar(value="102")
        self.start_address_entry = ttk.Entry(self.modbus_frame, textvariable=self.start_address_var, width=10)
        self.start_address_entry.grid(row=1, column=1, padx=5, pady=5)

        # Data to Send
        self.data_label = ttk.Label(self.modbus_frame, text="Data (decimal):")
        self.data_label.grid(row=2, column=0, padx=5, pady=5)
        
        self.data_var = tk.StringVar(value="10000")
        self.data_entry = ttk.Entry(self.modbus_frame, textvariable=self.data_var, width=20)
        self.data_entry.grid(row=2, column=1, columnspan=2, padx=5, pady=5)

        # Send Button
        self.send_button = ttk.Button(self.modbus_frame, text="Send", command=self.send_modbus_packet)
        self.send_button.grid(row=3, column=0, columnspan=4, pady=10)

        # Log Window
        self.log = scrolledtext.ScrolledText(self.root, width=60, height=10, state="disabled")
        self.log.grid(row=2, column=0, padx=10, pady=10)

    def refresh_com_ports(self):
        ports = serial.tools.list_ports.comports()
        self.com_dropdown['values'] = [port.device for port in ports]

    def connect_disconnect(self):
        if self.connected:
            self.client.close()
            self.connected = False
            self.connect_button.config(text="Connect")
            self.log_message("Disconnected from serial port.")
        else:
            try:
                self.client = ModbusSerialClient(
                    port=self.com_var.get(),
                    baudrate=int(self.baud_var.get()),
                    stopbits=int(self.stop_bits_var.get()),
                    timeout=1
                )
                self.connected = self.client.connect()
                if self.connected:
                    self.connect_button.config(text="Disconnect")
                    self.log_message("Connected to serial port.")
                else:
                    messagebox.showerror("Error", "Failed to connect to serial port.")
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def compute_crc16(self, data):
        crc = 0xFFFF
        for pos in data:
            crc ^= pos
            for _ in range(8):
                if (crc & 1) != 0:
                    crc >>= 1
                    crc ^= 0xA001
                else:
                    crc >>= 1
        return crc

    def send_modbus_packet(self):
        if not self.connected:
            messagebox.showerror("Error", "Not connected to any COM port.")
            return
        
        try:
            # Parse user inputs
            slave_address = int(self.slave_var.get(), 16)  # Convert hex string to integer
            function_code = int(self.func_var.get().split()[0], 16)  # Get function code integer from dropdown
            start_address = int(self.start_address_var.get()) + 40000 # parameter address offset
            data = int(self.data_var.get())

            # Create Modbus packet without CRC
            packet = struct.pack('>BBHH', slave_address, function_code, start_address, data)
            crc = self.compute_crc16(packet)
            packet += struct.pack('<H', crc)

            # Send packet via serial client
            self.client.socket.write(packet)
            self.log_message(f"Sent    : {' '.join(format(x, '02X') for x in packet)}")

            # Read the response from the Modbus slave
            response = self.client.socket.read(8)  # Adjust byte count based on expected response
            if response:
                # Log the response
                response_hex = ' '.join(format(x, '02X') for x in response)
                self.log_message(f"Received: {response_hex}")
            else:
                # Log timeout error
                self.log_message("Timeout error: No response from slave.")

        except ValueError:
            messagebox.showerror("Error", "Invalid input data.")
        except Exception as e:
            messagebox.showerror("Error", str(e))


    def log_message(self, message):
        self.log.config(state="normal")
        self.log.insert(tk.END, message + "\n")
        self.log.config(state="disabled")
        self.log.see(tk.END)

root = tk.Tk()
app = SerialTool(root)
root.mainloop()
