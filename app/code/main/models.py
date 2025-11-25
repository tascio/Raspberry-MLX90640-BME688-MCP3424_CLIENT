import numpy as np
import requests, time, datetime, socketio
from flask import current_app
from threading import Lock, Thread
from main.logger import logger
from main.config import cfg, update_ip_rest, update_ip_sock

csv_path = cfg['CSV']['path']

class Threshold:
    status = False
    air_temp = None
    wri1_th = 18
    dc_th = 31
    fpga_th = 24
    wri2_18_th = 14
    

class Termocamera:
    VMIN, VMAX = 22, 40
    INTERP = 10



class mlx90640_view:
    def __init__(self, url):
        self.running = True
        try:
            self.url = url
            self.sio = socketio.Client()

            self.t_max = None
            self.timestamp = None
            self.array = np.zeros((24, 32))

            self.lock = Lock()

            @self.sio.event
            def connect():
                print("✅ Connesso al WebSocket")

            @self.sio.event
            def disconnect():
                print("🔌 Disconnesso dal WebSocket")

            @self.sio.on('sensor_data_mlx90640')
            def on_sensor_data(data):
                t_max = float(data['t_max'])
                timestamp = datetime.datetime.fromtimestamp(data['timestamp'] / 1000).strftime("%d-%m-%Y %H:%M:%S")
                array = np.zeros((24, 32))
                for key, value in data.items():
                    if key.startswith('mlx90640.array.'):
                        row = int(key.split('.')[-2])
                        col = int(key.split('.')[-1])
                        array[row, col] = value
                with self.lock:
                    self.t_max = t_max
                    self.timestamp = timestamp
                    self.array = array
            self.thread = Thread(target=self.start, daemon=True)
            self.thread.start()
        except Exception as e:
            logger.error(f"Error in mlxview {e}")
    
    def start(self):
        while self.running:
            try:
                self.sio.connect(self.url)
                while self.running and self.sio.connected:
                    time.sleep(0.2) 
            except Exception as e:
                if self.running:
                    time.sleep(5)
    def stop(self):
        self.running = False
        try:
            self.sio.disconnect()
        except:
            pass

    def update(self):
        with self.lock:
            return self.t_max, self.array, self.timestamp




#CLIENT FOR REST API
# class mlx90640_view:
#     def __init__(self, url):
#         self.URL_t_max = url + '/api/v1.0/mlx90640_get_tmax'
#         self.URL_camera = url + '/api/v1.0/mlx90640_get_array'

#     def update(self):
#         try:
#             response = requests.get(f'{self.URL_t_max}')
#             if response.status_code == 200:
#                 data = response.json()
#                 t_max = float(data['t_max'])
#                 timestamp = datetime.datetime.fromtimestamp(data['timestamp'] / 1000).strftime("%d-%m-%Y %H:%M:%S")

#                 data = requests.get(f'{self.URL_camera}').json()
#                 array = np.zeros((24, 32))
#                 for key, value in data.items():
#                     row = int(key.split('.')[-2])
#                     col = int(key.split('.')[-1])
#                     array[row, col] = value
#                 return t_max, array, timestamp
#             else:
#                 raise Exception(f"response status code {response.status_code}")
#         except requests.exceptions.RequestException as e:
#             return {"timestamp": "Network Error"}



class bme688_view:
    def __init__(self, url):
        self.url = url + '/api/v1.0/bme688_values'
    
    def update(self):
        try:
            response = requests.get(self.url)
            if response.status_code == 200:
                data = response.json()
                if data.get('response') == 503:
                    data['timestamp'] = 'Error 503'
                    return data
                data['altitude'] = round(data['altitude'], 2)
                data['humidity'] = round(data['humidity'], 2)
                data['pressure'] = round(data['pressure'], 2)
                Threshold.air_temp = data['temp'] = round(data['temp'], 2)
                data['dew_point'] = round(data['dew_point'], 2)
                data['timestamp'] = datetime.datetime.fromtimestamp(data['timestamp'] / 1000).strftime("%d-%m-%Y %H:%M:%S")
                return data
            else:
                raise Exception(f"response status code {response.status_code}")
        except requests.exceptions.RequestException as e:
            return {"timestamp": "Network Error"}
        except Exception as e:
            data = {}
            data['timestamp'] = f'Error 500'
            return data
    
class mcp3424_view:
    def __init__(self, url):
        self.url = url + '/api/v1.0/mcp3424_values'
    
    def update(self):
        try:
            response = requests.get(self.url)
            if response.status_code == 200:
                data = response.json()
                if data.get('response') == 503:
                    data['timestamp'] = 'Error 503'
                    return data
                data['val'] = round(data['val'], 2)
                data['timestamp'] = datetime.datetime.fromtimestamp(data['timestamp'] / 1000).strftime("%d-%m-%Y %H:%M:%S")
                return data
            else:
                raise Exception(f"response status code {response.status_code}")
        except requests.exceptions.RequestException as e:
            return {"timestamp": "Network Error"}
        except Exception as e:
            data = {}
            data['timestamp'] = 'Error 500'
            return data
    
class wet_view:
    def __init__(self, url):
        self.url = url + '/api/v1.0/wet_values'
        self.url_net = url + '/api/v1.0/what_wet'
    
    def update(self):
        try:
            response = requests.get(self.url)
            if response.status_code == 200:
                data = response.json()
                if data.get('response') == 503:
                    for val in current_app.config['WA']:
                        data[val] = 0 
                    data['timestamp'] = 'Error 503'
                    return data
                data['fpga'] = round(data['fpga'], 2)
                data['timestamp'] = datetime.datetime.fromtimestamp(data['timestamp'] / 1000).strftime("%d-%m-%Y %H:%M:%S")
                return data
            else:
                raise Exception(f"response status code {response.status_code}")
        except requests.exceptions.RequestException as e:
            return {"timestamp": "Network Error"}
        except Exception as e:
            data = {}
            data['timestamp'] = 'Error 500'
            return data
    
    def get_ip_mac(self):
        try:
            data = requests.post(self.url_net).json()
            ip = data['wet'].replace('"', '')
            mac = data['wet_mac'].replace('"', '')
        except Exception as e:
            ip = mac = f"WET Error {e}"
        return ip, mac

class wet_edit:
    def __init__(self, url):
        self.url_ip = url + '/api/v1.0/update_wet_ip'
        self.url_arp = url + '/api/v1.0/edit_ethers'
    
    def update_ip(self, ip):
        try:
            response = requests.post(self.url_ip, json={'set_wet_ip' : ip})
            if response.status_code == 200:
                data = response.json()
                if data.get('response') == 503:
                    data['response'] = 'Error 503'
                    return data
                return data
            else:
                raise Exception(f"response status code {response.status_code}")
        except requests.exceptions.RequestException as e:
            data = {}
            data['response'] = 503
            data['error'] = "Network Error"
            return data
        except Exception as e:
            data = {}
            data['response'] = 500
            data['error'] = 'Error 500'
            return data
    
    def update_arp(self, ip, mac):
        try:
            response = requests.post(self.url_arp, json={'ip' : ip, 'mac' : mac})
            if response.status_code == 200:
                data = response.json()
                if data.get('response') == 503:
                    data['response'] = 'Error 503'
                    return data
                return data
            else:
                raise Exception(f"response status code {response.status_code}")
        except requests.exceptions.RequestException as e:
            data = {}
            data['response'] = 503
            data['error'] = "Network Error"
            return data
        except Exception as e:
            data = {}
            data['response'] = 500
            data['error'] = f'Error 500 {e}'
            return data

class power_supply_view:
    def __init__(self, url):
        self.url = url + '/api/v1.0/power_supply_values'
        self.url_model = url + '/api/v1.0/what_ps'
    
    def update(self):
        try:
            response = requests.get(self.url)
            if response.status_code == 200:
                data = response.json()
                if data.get('response') == 503:
                    data['timestamp'] = 'Error 503'
                    return data
                data['timestamp'] = datetime.datetime.fromtimestamp(data['timestamp'] / 1000).strftime("%d-%m-%Y %H:%M:%S")
                return data
            else:
                raise Exception(f"response status code {response.status_code}")
        except requests.exceptions.RequestException as e:
            return {"timestamp": "Network Error"}
        except Exception as e:
            data = {}
            data['timestamp'] = 'Error 500'
            return data
    
    def get_model(self):
        try:
            model = requests.get(self.url_model).json()['model']
        except Exception as e:
            model = f"PS Error {e}"
        return model


class server_edit:
    def __init__(self, url):
        self.url = url + '/api/v1.0/update_server_ip'

    def update(self, ip):
        current_app.config['SERVER_REST'] = f"http://{ip}:{cfg['API_SERVER']['PORT_REST']}"
        current_app.config['SERVER_SOCK'] = f"http://{ip}:{cfg['API_SERVER']['PORT_SOCK']}"

        mlx_thread = current_app.config.get("mlx90640_websocket")

        if mlx_thread:
            mlx_thread.stop()

            if mlx_thread.thread.is_alive():
                mlx_thread.thread.join(timeout=2)
                logger.info(f"mlx_thread killed")
        
        current_app.config['mlx90640_websocket'] = mlx90640_view(current_app.config['SERVER_SOCK'])
        update_ip_rest(ip)
        update_ip_sock(ip)

        return dict(server_rest=current_app.config['SERVER_REST'],
                    server_sock=current_app.config['SERVER_SOCK'])


class csv_view:
    def __init__(self, url):
        self.url = url + '/api/v1.0/get_csv_data'

    def update(self):
        data = requests.get(f'{self.url}').json()
        for val in data.keys():
            data[val] = round(float(data[val]), 2)
        return data
    

