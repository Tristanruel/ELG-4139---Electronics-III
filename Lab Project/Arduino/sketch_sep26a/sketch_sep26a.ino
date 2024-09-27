void setup() {
  Serial.begin(9600);  // Start serial communication at 9600 baud
}

void loop() {
  if (Serial.available() > 0) {
    String received = Serial.readString();
    // Do something with the received string
    Serial.println(received);  // Echo back to Serial Monitor
  }
}
