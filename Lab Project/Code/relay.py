import RPi.GPIO as GPIO

# Set up GPIO pins
relay_pins = {1: 6, 2: 13, 3: 19, 4: 26}
GPIO.setmode(GPIO.BCM)  # Use Broadcom pin-numbering scheme
GPIO.setup(list(relay_pins.values()), GPIO.OUT, initial=GPIO.HIGH)  # Initialize pins as outputs, set to HIGH

def relay_command(command):
    """
    Accepts a command string to control relays, e.g., '1 ON', '2 OFF'.
    Handles active-low relays where 'ON' means setting GPIO to LOW.
    """
    try:
        relay_number, state = command.split()
        relay_number = int(relay_number)
        if relay_number in relay_pins:
            if state.upper() == 'ON':
                GPIO.output(relay_pins[relay_number], GPIO.LOW)  # Active-low relay ON
                print(f"Relay {relay_number} turned ON")
            elif state.upper() == 'OFF':
                GPIO.output(relay_pins[relay_number], GPIO.HIGH)  # Active-low relay OFF
                print(f"Relay {relay_number} turned OFF")
            else:
                print("Invalid command")
        else:
            print("Invalid relay number")
    except ValueError:
        print("Command format error. Use '<relay number> <ON/OFF>'.")

def cleanup():
    """
    Clean up GPIO assignments
    """
    GPIO.cleanup()

if __name__ == "__main__":
    try:
        while True:
            command = input("Enter relay command (e.g., '1 ON'): ")
            relay_command(command)
    except KeyboardInterrupt:
        cleanup()
        print("Program exited cleanly")
