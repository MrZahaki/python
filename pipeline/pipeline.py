import multiprocessing
import queue


class Pipeline(multiprocessing.Process):
    # type LiveProcessing, DeadProcessing or timeout value
    def __init__(self, max_size=None, io_buffer_size=10, pipe_type='LiveProcessing'):
        super(Pipeline, self).__init__(daemon=True)
        manager = multiprocessing.Manager()
        # self.namespace = manager.Namespace()
        self.pipeline = manager.list([])
        self.input_line = multiprocessing.Queue(maxsize=io_buffer_size)
        self.output_line = multiprocessing.Queue(maxsize=io_buffer_size)
        self.max_size = max_size

        self.put = self.__call__
        self.get = self.output_line.get

        # block value, timeout
        if pipe_type == 'LiveProcessing':
            self.process_type = (False, None)
        elif pipe_type == 'DeadProcessing':
            self.process_type = (True, None)
        elif type(pipe_type) == float:
            self.process_type = (True, pipe_type)
        else:
            raise ValueError

    def __call__(self, *args):
        try:
            args = list(args)
            while args:
                self.input_line.put(args.pop(), block=self.process_type[0], timeout=self.process_type[1])
        except (queue.Empty, queue.Full):
            pass

    def run(self):
        while 1:
            try:
                while 1:
                    ret_val = self.pipeline[-1](self.input_line.get())
                    for i in self.pipeline[-2::-1]:
                        ret_val = i(ret_val)
                    self.output_line.put(ret_val, block=self.process_type[0], timeout=self.process_type[1])

            except IndexError:
                while not len(self.pipeline):
                    pass

    def append(self, *args):
        for i in args:
            self.pipeline.append(i)

    # def __delattr__(self, index):
    #     del self.pipeline[int(index)]

    def __len__(self):
        return len(self.pipeline)

    def __getitem__(self, key):
        print('key',key)
