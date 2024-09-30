#include <iostream>
#include <cpr/cpr.h>
#include <nlohmann/json.hpp>

int main() {
    std::string url = "http://api.weatherapi.com/v1/current.json";
    std::string apiKey = "216de71353404ef899e162434242709";
    std::string query = "45.419847,-75.679463";

    auto response = cpr::Get(cpr::Url{url},
                             cpr::Parameters{{"key", apiKey}, {"q", query}});

    if (response.status_code == 200) {
        auto json = nlohmann::json::parse(response.text);

        std::string location = json["location"]["region"].get<std::string>() + ", " + 
                               json["location"]["name"].get<std::string>() + ", " +
                               json["location"]["country"].get<std::string>();
        std::string localTime = json["location"]["localtime"].get<std::string>();
        std::string weatherCondition = json["current"]["condition"]["text"].get<std::string>();
        double tempC = json["current"]["temp_c"].get<double>();
        double windKph = json["current"]["wind_kph"].get<double>();
        int windDegree = json["current"]["wind_degree"].get<int>();
        std::string windDir = json["current"]["wind_dir"].get<std::string>();
        double pressureMb = json["current"]["pressure_mb"].get<double>();
        double precipMm = json["current"]["precip_mm"].get<double>();
        int humidity = json["current"]["humidity"].get<int>();
        int cloud = json["current"]["cloud"].get<int>();
        double feelsLikeC = json["current"]["feelslike_c"].get<double>();
        double windChillC = json["current"]["windchill_c"].get<double>();
        double heatIndexC = json["current"]["heatindex_c"].get<double>();
        double dewPointC = json["current"]["dewpoint_c"].get<double>();
        double visKm = json["current"]["vis_km"].get<double>();
        double uv = json["current"]["uv"].get<double>();
        double gustKph = json["current"]["gust_kph"].get<double>();

        std::cout << "Current weather in \"" << location << "\" on " << localTime << std::endl;
        std::cout << "\"" << weatherCondition << "\"" << std::endl;
        std::cout << "Temperature " << tempC << " C" << std::endl;
        std::cout << "wind_kph: " << windKph << std::endl;
        std::cout << "wind_degree: " << windDegree << std::endl;
        std::cout << "wind_dir: " << windDir << std::endl;
        std::cout << "pressure_mb: " << pressureMb << std::endl;
        std::cout << "precip_mm: " << precipMm << std::endl;
        std::cout << "humidity: " << humidity << std::endl;
        std::cout << "cloud: " << cloud << std::endl;
        std::cout << "feelslike_c: " << feelsLikeC << std::endl;
        std::cout << "windchill_c: " << windChillC << std::endl;
        std::cout << "heatindex_c: " << heatIndexC << std::endl;
        std::cout << "dewpoint_c: " << dewPointC << std::endl;
        std::cout << "vis_km: " << visKm << std::endl;
        std::cout << "uv: " << uv << std::endl;
        std::cout << "gust_kph: " << gustKph << std::endl;
    } else {
        std::cerr << "Failed to retrieve weather data. HTTP status code: " << response.status_code << std::endl;
    }

    return 0;
}
