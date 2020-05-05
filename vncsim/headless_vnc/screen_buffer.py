from twisted.internet import reactor
from types import FunctionType
from typing import NamedTuple
from PIL import Image


#---- INITIALIZATION

Image.preinit()
Image.init()


#---- CONFIGURATION

class ScreenBufferConfig(NamedTuple):
    signal_min_width: int
    signal_min_height: int
    signal_timeout: int


DefaultScreenBufferConfig = ScreenBufferConfig(
    signal_min_width=70,
    signal_min_height=70,
    signal_timeout=1
)


#---- IMPLEMENTATION

class ScreenBuffer:
    config: ScreenBufferConfig = None
    buffer: Image = None
    flush_handler: FunctionType = None
    schedule_event = None

    def __init__(self,
                 flush_handler: FunctionType = None,
                 config: ScreenBufferConfig = DefaultScreenBufferConfig):
        self.config = config
        if flush_handler:
            self.flush_handler = flush_handler

    # noinspection PyUnusedLocal
    def on_buffer_ready(self):
        self.schedule_event = None
        if self.buffer and self.flush_handler:
            self.flush_handler(self, self.buffer)

    # noinspection PyUnusedLocal
    def vnc_update_rectangle_handler(self, x, y, width, height, data):
        size = (width, height)
        update = Image.frombytes('RGB', size, data, 'raw', 'RGBX')

        if not self.buffer:
            self.buffer = update
        elif self.buffer.size[0] < (x + width) \
                or self.buffer.size[1] < (y + height):
            new_size = (
                max(x + width, self.buffer.size[0]),
                max(y + height, self.buffer.size[1])
            )
            new_screen = Image.new("RGB", new_size, "black")
            new_screen.paste(self.buffer, (0, 0))
            new_screen.paste(update, (x, y))
            self.buffer = new_screen
        else:
            self.buffer.paste(update, (x, y))

        if width >= self.config.signal_min_width \
                and height >= self.config.signal_min_height:
            if self.schedule_event:
                self.schedule_event.cancel()
            self.schedule_event = reactor.callLater(
                self.config.signal_timeout,
                self.on_buffer_ready
            )
            print("Screen buffer: received the significant changes. Waiting for 3 secs more...")
