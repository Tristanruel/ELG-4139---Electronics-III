import pigpio
import time

TX_PIN = 23
BAUD_RATE = 9600

pi = pigpio.pi()

if not pi.connected:
    exit(0)

# Set up the GPIO pin as output
pi.set_mode(TX_PIN, pigpio.OUTPUT)

# Define a helper function to send data
def send_serial_data(pi, tx_pin, data, baud):
    bit_time = 1 / baud  # Time for one bit of data
    stop_bits = 2  # Number of stop bits in the communication

    for byte in data:
        # Start bit
        pi.write(tx_pin, 0)
        time.sleep(bit_time)

        # Data bits
        for bit in range(8):
            pi.write(tx_pin, byte & 1)
            time.sleep(bit_time)
            byte >>= 1

        # Stop bits
        pi.write(tx_pin, 1)
        time.sleep(bit_time * stop_bits)

try:
    # Sending "Hello World" followed by a newline
    send_serial_data(pi, TX_PIN, b'Hello World\n', BAUD_RATE)
finally:
    pi.stop()  # Properly stop the pigpio instance

