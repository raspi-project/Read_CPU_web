# monitor.py
import psutil
import subprocess

def get_cpu_temp():
    try:
        output = subprocess.check_output("vcgencmd measure_temp", shell=True).decode()
        temp = float(output.replace("temp=", "").replace("'C\n", ""))
        return temp
    except:
        return 0

def get_ram_info():
    mem = psutil.virtual_memory()
    total = round(mem.total / (1024 * 1024), 2)
    used = round(mem.used / (1024 * 1024), 2)
    percent = mem.percent
    return total, used, percent

def get_disk_info():
    disk = psutil.disk_usage('/')
    total = round(disk.total / (1024 * 1024 * 1024), 2)
    used = round(disk.used / (1024 * 1024 * 1024), 2)
    percent = disk.percent
    return total, used, percent

def get_all_stats():
    temp = get_cpu_temp()
    total_ram, used_ram, ram_percent = get_ram_info()
    total_disk, used_disk, disk_percent = get_disk_info()

    return {
        "temperature": temp,
        "total_ram": total_ram,
        "used_ram": used_ram,
        "ram_percent": ram_percent,
        "total_disk": total_disk,
        "used_disk": used_disk,
        "disk_percent": disk_percent
    }
