class Fault:
    def __init__(self, code, description, action):
        self.code = code
        self.description = description
        self.action = action

def get_fault(fault_number):
    if fault_number in fault_mapping:
        return fault_mapping[fault_number]
    else:
        raise ValueError(f"Invalid fault number {fault_number}")

# Define the fault mapping as a dictionary
fault_mapping = {
    3: Fault("OC", "Instantaneous overcurrent", ""),
    4: Fault("OCA", "Acceleration overcurrent", ""),
    5: Fault("OCD", "Deceleration overcurrent", ""),
    6: Fault("OCN", "Constant speed overcurrent", ""),
    7: Fault("OU", "Over-voltage", ""),
    8: Fault("LU" , "Undervoltage", ""),
    9: Fault("OH" , "Inverter overheat", ""),
    10: Fault("EF" , "External fault", ""),
    11: Fault("ERS", "Failure to restart", ""),
    12: Fault("LP" , "Input phase loss", ""),
    13: Fault("OL1", "Motor overload", ""),
    14: Fault("OL2", "VFD overload", ""),
    15: Fault("OL3", "Temporary motor overload", ""),
    16: Fault("OL4", "VFD Temporary overload", ""),
    17: Fault("485","Communication Failure", ""),
    18: Fault("PID" , "PID fault", ""),
}