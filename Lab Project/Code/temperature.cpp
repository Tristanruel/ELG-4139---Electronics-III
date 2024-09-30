#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>
#include <dirent.h>
#include <unistd.h>  // For usleep and sleep
#include <cstring>
#include <map>
#include <signal.h>
#include <chrono>
#include <pigpio.h>

volatile sig_atomic_t stop = 0;

void inthand(int signum) {
    stop = 1;
}

// Function to get DS18B20 device folders
std::vector<std::string> get_ds18b20_device_folders(const std::string& base_dir) {
    std::vector<std::string> device_folders;
    DIR* dir = opendir(base_dir.c_str());
    if (dir == nullptr) {
        std::cerr << "Failed to open directory: " << base_dir << std::endl;
        return device_folders;
    }
    struct dirent* ent;
    while ((ent = readdir(dir)) != nullptr) {
        std::string name = ent->d_name;
        if (name.find("28-") == 0) {
            device_folders.push_back(base_dir + name);
        }
    }
    closedir(dir);
    return device_folders;
}

// Function to read raw temperature data from DS18B20
std::vector<std::string> read_temp_raw(const std::string& device_file) {
    std::vector<std::string> lines;
    std::ifstream file(device_file);
    if (!file) {
        std::cerr << "Failed to open file: " << device_file << std::endl;
        return lines;
    }
    std::string line;
    while (std::getline(file, line)) {
        lines.push_back(line);
    }
    return lines;
}

// Function to convert raw data to Celsius for DS18B20
double read_temp(const std::string& device_file) {
    std::vector<std::string> lines = read_temp_raw(device_file);
    while (lines.empty() || lines[0].find("YES") == std::string::npos) {
        usleep(200000);  // Sleep for 200ms
        lines = read_temp_raw(device_file);
    }
    size_t pos = lines[1].find("t=");
    if (pos != std::string::npos) {
        std::string temp_string = lines[1].substr(pos + 2);
        double temp_c = std::stod(temp_string) / 1000.0;
        return temp_c;
    }
    return -1000.0;  // Return an invalid temperature value
}

// DHT22 reading function using pigpio
bool read_dht22(int pin, float& temperature, float& humidity) {
    if (gpioSetMode(pin, PI_OUTPUT) != 0) {
        return false;
    }
    gpioWrite(pin, 0);
    gpioDelay(18000); // 18 milliseconds
    gpioWrite(pin, 1);
    gpioDelay(40); // 40 microseconds

    if (gpioSetMode(pin, PI_INPUT) != 0) {
        return false;
    }

    // Data read logic remains the same, using gpioRead instead of digitalRead
    // Include your previous DHT22 reading logic here, replacing digitalRead with gpioRead
    // ...
}

int main() {
    signal(SIGINT, inthand);

    if (gpioInitialise() < 0) {
        std::cerr << "Failed to initialize pigpio" << std::endl;
        return 1;
    }

    // Initialize DS18B20 sensors
    std::string base_dir = "/sys/bus/w1/devices/";
    std::vector<std::string> device_folders = get_ds18b20_device_folders(base_dir);

    // Sensor names
    std::map<std::string, std::string> sensor_names = {
        {"28-3c01f0965cb3", "Ground Temperature 2"},
        {"28-3c01f0963fbc", "Ground Temperature 1"}
    };

    // Initialize water sensor
    int water_pin = 2;  // GPIO 2
    gpioSetMode(water_pin, PI_INPUT);

    // DHT22 sensor
    int dht22_pin = 3;  // GPIO 3

    while (!stop) {
        // Read from DHT22
        float temperature, humidity;
        if (read_dht22(dht22_pin, temperature, humidity)) {
            std::cout << "Air Temperature: " << temperature << " C" << std::endl;
            std::cout << "Humidity: " << humidity << " %" << std::endl;
        } else {
            std::cout << "Failed to retrieve data from humidity sensor" << std::endl;
        }

        // Read from water sensor
        int water_detected = gpioRead(water_pin);
        if (water_detected == 0) {
            std::cout << "Water: No" << std::endl;
        } else if (water_detected == 1) {
            std::cout << "Water: Yes" << std::endl;
        } else {
            std::cout << "Failed to read water sensor" << std::endl;
        }

        // Read from DS18B20
        for (const auto& device_folder : device_folders) {
            std::string device_file = device_folder + "/w1_slave";
            std::string sensor_id = device_folder.substr(device_folder.find_last_of('/') + 1);
            std::string sensor_name = "Unknown Sensor";
            auto it = sensor_names.find(sensor_id);
            if (it != sensor_names.end()) {
                sensor_name = it->second;
            }
            double ground_temp = read_temp(device_file);
            if (ground_temp > -1000.0) {
                std::cout << sensor_name << ": " << ground_temp << " °C" << std::endl;
            } else {
                std::cout << "Failed to read temperature from " << sensor_name << std::endl;
            }
        }

        sleep(1);  // Delay for a second
    }

    std::cout << "\nStopped by User" << std::endl;
    gpioTerminate();
    return 0;
}






#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>
#include <dirent.h>
#include <unistd.h>
#include <cstring>
#include <map>
#include <signal.h>
#include <chrono>

volatile sig_atomic_t stop = 0;

void inthand(int signum) {
    stop = 1;
}

// Function to get DS18B20 device folders
std::vector<std::string> get_ds18b20_device_folders(const std::string& base_dir) {
    std::vector<std::string> device_folders;
    DIR* dir = opendir(base_dir.c_str());
    if (dir == nullptr) {
        std::cerr << "Failed to open directory: " << base_dir << std::endl;
        return device_folders;
    }
    struct dirent* ent;
    while ((ent = readdir(dir)) != nullptr) {
        std::string name = ent->d_name;
        if (name.find("28-") == 0) {
            device_folders.push_back(base_dir + name);
        }
    }
    closedir(dir);
    return device_folders;
}

// Function to read raw temperature data from DS18B20
std::vector<std::string> read_temp_raw(const std::string& device_file) {
    std::vector<std::string> lines;
    std::ifstream file(device_file);
    if (!file) {
        std::cerr << "Failed to open file: " << device_file << std::endl;
        return lines;
    }
    std::string line;
    while (std::getline(file, line)) {
        lines.push_back(line);
    }
    return lines;
}

// Function to convert raw data to Celsius for DS18B20
double read_temp(const std::string& device_file) {
    std::vector<std::string> lines = read_temp_raw(device_file);
    while (lines.empty() || lines[0].find("YES") == std::string::npos) {
        usleep(200000);  // Sleep for 200ms
        lines = read_temp_raw(device_file);
    }
    size_t pos = lines[1].find("t=");
    if (pos != std::string::npos) {
        std::string temp_string = lines[1].substr(pos + 2);
        double temp_c = std::stod(temp_string) / 1000.0;
        return temp_c;
    }
    return -1000.0; 
}


class GPIO {
public:
    GPIO(int pin) : pin_number(pin) {
        export_pin();
        set_direction("in");
    }
    ~GPIO() {
        unexport_pin();
    }
    void export_pin() {
        std::ofstream export_file("/sys/class/gpio/export");
        if (export_file) {
            export_file << pin_number;
        } else {
            std::cerr << "Failed to export GPIO" << std::endl;
        }
    }
    void unexport_pin() {
        std::ofstream unexport_file("/sys/class/gpio/unexport");
        if (unexport_file) {
            unexport_file << pin_number;
        } else {
            std::cerr << "Failed to unexport GPIO" << std::endl;
        }
    }
    void set_direction(const std::string& dir) {
        std::string path = "/sys/class/gpio/gpio" + std::to_string(pin_number) + "/direction";
        std::ofstream dir_file(path);
        if (dir_file) {
            dir_file << dir;
        } else {
            std::cerr << "Failed to set direction for GPIO" << std::endl;
        }
    }
    int read_value() {
        std::string path = "/sys/class/gpio/gpio" + std::to_string(pin_number) + "/value";
        std::ifstream value_file(path);
        if (value_file) {
            int value;
            value_file >> value;
            return value;
        } else {
            std::cerr << "Failed to read value from GPIO" << std::endl;
            return -1;
        }
    }
private:
    int pin_number;
};


class DHT22 {
public:
    DHT22(int pin) : pin_number(pin) {
        export_pin();
        set_direction("out");
    }
    ~DHT22() {
        unexport_pin();
    }
    bool read_data(float& temperature, float& humidity) {
       
        write_value(0);
        usleep(18000);
        
        write_value(1);
        
        set_direction("in");
       
        if (!wait_for_level(0, 40)) {
            std::cerr << "DHT22: Failed to get response from sensor (initial low)" << std::endl;
            return false;
        }
        if (!wait_for_level(1, 88)) {
            std::cerr << "DHT22: Failed to get response from sensor (initial high)" << std::endl;
            return false;
        }
        if (!wait_for_level(0, 88)) {
            std::cerr << "DHT22: Failed to get response from sensor (second low)" << std::endl;
            return false;
        }
        // Now read 40 bits of data
        uint8_t data[5] = {0};
        for (int i = 0; i < 40; ++i) {
            if (!wait_for_level(1, 65)) {
                std::cerr << "DHT22: Failed to read data bit (start)" << std::endl;
                return false;
            }
            int duration = measure_pulse(0);
            if (duration < 0) {
                std::cerr << "DHT22: Failed to read data bit (duration)" << std::endl;
                return false;
            }
            int bit = duration > 40 ? 1 : 0;
            data[i/8] <<= 1;
            data[i/8] |= bit;
        }
        // Check checksum
        uint8_t checksum = data[0] + data[1] + data[2] + data[3];
        if (checksum != data[4]) {
            std::cerr << "DHT22: Checksum error" << std::endl;
            return false;
        }
        // Convert data
        humidity = ((data[0] << 8) + data[1]) * 0.1f;
        temperature = (((data[2] & 0x7F) << 8) + data[3]) * 0.1f;
        if (data[2] & 0x80) {
            temperature = -temperature;
        }
        return true;
    }
private:
    int pin_number;
    void export_pin() {
        std::ofstream export_file("/sys/class/gpio/export");
        if (export_file) {
            export_file << pin_number;
        }
    }
    void unexport_pin() {
        std::ofstream unexport_file("/sys/class/gpio/unexport");
        if (unexport_file) {
            unexport_file << pin_number;
        }
    }
    void set_direction(const std::string& dir) {
        std::string path = "/sys/class/gpio/gpio" + std::to_string(pin_number) + "/direction";
        std::ofstream dir_file(path);
        if (dir_file) {
            dir_file << dir;
        }
    }
    void write_value(int value) {
        std::string path = "/sys/class/gpio/gpio" + std::to_string(pin_number) + "/value";
        std::ofstream value_file(path);
        if (value_file) {
            value_file << value;
        }
    }
    int read_value() {
        std::string path = "/sys/class/gpio/gpio" + std::to_string(pin_number) + "/value";
        std::ifstream value_file(path);
        if (value_file) {
            int value;
            value_file >> value;
            return value;
        }
        return -1;
    }
    bool wait_for_level(int level, int timeout_us) {
        auto start = std::chrono::high_resolution_clock::now();
        while (true) {
            int value = read_value();
            if (value == level) {
                return true;
            }
            auto now = std::chrono::high_resolution_clock::now();
            int elapsed = std::chrono::duration_cast<std::chrono::microseconds>(now - start).count();
            if (elapsed > timeout_us) {
                return false;
            }
        }
    }
    int measure_pulse(int level) {
        auto start = std::chrono::high_resolution_clock::now();
        while (read_value() == level) {
            auto now = std::chrono::high_resolution_clock::now();
            int elapsed = std::chrono::duration_cast<std::chrono::microseconds>(now - start).count();
            if (elapsed > 100) {
                break;
            }
        }
        auto end = std::chrono::high_resolution_clock::now();
        return std::chrono::duration_cast<std::chrono::microseconds>(end - start).count();
    }
};

int main() {
    signal(SIGINT, inthand);

   
    std::string base_dir = "/sys/bus/w1/devices/";
    std::vector<std::string> device_folders = get_ds18b20_device_folders(base_dir);

   
    std::map<std::string, std::string> sensor_names = {
        {"28-3c01f0965cb3", "Ground Temperature 2"},
        {"28-3c01f0963fbc", "Ground Temperature 1"}
    };

    
    GPIO water_sensor(2);  // GPIO 2 (BCM numbering)

   
    DHT22 dht22_sensor(3);  // GPIO 3 (BCM numbering)

    while (!stop) {
        // Read from DHT22
        float temperature, humidity;
        if (dht22_sensor.read_data(temperature, humidity)) {
            std::cout << "Air Temperature: " << temperature << " C" << std::endl;
            std::cout << "Humidity: " << humidity << " %" << std::endl;
        } else {
            std::cout << "Failed to retrieve data from humidity sensor" << std::endl;
        }

        // Read from water sensor
        int water_detected = water_sensor.read_value();
        if (water_detected == 0) {
            std::cout << "Water: No" << std::endl;
        } else if (water_detected == 1) {
            std::cout << "Water: Yes" << std::endl;
        } else {
            std::cout << "Failed to read water sensor" << std::endl;
        }

        // Read from DS18B20
        for (const auto& device_folder : device_folders) {
            std::string device_file = device_folder + "/w1_slave";
            std::string sensor_id = device_folder.substr(device_folder.find_last_of('/') + 1);
            std::string sensor_name = "Unknown Sensor";
            auto it = sensor_names.find(sensor_id);
            if (it != sensor_names.end()) {
                sensor_name = it->second;
            }
            double ground_temp = read_temp(device_file);
            if (ground_temp > -1000.0) {
                std::cout << sensor_name << ": " << ground_temp << " °C" << std::endl;
            } else {
                std::cout << "Failed to read temperature from " << sensor_name << std::endl;
            }
        }

        
        sleep(1);
    }

    std::cout << "\nStopped by User" << std::endl;
    return 0;
}