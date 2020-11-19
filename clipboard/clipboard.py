import win32clipboard
import time
import threading
import queue
from _queue import Empty
""" Executes python code directly from the clipboard."""


class Clipboard:
    data_types = [win32clipboard.CF_HDROP,  # A tuple of Unicode filenames.
                  win32clipboard.CF_UNICODETEXT,  # A unicode object.
                  win32clipboard.CF_OEMTEXT,  # A string object.
                  win32clipboard.CF_TEXT,  # A string object.
                  win32clipboard.CF_ENHMETAFILE,  # A string with binary data obtained from GetEnhMetaFileBits
                  win32clipboard.CF_METAFILEPICT,
                  # A string with binary data obtained from GetMetaFileBitsEx (currently broken)
                  win32clipboard.CF_BITMAP]

    def __init__(self, period=0.7):
        self.functions = [self.event_handler]
        self.threads = []
        self.period = period
        try:

            self.queue = queue.Queue()

            # create threads and queues
            for i in range(len(self.functions)):
                self.threads.append(threading.Thread(target=self.run, daemon=True, args=(len(self.threads),)))
                self.queue.put(i)

        except:
            print('Initialization error!')
            raise

    def on_change_event_start(self):
        try:
            for i in self.threads:
                i.start()

            # The server blocks all active threads
            # del self.threads[:]
            self.queue.join()

        except:
            print('Clipboard failed to start!')
            raise

    def run(self, th_id):
        self.functions[self.queue.get()](th_id)
        # Indicate that a formerly enqueued task is complete.
        # Used by queue consumer threads. For each get() used to fetch a task,
        # a subsequent call to task_done() tells the queue that the processing on the task is complete.

        # If a join() is currently blocking,
        # it will resume when all items have been processed
        # (meaning that a task_done() call was received for every item that had been put() into the queue).
        self.queue.task_done()

    def on_change(self, data_type, content):
        pass

    def event_handler(self, thread_id):

        win32clipboard.OpenClipboard()
        for i in Clipboard.data_types:
            try:
                pre_code = win32clipboard.GetClipboardData(i)
                pre_type = i
                break
            except TypeError:
                code = None
        win32clipboard.CloseClipboard()

        while 1:
            time.sleep(self.period)
            try:
                win32clipboard.OpenClipboard()
                for i in Clipboard.data_types:
                    try:
                        current_code = win32clipboard.GetClipboardData(i)
                        current_type = i
                        break
                    except TypeError:
                        current_code = current_type = None
            except:
                continue

            win32clipboard.CloseClipboard()
            if current_code and not (current_type == pre_type and current_code == pre_code):
                self.on_change(current_type, current_code)
                pre_type = current_type
                pre_code = current_code
