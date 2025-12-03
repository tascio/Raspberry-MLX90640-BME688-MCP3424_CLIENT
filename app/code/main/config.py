import configparser, os

BASEDIR = os.path.abspath(os.path.dirname(__file__))
config_path = os.path.join(BASEDIR, '../shared/config.cfg')

cfg = configparser.ConfigParser()
cfg.optionxform = str
cfg.read(config_path)

def update_ip_rest(ip):
    try:
        cfg['API_SERVER']['IP_REST'] = ip
        with open(config_path, 'w') as configfile:
            cfg.write(configfile)
        return True
    except Exception as e:
        return str(e)
    
def update_ip_sock(ip):
    try:
        cfg['API_SERVER']['IP_SOCK'] = ip
        with open(config_path, 'w') as configfile:
            cfg.write(configfile)
        return True
    except Exception as e:
        return str(e)