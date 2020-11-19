from clipboard import Clipboard


class Main(Clipboard):
    def __init__(self):
        super(Main, self).__init__(period=0.5)
        self.on_change_event_start()

    def on_change(self, data_type, content):
        print(data_type, content)


if __name__ == '__main__':
    m = Main()
