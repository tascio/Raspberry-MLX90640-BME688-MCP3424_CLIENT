from flask import Flask, jsonify
import random, time

app = Flask(__name__)

@app.route("/api/v1.0/mlx90640_get_tmax")
def get_tmax():
    t_max = round(random.uniform(28.0, 40.0), 2)
    timestamp = int(time.time() * 1000) 
    return jsonify({"t_max": [timestamp, t_max]})

@app.route("/api/v1.0/mlx90640_get_array")
def get_array():
    data = {}
    for row in range(32):
        for col in range(24):
            value = round(random.uniform(20.0, 38.0), 2)
            key = f"x.{row}.{col}"
            data[key] = value
    return jsonify(data)

@app.route('/api/v1.0/bme688_values', methods=['GET'])
def simulate_sensor():
    timestamp = int(time.time() * 1000)
    data = {
        "altitude": [timestamp, random.uniform(0, 200)],
        "gas": [timestamp, random.uniform(0, 100000)],
        "humidity": [timestamp, random.uniform(0, 100)],
        "pressure": [timestamp, random.uniform(950, 1050)],
        "temp": [timestamp, random.uniform(20, 35)]
    }
    return jsonify(data)

@app.route('/api/v1.0/mcp3424_values', methods=['GET'])
def simulate_adc():
    timestamp = int(time.time() * 1000)  # timestamp in millisecondi
    
    adc_raw = random.randint(0, 4095)
    
    voltage = round((adc_raw / 4095) * 3.3, 4)
    
    data = {
        "channel0": [timestamp, {"raw": adc_raw, "voltage": voltage}],
        "channel1": [timestamp, {"raw": random.randint(0, 4095), "voltage": round(random.uniform(0, 3.3), 4)}],
        "channel2": [timestamp, {"raw": random.randint(0, 4095), "voltage": round(random.uniform(0, 3.3), 4)}],
        "channel3": [timestamp, {"raw": random.randint(0, 4095), "voltage": round(random.uniform(0, 3.3), 4)}],
    }
    
    return jsonify(data)

@app.route('/api/v1.0/wet_values')
def simulate_wet():
    timestamp = int(time.time() * 1000)
    wet = {}

    wet['timestamp'] = timestamp
    wet['temps'] = [round(random.uniform(0.0, 45.9), 3) for x in range (0, 19)]
    return jsonify(wet)

@app.route('/api/v1.0/power_supply_values')
def simulate_power_supply():
    timestamp = int(time.time() * 1000)
    data = {}

    data['timestamp'] = timestamp
    data['curr'] = round(random.uniform(0.0, 45.9), 3)
    data['volt'] = round(random.uniform(0.0, 45.9), 3)
    return jsonify(data)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5060, debug=True)
