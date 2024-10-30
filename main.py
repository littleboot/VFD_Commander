import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, Scale
import serial.tools.list_ports
from pymodbus.client.serial import ModbusSerialClient
from pymodbus.pdu import ExceptionResponse
import struct
import datetime

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
        ### COM Port Section ###
        self.com_frame = ttk.LabelFrame(self.root, text="Serial Connection")
        self.com_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        self.com_label = ttk.Label(self.com_frame, text="COM Port:")
        self.com_label.grid(row=0, column=0, padx=5, pady=5)
        
        self.com_var = tk.StringVar(value="COM15")
        self.com_dropdown = ttk.Combobox(self.com_frame, textvariable=self.com_var, width=10)
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
        self.baud_entry = ttk.Entry(self.com_frame, textvariable=self.baud_var, width=13)
        self.baud_entry.grid(row=1, column=1, padx=5, pady=5)

        self.stop_bits_var = tk.StringVar(value="1")
        ttk.Label(self.com_frame, text="Stop Bits:").grid(row=1, column=2, padx=5, pady=5)
        self.stop_bits_dropdown = ttk.Combobox(self.com_frame, textvariable=self.stop_bits_var, values=["1", "1.5", "2"], width=5)
        self.stop_bits_dropdown.grid(row=1, column=3, padx=5, pady=5)

        ### Modbus Parameters ###
        self.modbus_frame = ttk.LabelFrame(self.root, text="Modbus Settings")
        self.modbus_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

        self.slave_label = ttk.Label(self.modbus_frame, text="Slave Address (hex):")
        self.slave_label.grid(row=0, column=0, padx=5, pady=5)
        
        self.slave_var = tk.StringVar(value="8")
        self.slave_entry = ttk.Entry(self.modbus_frame, textvariable=self.slave_var, width=20)
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
        self.start_address_entry = ttk.Entry(self.modbus_frame, textvariable=self.start_address_var, width=20)
        self.start_address_entry.grid(row=1, column=1, padx=5, pady=5)

        # Data to Send
        self.data_label = ttk.Label(self.modbus_frame, text="Data (decimal):")
        self.data_label.grid(row=2, column=0, padx=5, pady=5)
        
        self.data_var = tk.StringVar(value="10000")
        self.data_entry = ttk.Entry(self.modbus_frame, textvariable=self.data_var, width=20)
        self.data_entry.grid(row=2, column=1, columnspan=1, padx=5, pady=5)

        # Send Button
        self.send_button = ttk.Button(self.modbus_frame, text="Send", command=self.send_modbus_packet)
        self.send_button.grid(row=3, column=0, columnspan=1, pady=10)

        ### Log frame ###
        self.log_frame = ttk.LabelFrame(self.root, text="Log: ▼")
        self.log_frame.grid(row=2, column=0, padx=10, pady=10, sticky="w")      
        self.log_frame.bind("<Button-1>", self.toggle_log_frame) # Bind label press event to hide log frame
        
        # Show Modbus TX checkbox
        self.log_modbusTX_checkbox = ttk.Checkbutton(self.log_frame, text="Show Modbus TX", variable=tk.BooleanVar(value=True))
        self.log_modbusTX_checkbox.state(['!alternate']) # Disable alternate state
        self.log_modbusTX_checkbox.grid(row=0, column=0, padx=0, pady=(0,5), sticky='w')
        
        # Show Modbus RX checkbox
        self.log_modbusRX_checkbox = ttk.Checkbutton(self.log_frame, text="Show Modbus RX", variable=tk.BooleanVar(value=True))
        self.log_modbusRX_checkbox.state(['!alternate']) # Disable alternate state
        self.log_modbusRX_checkbox.grid(row=0, column=1, padx=0, pady=(0,5), sticky='w')
        
        # Log Window
        self.logwindow = scrolledtext.ScrolledText(self.log_frame, width=60, height=10, state="disabled")
        self.logwindow.grid(row=1, column=0, padx=10, pady=0, columnspan=2)
        
        # Clear log button
        self.clearlog_button = ttk.Button(self.log_frame, text="Clear Log", command=self.clearlog_callback)
        self.clearlog_button.grid(row=2, column=0, padx=0, pady=5)
                


        ### VFD Control Actions Frame ###
        self.vfd_frame = ttk.LabelFrame(self.root, text="VFD Control Actions")
        self.vfd_frame.grid(row=3, column=0, padx=10, pady=10, sticky="ew")

        # FWD Button
        self.fwd_button = ttk.Button(self.vfd_frame, text="FWD", command=self.set_fwd_parameters)
        self.fwd_button.grid(row=0, column=0, padx=5, pady=5)

        # REV Button
        self.fwd_button = ttk.Button(self.vfd_frame, text="REV", command=self.set_rev_parameters)
        self.fwd_button.grid(row=0, column=1, padx=5, pady=5)

        # STOP Button
        self.stop_button = ttk.Button(self.vfd_frame, text="STOP", command=self.set_stop_parameters)
        self.stop_button.grid(row=0, column=2, padx=5, pady=5)

        # Speed slider
        self.speed_label = ttk.Label(self.vfd_frame, text="Speed")
        self.speed_label.grid(row=1, column=0, padx=5, pady=5)

        self.frequency_slider = ttk.Scale(self.vfd_frame, from_=10, to=50, orient="horizontal", command=self.set_speed_parameters)
        self.frequency_slider.grid(row=1, column=1, padx=5, pady=5)

        self.speedvalue = "10Hz"
        self.speedvalue_label = ttk.Label(self.vfd_frame, text=self.speedvalue)
        self.speedvalue_label.grid(row=1, column=2, padx=5, pady=5)
        
        ### VFD Status feedback ###
        self.sensor_frame = ttk.LabelFrame(self.root, text="VFD status feedback")
        self.sensor_frame.grid(row=4, column=0, padx=10, pady=10, sticky="ew")
        
        # Get Running status
        self.test_button = ttk.Button(self.sensor_frame, text="Get Running-status", width=20, command=self.get_running_status)
        self.test_button.grid(row=0, column=0, padx=5, pady=5)
        
        # Get set frequency
        self.test_button = ttk.Button(self.sensor_frame, text="Get set-frequency", width=20, command=self.get_set_frequency)
        self.test_button.grid(row=1, column=0, padx=5, pady=5)
        
        # Get current frequency
        self.test_button = ttk.Button(self.sensor_frame, text="Get current-frequency", width=20, command=self.get_current_frequency)
        self.test_button.grid(row=2, column=0, padx=5, pady=5)


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
            return None

        try:
            # Parse user inputs
            slave_address = int(self.slave_var.get(), 16)  # Convert hex string to integer
            function_code = int(self.func_var.get().split()[0], 16)  # Get function code integer from dropdown
            start_address = int(self.start_address_var.get()) + 40000  # Parameter address offset
            data = int(self.data_var.get())

            # Create Modbus packet without CRC
            packet = struct.pack('>BBHH', slave_address, function_code, start_address, data)
            crc = self.compute_crc16(packet)
            packet += struct.pack('<H', crc)

            # Send packet via serial client
            self.client.socket.write(packet)
            self.log_message(f"Sent    : {' '.join(format(x, '02X') for x in packet)}")

            # Determine expected response length based on function code
            if function_code == 0x06:
                expected_length = 8  # Fixed length for function 0x06
            elif function_code == 0x03:
                # Read the first 3 bytes of the response to determine byte count
                header = self.client.socket.read(3)  # Slave address, function code, byte count
                if len(header) < 3:
                    self.log_message("Error: Incomplete response header received.")
                    return None

                # Unpack the header to get the byte count
                slave_address, function_code, byte_count = struct.unpack('>BBB', header)
                expected_length = 3 + byte_count + 2  # Header (3 bytes) + data bytes + CRC (2 bytes)

                # Read the remaining response bytes based on the expected length
                response_body = self.client.socket.read(expected_length - 3)
                if len(response_body) != (expected_length - 3):
                    self.log_message("Error: Incomplete response body received.")
                    return None

                # Combine header and body
                response = header + response_body
            else:
                self.log_message("Unsupported function code or not implemented.")
                return None

            # For function 0x06, directly read the full expected length
            if function_code == 0x06:
                response = self.client.socket.read(expected_length)
                if len(response) != expected_length:
                    self.log_message("Error: Incomplete response body received.")
                    return None

            # Separate CRC for validation
            response_without_crc = response[:-2]  # All except CRC bytes
            received_crc = struct.unpack('<H', response[-2:])[0]
            calculated_crc = self.compute_crc16(response_without_crc)

            # Check CRC validity
            if received_crc != calculated_crc:
                self.log_message("CRC error: Invalid checksum in received packet.")
                return None

            # Parse response if CRC is correct
            response_structure = {
                "slave_address": slave_address,
                "function_code": function_code
            }

            if function_code == 0x06:
                # Unpack response fields for function code 0x06
                response_structure["register_address"], response_structure["data"] = struct.unpack('>HH', response[2:6])
            elif function_code == 0x03:
                # For function 0x03, parse the data bytes based on byte count
                response_structure["byte_count"] = byte_count
                data_bytes = response[3:3 + byte_count]
                response_structure["data"] = [struct.unpack('>H', data_bytes[i:i+2])[0] for i in range(0, len(data_bytes), 2)]

            # Log the structured response
            response_hex = ' '.join(format(x, '02X') for x in response)
            self.log_message(f"Received: {response_hex}")
            
            return response_structure

        except ValueError:
            messagebox.showerror("Error", "Invalid input data.")
            return None
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return None

    @staticmethod
    def binarystring_to_decimalstring(binary_str):
        binary_str = binary_str[2:] # Remove the "0b" prefix from the binary string
        decimal_int = int(binary_str, 2)# Use built-in int function with base 2 to convert binary to decimal
        decimal_str = str(decimal_int) # Convert the decimal integer to a string
        return decimal_str
    
    def toggle_log_frame(self, event=None):
        # Toggle the visibility of the log frame contents and adjust frame height.
        if self.logwindow.winfo_viewable():  # If the log window is currently visible
            self.logwindow.grid_remove()      # Hide the log window
            self.clearlog_button.grid_remove() # Hide the clear log button
            self.log_frame.config(height=20)    # Set the height to 0 (optional)
            self.log_frame.config(text="Log: ▲")
        else:
            self.logwindow.grid()              # Show the log window
            self.clearlog_button.grid()        # Show the clear log button
            self.log_frame.config(text="Log: ▼")
            
        self.log_frame.update_idletasks()      # Refresh the layout

    def set_fwd_parameters(self):
        #  Modbus parameters: FWD action.
        # self.slave_var.set("8")                 # Set Slave Address (hex)
        self.func_var.set("0x06")  # Set Function Code
        self.start_address_var.set("103")        # Set Parameter Pxx
        self.data_var.set(self.binarystring_to_decimalstring("0b0001")) # Set Data (decimal)
        self.log_message("FWD parameters set.")
        self.send_modbus_packet()
    
    def set_rev_parameters(self):
        #  Modbus parameters: REV action.
        # self.slave_var.set("8")
        self.func_var.set("0x06")
        self.start_address_var.set("103")
        self.data_var.set(self.binarystring_to_decimalstring("0b0011"))
        self.log_message("REV parameters set.")
        self.send_modbus_packet()
    
    def set_stop_parameters(self):
        #  Modbus parameters: STOP action.
        # self.slave_var.set("8")
        self.func_var.set("0x06")
        self.start_address_var.set("103")
        self.data_var.set(self.binarystring_to_decimalstring("0b0000"))
        self.log_message("STOP parameters set.")
        self.send_modbus_packet()
    
    def set_speed_parameters(self, event=None):
        #  Modbus parameters: SPEED.
        frequency = str(int(self.frequency_slider.get()))

        # self.slave_var.set("8")
        self.func_var.set("0x06")
        self.start_address_var.set("102")
        self.data_var.set(str(int(self.frequency_slider.get())*100))
        self.log_message(f"Set Setpoint-frequency: {frequency} Hz", color="green")
        self.speedvalue_label["text"] = frequency + " Hz"
        self.send_modbus_packet()
        
    def get_running_status(self):
        # Send message to get running status
        # self.slave_var.set("8")                 # Set Slave Address (hex)
        self.func_var.set("0x03")  # Set Function Code
        self.start_address_var.set("180")        # Set Parameter Pxx
        self.data_var.set("1") # read single register
        
        response = self.send_modbus_packet()
        if response:
            data = response.get("data")[0]
            
            # self.log_message(data >> 0 & 1) #BIT0
            # self.log_message(data >> 1 & 1) #BIT1
            # self.log_message(data >> 2 & 1) #BIT2
            # self.log_message(data >> 3 & 1) #BIT3
            # self.log_message(data >> 4 & 1) #BIT4
            # self.log_message(data >> 5 & 1) #BIT5
            # self.log_message(data >> 6 & 1) #BIT6
            # self.log_message(data >> 7 & 1) #BIT7
            
            if data & 0b111 == 0b111: # BIT0, BIT1 and BIT2 are HIGH (running)
                self.log_message("Status   : Running", color="blue")
            else:
                self.log_message("Status   : Not running (Stopped)", color="blue")
            
            if data & (1 << 4) == (1 << 4): #Bit4 = HIGH; NOTE: manual sastates bit4-bit7 for direction status but only bit4 is used!
                self.log_message("Direction: Reverse", color="blue")
            else:
                self.log_message("Direction: Forward", color="blue")
            
        else:
            self.log_message("invalid response", color="red")
        
    def get_set_frequency(self):
        # Send message to get set frequency
        # self.slave_var.set("8")                 # Set Slave Address (hex)
        self.func_var.set("0x03")  # Set Function Code
        self.start_address_var.set("181")        # Set Parameter Pxx
        self.data_var.set("1") # read single register
        
        response = self.send_modbus_packet()
        if response:
            data = int(response.get("data")[0])
            self.log_message(f"Get Setpoint-frequency: {int(data/100)} Hz", color="blue")
        else:
            self.log_message("invalid response", color="red")
    
    def get_current_frequency(self):
        # Send message to get set current output drive frequency
        # self.slave_var.set("8")
        self.func_var.set("0x03")
        self.start_address_var.set("182")
        self.data_var.set("1")
        response = self.send_modbus_packet()
        
        if response:
            data = int(response.get("data")[0])
            self.log_message(f"Get Current-frequency: {int(data/100)} Hz", color="blue")
        else:
            self.log_message("invalid response", color="red")


    def log_message(self, message, color="black"):
        # Get the current date and time
        now = datetime.datetime.now()
        # Format the timestamp as a string
        timestamp = now.strftime("%H:%M:%S")
        
        # Insert the timestamp in black
        self.logwindow.config(state="normal")
        self.logwindow.insert(tk.END, f"[{timestamp}] ", "black")
        
        # Create a unique tag name for each message
        tag_name = f"color_{timestamp}_{color}"
        self.logwindow.tag_configure(tag_name, foreground=color)
        
        # Insert the message with the unique color tag
        self.logwindow.insert(tk.END, f"{message}\n", tag_name)
        
        self.logwindow.config(state="disabled")
        self.logwindow.see(tk.END)

    
    def clearlog_callback(self):
        # Clear the contents of the log widget.
        self.logwindow.config(state="normal")  # enable editing
        self.logwindow.delete('1.0', 'end')   # delete all text in the widget
        self.logwindow.config(state="disabled")  # disable editing


root = tk.Tk()
app = SerialTool(root)
root.mainloop()
