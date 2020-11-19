# the name of allah
# tested on windows 7

import subprocess
import os
from bs4 import BeautifulSoup

# all of wifi profiles
# netsh wlan show profiles

# show wifi profile password
# netsh wlan show profile [wifi_name] key=clear


class Wifi():

    class Profile:
        def __init__(self):
            try:
                self.cwd = os.getcwd() + '\\clients'
                subprocess.check_output(f"netsh wlan export profile folder={self.cwd} key=clear", shell=True)

            except subprocess.CalledProcessError as msg:
                print(f'error! {msg}')

        def get_ssid(self):
            files = os.listdir(self.cwd)
            ssid = []
            try:
                for f in files:
                    with open(self.cwd+'\\' + f, 'r') as f:
                        ssid.append(BeautifulSoup(f.read(), "xml").find('name').get_text())
                return ssid
            except:
                print('error!')
                raise

        def get_password(self, *args):
            files = os.listdir(self.cwd)
            if len(args) and type(args[0]) == str:
                try:
                    for f in files:
                        with open(self.cwd + '\\' + f, 'r') as f:
                            data = BeautifulSoup(f.read(), "xml")
                            if data.find('name').get_text() == args[0]:
                                if data.find('sharedKey').find('protected').get_text().lower() == 'true':
                                    raise WindowsError('Please run the script as administrator!')
                                password = data.find('sharedKey').find('keyMaterial').get_text()
                                f.close()
                                return password

                except:
                    print('Error:')
                    raise
            else:
                password = {}
                try:
                    for f in files:
                        with open(self.cwd + '\\' + f, 'r') as f:
                            data = BeautifulSoup(f.read(), "xml")
                            if data.find('sharedKey').find('protected').get_text().lower() == 'true':
                                raise WindowsError('Please run the script as administrator!')
                            password[data.find('name').get_text()] = data.find('sharedKey').find('keyMaterial').get_text()
                    return password
                except:
                    print('Error:')
                    raise