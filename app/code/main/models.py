import numpy as np
import requests, time, datetime
from flask import current_app
from threading import Lock, Thread
from main.logger import logger
from main.config import cfg, update_ip_rest, update_ip_sock

csv_path = cfg['CSV']['path']
socketio = None

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


class MLX90640Hub:
    def __init__(self, app):
        self.app = app
        self.url = self.app.config['SERVER_SOCK']
        self.lock = Lock()
        self.latest = {
            't_max': None,
            'array': np.zeros((24, 32)),
            'timestamp': None
        }
        self.running = True
        Thread(target=self._worker, daemon=True).start()
        self.app.mlx_hub = self  # per accesso esterno se serve

    def _worker(self):
        import socketio as socketio_client  # client lato Python
        sio = socketio_client.Client()

        @sio.event
        def connect():
            logger.info("MLX90640 WebSocket connected")

        @sio.event
        def disconnect():
            logger.warning("MLX90640 WebSocket disconnected")

        @sio.on('sensor_data_mlx90640')
        def on_data(data):
            try:
                t_max = float(data['t_max'])
                timestamp = datetime.datetime.fromtimestamp(data['timestamp'] / 1000).strftime("%d-%m-%Y %H:%M:%S")
                array = np.zeros((24, 32))

                for k, v in data.items():
                    if k.startswith('mlx90640.array.'):
                        row = int(k.split('.')[-2])
                        col = int(k.split('.')[-1])
                        array[row, col] = float(v)

                with self.lock:
                    self.latest['t_max'] = t_max
                    self.latest['array'][:] = array
                    self.latest['timestamp'] = timestamp

               
                if socketio:
                    socketio.emit('mlx90640_update', {
                        't_max': round(t_max, 2),
                        'timestamp': timestamp,
                        'array': array.flatten().tolist()
                    })
            except Exception as e:
                logger.error(f"Error MLX90640: {e}")

        while self.running:
            try:
                if getattr(self, "_force_reconnect", False):
                    if sio.connected:
                        sio.disconnect()
                    self._force_reconnect = False
                if not sio.connected:
                    sio.connect(self.url, wait_timeout=10)
                time.sleep(0.2)
            except Exception as e:
                logger.error(f"Reconnect MLX90640 failed: {e}")
                if self.running:
                    time.sleep(5)

    def get_latest(self):
        with self.lock:
            return (
                self.latest['t_max'],
                self.latest['array'].copy(),
                self.latest['timestamp']
            )

#CLIENT FOR REST API
# class mlx90640_view_rest:
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
        new_rest = f"http://{ip}:{cfg['API_SERVER']['PORT_REST']}"
        new_sock = f"http://{ip}:{cfg['API_SERVER']['PORT_SOCK']}"

        current_app.config['SERVER_REST'] = new_rest
        current_app.config['SERVER_SOCK'] = new_sock

        current_app.mlx_hub.url = new_sock
        current_app.mlx_hub._force_reconnect = True

        update_ip_rest(ip)
        update_ip_sock(ip)

        return dict(server_rest=new_rest,
                    server_sock=new_sock)


class csv_view:
    def __init__(self, url):
        self.url = url + '/api/v1.0/get_csv_data'

    def update(self):
        data = requests.get(self.url).json()
        for val in data.keys():
            data[val] = round(float(data[val]), 2)
        return data
    

