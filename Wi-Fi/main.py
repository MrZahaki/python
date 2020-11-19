from wifi import Wifi

if __name__ == '__main__':
    # Show saved Wi-Fi profiles on the system
    prof = Wifi.Profile()
    ssid = prof.get_ssid()
    print(ssid)
    print(prof.get_password(ssid[0]))