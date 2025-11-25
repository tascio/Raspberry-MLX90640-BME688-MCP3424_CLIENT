import subprocess
class wet_view:
    def get_temp(host):
        cmd = (
            f'sshpass -p "" ssh -o StrictHostKeyChecking=no root@{host} '
            '"/wr/bin/wrs_dump_shmem | grep -i \\.temp | grep -v \'attempts\'" '
            '| awk \'{print $2}\' | awk \'NR!=2 && NR!=3 && NR!=4 { printf \"%s\\t\", $0 }\''
        )
        result = subprocess.check_output(cmd, shell=True, text=True)
        return result.strip().split('\t')
    
t = wet_view()
print(wet_view.get_temp("192.168.1.254"))
#example output
#['49.875000', '0.000', '0.000', '0.000', '0.000', '0.000', '0.000', '0.000', '0.000', '0.000', '0.000', '0.000', '0.000', '0.000', '0.000', '0.000', '0.000', '0.000', '0.000']
