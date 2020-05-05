from twisted.python import log
from twisted.internet import reactor
from . import rfb
from .vnc_action_helper import VncActionHelper


class HeadlessVncClient:
    action_helper: VncActionHelper = None

    def __init__(self, reactor_int=None):
        self.protocol = None
        self.alive = 1
        self.reactor_int = reactor_int
        self.action_helper = VncActionHelper()

    def set_protocol(self, protocol):
        self.protocol = protocol
        self.action_helper.set_protocol(protocol)

    # noinspection PyUnresolvedReferences
    def mainloop(self):
        no_work = self.reactor_int(self) if self.reactor_int else 1
        if self.alive:
            reactor.callLater(no_work and 0.020, self.mainloop)

    # noinspection PyUnresolvedReferences
    def stop(self):
        self.alive = 0
        reactor.removeAll()
        reactor.iterate()
        reactor.stop()


# noinspection PyAbstractClass,PyPep8Naming,PyUnusedFunction,PyMethodMayBeStatic
class RFBToGUI(rfb.RFBClient):

    remoteframebuffer = None
    connection_made_handler = None
    update_rectangle_handler = None

    def vncConnectionMade(self):
        self.remoteframebuffer = self.factory.remoteframebuffer
        self.remoteframebuffer.set_protocol(self)
        self.setEncodings(self.factory.encodings)
        self.setPixelFormat()            #set up pixel format to 32 bits
        self.framebufferUpdateRequest()  #request initial screen update
        if self.connection_made_handler:
            self.connection_made_handler()


    def vncRequestPassword(self):
        if self.factory.password is not None:
            self.sendPassword(self.factory.password)
        else:
            raise ValueError("Password must be provided")

    def beginUpdate(self):
        """begin series of display updates"""

    # noinspection PyUnusedLocal
    def commitUpdate(self, rectangles=None):
        """finish series of display updates"""
        self.framebufferUpdateRequest(incremental=1)

    def updateRectangle(self, x, y, width, height, data):
        """new bitmap data"""
        if self.update_rectangle_handler:
            self.update_rectangle_handler(x, y, width, height, data)

    def copyRectangle(self, srcx, srcy, x, y, width, height):
        """copy src rectangle -> destination"""

    def fillRectangle(self, x, y, width, height, color):
        """fill rectangle with one color"""

    def bell(self):
        print("bell")

    def copy_text(self, text):
        print(f"Clipboard: {text}")


# noinspection PyPep8Naming,PyMethodMayBeStatic,PyUnusedFunction
class VncFactory(rfb.RFBFactory):
    """A factory for remote frame buffer connections."""
    
    def __init__(self, remoteframebuffer, *args, **kwargs):
        rfb.RFBFactory.__init__(self, *args, **kwargs)
        self.remoteframebuffer = remoteframebuffer
        self.protocol = RFBToGUI

        self.encodings = [
            rfb.COPY_RECTANGLE_ENCODING,
            rfb.RAW_ENCODING,
        ]

    def assign_update_rectangle_handler(self, handler):
        self.protocol.update_rectangle_handler = handler

    def assign_connection_made_handler(self, handler):
        self.protocol.connection_made_handler = handler

    def buildProtocol(self, addr):
        return rfb.RFBFactory.buildProtocol(self, addr)

    # noinspection PyUnusedLocal
    def clientConnectionLost(self, connector, reason):
        log.msg(f"connection lost: {reason.getErrorMessage()}\n")
        # noinspection PyUnresolvedReferences
        reactor.stop()

    # noinspection PyUnusedLocal
    def clientConnectionFailed(self, connector, reason):
        log.msg(f"cannot connect to server: {reason.getErrorMessage()}\n")
        # noinspection PyUnresolvedReferences
        reactor.stop()


# noinspection PyUnresolvedReferences
def connect(host, port, password,
            reactor_int=None,
            connection_made_handler=None,
            update_rectangle_handler=None):
    remoteframebuffer = HeadlessVncClient(reactor_int)
    factory = VncFactory(remoteframebuffer, password)

    if update_rectangle_handler:
        factory.assign_update_rectangle_handler(update_rectangle_handler)

    if connection_made_handler:
        factory.assign_connection_made_handler(connection_made_handler)

    reactor.connectTCP(host, port, factory)
    reactor.callLater(0.1, remoteframebuffer.mainloop)
    reactor.run()
