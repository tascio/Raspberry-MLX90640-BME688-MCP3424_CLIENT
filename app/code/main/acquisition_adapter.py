from threading import Lock, Thread, Event
from main.models import csv_view, csv_path
from main.logger import logger
from time import sleep
from flask import current_app
from datetime import datetime

class CSV_adapter:
    def __init__(self, pace=60):#900
        self.pace = pace
        self.remaining_time = pace
        self.lock = Lock()
        self.stop_event = Event()
        self.csv = csv_view(current_app.config['SERVER_REST'])
        self.d = datetime.now().strftime("%d-%m-%Y_%H:%M:%S")
        self.file = open(f'{csv_path}{self.d}_test.csv', 'a')
    
    def refresh(self):
        try:
            with self.lock:
                data = self.csv.update()
                row = ",".join([
                                str(data['dv']),
                                str(data['air_temp']),
                                str(data['humidity']),
                                str(data['curr_gbp']),
                                str(data['fpga']),
                                str(data['wri1']),
                                str(data['wri2']),
                                str(data['wri3']),
                                str(data['wri4']),
                                str(data['wri5']),
                                str(data['wri6']),
                                str(data['wri7']),
                                str(data['wri8']),
                                str(data['wri9']),
                                str(data['wri10']),
                                str(data['wri11']),
                                str(data['wri12']),
                                str(data['wri13']),
                                str(data['wri14']),
                                str(data['wri15']),
                                str(data['wri16']),
                                str(data['wri17']),
                                str(data['wri18']),
                            ]) + "\n"
                self.file.write(row)
                self.file.flush()
                return True
        except Exception as e:
            logger.error(f'CSV adapter error {e}')
            return False
    
    def data_polling(self, app):
        with app.app_context():
            while not self.stop_event.is_set():
                response = self.refresh()
                if response:
                    logger.info('Refresh and Polling CSV adapter ok')
                    self.remaining_time =self.pace
                    while self.remaining_time > 0 and not self.stop_event.is_set():
                        sleep(1)
                        self.remaining_time -= 1
            self.file.close()
            logger.info("CSV acquisition stopped")
    
    def stop(self):
        self.stop_event.set()

            
