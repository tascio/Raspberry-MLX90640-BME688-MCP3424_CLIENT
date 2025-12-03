from flask import Flask, Response, render_template, current_app, Blueprint, jsonify, request, send_from_directory
from main.models import bme688_view, mcp3424_view, power_supply_view, wet_view, wet_edit, server_edit, csv_view, Threshold
from main import acquisition_manager
from main.utils import check_threshold, open_latest_csv
import os, requests
from main.logger import logger

views_bp = Blueprint('views', __name__)


@views_bp.route('/')
def index():
    url = current_app.config['SERVER_REST']
    serverIp = current_app.config['SERVER_REST'].split('//')[1].split(':')[0]

    power_supply = power_supply_view(url)
    power_supply = power_supply.get_model()

    wwrs = wet_view(url)
    wet_ip, wet_mac = wwrs.get_ip_mac()

    return render_template('page/index.html', wet_array=current_app.config['WA'], serverIp=serverIp, wet_ip=wet_ip, mac_wet=wet_mac, power_supply=power_supply)


# @views_bp.route('/video_feed')
# def video_feed():
#     #FOR REST API
#     # mlx_rest = mlx90640_view_rest(current_app.config['SERVER_REST'])
#     # return Response(
#     #     generate_frames(mlx_rest),
#     #     mimetype='multipart/x-mixed-replace; boundary=frame'
#     # )

#     #FOR WEBSOCKET
#     return Response(
#         generate_frames(current_app.config['mlx90640_websocket']),
#         mimetype='multipart/x-mixed-replace; boundary=frame'
#     )

# @views_bp.route('/tmax')
# def tmax():
#     #mlx90640_websocket = current_app.config['mlx90640_websocket']
#     mlx90640_websocket = mlx90640_view_rest(current_app.config['SERVER_REST'])

#     try:
#         t_max, _, timestamp = mlx90640_websocket.update()
#         return {'t_max': round(t_max, 2), 
#                 'timestamp': timestamp}
#     except Exception as e:
#         logger.error(f"TMAX endpoint {e}")
#         return {'t_max': None, 
#                 'timestamp': None}

@views_bp.route('/bme688')
def bme688():
    camera = bme688_view(current_app.config['SERVER_REST'])
    data = camera.update()
    return jsonify(data)

@views_bp.route('/mcp3424')
def mcp3424():
    camera = mcp3424_view(current_app.config['SERVER_REST'])
    data = camera.update()
    if Threshold.status:
        data['threshold'] = ''
        if check_threshold(data.get('converted'), Threshold.dc_th):
            data['threshold'] = "DC TRIGGERED<br>"
    return jsonify(data)

@views_bp.route('/wet')
def wet():
    camera = wet_view(current_app.config['SERVER_REST'])
    data = camera.update()
    if Threshold.status:
        data['threshold'] = ''
        if check_threshold(data.get('fpga'), Threshold.fpga_th):
            data['threshold'] += "FPGA TRIGGERED<br>"
        if check_threshold(data.get('wri1'), Threshold.wri1_th):
            data['threshold'] += "WRI1 TRIGGERED<br>"
        for port in current_app.config['WA'][2:]:
            if check_threshold(data[port], Threshold.wri2_18_th):
                data['threshold'] += f"{port} TRIGGERED<br>"

    return jsonify(data)

@views_bp.route('/power_supply')
def power_supply():
    camera = power_supply_view(current_app.config['SERVER_REST'])
    data = camera.update()
    return jsonify(data)

@views_bp.route('/csv')
def csv():
    data = csv_view(current_app.config['SERVER_REST'])
    csv = data.update()
    return jsonify(csv)

@views_bp.route('/read_csv')
def read_csv():
    file = open_latest_csv()
    f = open(file, 'r').readlines()
    return jsonify(f)

@views_bp.route('/start_acquisition')
def start_acquisition():
    if acquisition_manager.start():
        return jsonify(response="Acquisition started")
    else:
        return jsonify(response="Acquisition already running")

@views_bp.route('/stop_acquisition')
def stop_acquisition():
    if acquisition_manager.stop():
        return jsonify(response="Acquisition stopped")
    else:
        return jsonify(response="Acquisition not running")

@views_bp.route('/acquisition_status')
def acquisition_status():
    if acquisition_manager.adapter_instance is None:
        return jsonify(running=False)
    else:
        return jsonify(
            running=True,
            remaining_time=acquisition_manager.adapter_instance.remaining_time
        )

@views_bp.route('/start_threshold', methods=['POST'])
def start_threshold():
    try:
        if Threshold.status:
            return jsonify(response=f"Threshold already running")
        Threshold.status = True
        return jsonify(response=f"Threshold on")
    except Exception as e:
        return jsonify(response=f"Error {e}")

@views_bp.route('/stop_threshold')
def stop_threshold():
    if Threshold.status:
        Threshold.status = False
        return jsonify(response="Threshold stopped")
    else:
        return jsonify(response="Threshold not running")


@views_bp.route('/csv_list')
def csv_list():
    base_dir = '/app/acquisitions'
    files = [f for f in os.listdir(base_dir) if f.endswith('.csv')]
    return jsonify(files)

@views_bp.route('/csv/<path:filename>')
def csv_file(filename):
    base_dir = '/app/acquisitions'
    return send_from_directory(base_dir, filename)

    
@views_bp.route('/edit_wet_ip', methods=['POST'])
def edit_wet_ip():
    data = request.get_json()
    ip = data.get("set_wet_ip")
    mac = data.get("mac")

    wet = wet_edit(current_app.config['SERVER_REST'])

    res_ip = wet.update_ip(ip)
    
    res_arp = wet.update_arp(ip, mac)
    return jsonify(ip=res_ip, arp=res_arp)

@views_bp.route('/edit_server_ip', methods=['POST'])
def edit_server_ip():
    ip = request.get_json().get('server_ip')
    srv = server_edit(ip)
    res = srv.update(ip)
    return jsonify(res)


# @views_bp.route('/edit_ethers', methods=['GET'])
# def edit_ethers():
#     url = current_app.config['SERVER_REST']
#     res = requests.post(url + "/api/v1.0/edit_ethers", json={'ip' : '10.100.0.1', 'mac' : 'ff:ff:ff:ff:ff:ff'})
#     return jsonify(res.json())