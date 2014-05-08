################################################################################
#                                                                              #
# UCOM                                                                         #
#                                                                              #
################################################################################
#                                                                              #
# LICENCE INFORMATION                                                          #
#                                                                              #
# This program is a computer graphical user interface.                         #
#                                                                              #
# copyright (C) 2014 William Breaden Madden                                    #
#                                                                              #
# This software is released under the terms of the GNU General Public License  #
# version 3 (GPLv3).                                                           #
#                                                                              #
# This program is free software: you can redistribute it and/or modify it      #
# under the terms of the GNU General Public License as published by the Free   #
# Software Foundation, either version 3 of the License, or (at your option)    #
# any later version.                                                           #
#                                                                              #
# This program is distributed in the hope that it will be useful, but WITHOUT  #
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or        #
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for    #
# more details.                                                                #
#                                                                              #
# For a copy of the GNU General Public License, see                            #
# <http://www.gnu.org/licenses/>.                                              #
#                                                                              #
################################################################################

from __future__ import print_function
import os
import sys
import traceback
import logging
import time
import Xlib.rdb, Xlib.X, Xlib.XK

class Program(object):

    def __init__(
        self,
        parent = None
        ):
        # name
        self.name                      = "UCOM"
        # commands and options
        self.commandxterm              = ['/usr/bin/xterm']
        self.commandGNOMETerminal      = ['/usr/bin/gnome-terminal']
        self.commandDefaultTerminal    = self.commandxterm
        # startup procedures
        self.StartupProcedures = [
                                       '/usr/games/xphoon',
                                       #'/usr/bin/xcalc',
                                       #'/usr/bin/dmenu',
        ]
        self.requiredXlibVersion       = (0, 14)
        self.maximumNumberOfExceptions = 25
        self.releaseModifier           = Xlib.X.AnyModifier << 1
        # logging
        global logger
        logger = logging.getLogger(__name__)
        logging.basicConfig()
        logger.level = logging.INFO

    def run(self):
        logger.info("running {name}".format(name = self.name))
        # If the Xlib version available is less than that required, there is an
        # error.
        if Xlib.__version__ < program.requiredXlibVersion:
            logger.info(
                "Xlib version 0.14 is required; {version} was found".
                format(
                    version='.'.join(str(i) for i in Xlib.__version__)
                )
            )
            print(
                "Xlib version 0.14 is required; {version} was found".
                format(
                    version='.'.join(str(i) for i in Xlib.__version__),
                    file = sys.stderr
                )
            )
            return 2
        display, appname, resource_database, args = \
            Xlib.rdb.get_display_opts(Xlib.rdb.stdopts)
        try:
            windowManager = WindowManager(display)
        except ExceptionNoUnmanagedScreens:
            logger.info("no unmanaged screens found")
            print("no unmanaged screens found", file = sys.stderr)
            return 2
        try:
            windowManager.mainLoop()
        except KeyboardInterrupt:
            logger.info("keyboard interrupt")
            return 0
        except SystemExit:
            logger.info("system exit")
            raise
        except:
            logger.info("unknown exception")
            logger.info("traceback:")
            traceback.print_exc()
            return 1

class WindowManager(object):

    def __init__(
        self,
        display
        ):
        self.display = display
        self.dragWindow = None
        self.dragOffset = (0, 0)
        # If there is a display, get a name for it.
        if display is not None:
            os.environ['DISPLAY'] = display.get_display_name()
        self.enterCodes = set(
            code for code,
            index in self.display.keysym_to_keycodes(Xlib.XK.XK_Return)
        )
        self.screens = []
        for screen_id in xrange(0, display.screen_count()):
            if self.redirectScreenEvents(screen_id):
                self.screens.append(screen_id)
        if len(self.screens) == 0:
            raise ExceptionNoUnmanagedScreens()
        self.display.set_error_handler(self.XErrorHandler)
        # Run startup procedures.
        self.startup()
        # Prepare to handle events.
        self.event_dispatch_table = {
            Xlib.X.KeyPress:         self.handleKeyPress,
            Xlib.X.KeyRelease:       self.handleKeyRelease,
            Xlib.X.ButtonPress:      self.handleButtonPress,
            Xlib.X.ButtonRelease:    self.handleButtonRelease,
            Xlib.X.MapRequest:       self.handleMapRequest,
            Xlib.X.MappingNotify:    self.handleMappingNotify,
            Xlib.X.MotionNotify:     self.handleMotionNotify,
            Xlib.X.ConfigureRequest: self.handleConfigureRequest,
        }

    def startup(self):
        '''
        This method runs the startup procedures (system commands) for the
        interface environment.
        '''
        for procedure in program.StartupProcedures:
            self.system([procedure])

    def redirectScreenEvents(
        self,
        screen_id
        ):
        '''
        This method attempts to redirect the screen events and returns True on
        success.
        '''
        rootWindow = self.display.screen(screen_id).root
        errorCatcher = Xlib.error.CatchError(Xlib.error.BadAccess)
        mask = Xlib.X.SubstructureRedirectMask
        rootWindow.change_attributes(
            event_mask = mask,
            onerror = errorCatcher
        )
        self.display.sync()
        error = errorCatcher.get_error()
        if error:
            return False
        # Detect Alt Enter.
        for code in self.enterCodes:
            rootWindow.grab_key(
                code,
                Xlib.X.Mod1Mask & ~program.releaseModifier,
                1,
                Xlib.X.GrabModeAsync,
                Xlib.X.GrabModeAsync
            )
        # Detect window grab.
        for window in rootWindow.query_tree().children:
            logger.info(
                "detecting grab events for window {0}".
                format(window)
            )
            self.windowGrabEvents(window)
        return True

    def mainLoop(self):
        '''
        Loop until there is a Ctrl C interruption or exceptions have occurred
        more than the specified maximum number of exceptions.
        '''
        errorCount = 0
        while True:
            try:
                self.handleEvent()
            except (KeyboardInterrupt, SystemExit):
                raise
            except:
                errorCount += 1
                if errorCount > program.maximumNumberOfExceptions:
                    raise
                traceback.print_exc()

    def handleEvent(self):
        '''
        Wait for the next event and handle it.
        '''
        try:
            event = self.display.next_event()
        except Xlib.error.ConnectionClosedError:
            logger.info("display connection closed by server")
            print("display connection closed by server", file = sys.stderr)
            raise KeyboardInterrupt
        if event.type in self.event_dispatch_table:
            handler = self.event_dispatch_table[event.type]
            handler(event)
        else:
            logger.info("unhandled event: {event}".format(event = event))

    def handleKeyPress(
        self,
        event
        ):
        if event.state & Xlib.X.Mod1Mask and event.detail in self.enterCodes:
            # Alt Enter: start terminal
            self.system(program.commandDefaultTerminal)

    def handleKeyRelease(
        self,
        event
        ):
        pass

    def handleButtonPress(
        self,
        event
        ):
        if event.detail == 3:
            # right-click: raise window
            event.window.configure(stack_mode = Xlib.X.Above)

    def handleButtonRelease(
        self,
        event
        ):
        self.dragWindow = None

    def handleMapRequest(self, event):
        event.window.map()
        self.windowGrabEvents(event.window)

    def windowGrabEvents(
        self,
        window
        ):
        '''
        Detect right-click and drag events on the window.
        '''
        window.grab_button(
            3,
            0,
            True,
            Xlib.X.ButtonMotionMask \
                | Xlib.X.ButtonReleaseMask \
                | Xlib.X.ButtonPressMask,
            Xlib.X.GrabModeAsync,
            Xlib.X.GrabModeAsync,
            Xlib.X.NONE,
            Xlib.X.NONE,
            None
        )

    def handleMappingNotify(
        self,
        event
        ):
        self.display.refresh_keyboard_mapping(event)

    def handleMotionNotify(
        self,
        event
        ):
        '''
        Drag a window.
        '''
        if event.state & Xlib.X.Button3MotionMask:
            if self.dragWindow is None:
                # start drag
                self.dragWindow = event.window
                geometry = self.dragWindow.get_geometry()
                self.dragOffset = \
                    geometry.x - event.root_x, \
                    geometry.y - event.root_y
            else:
                # continue drag
                x, y = self.dragOffset
                self.dragWindow.configure(
                    x = x + event.root_x,
                    y = y + event.root_y
                )

    def handleConfigureRequest(
        self,
        event
        ):
        window = event.window
        arguments = {'border_width': 3}
        if event.value_mask & Xlib.X.CWX:
            arguments['x']          = event.x
        if event.value_mask & Xlib.X.CWY:
            arguments['y']          = event.y
        if event.value_mask & Xlib.X.CWWidth:
            arguments['width']      = event.width
        if event.value_mask & Xlib.X.CWHeight:
            arguments['height']     = event.height
        if event.value_mask & Xlib.X.CWSibling:
            arguments['sibling']    = event.above
        if event.value_mask & Xlib.X.CWStackMode:
            arguments['stack_mode'] = event.stack_mode
        window.configure(**arguments)

    def system(
        self,
        command
        ):
        '''
        This method forks a command and then disowns it.
        '''
        if os.fork() != 0:
            return
        try:
            # child
            os.setsid() # become session leader
            if os.fork() != 0:
                os._exit(0)
            os.chdir(os.path.expanduser('~'))
            os.umask(0)
            # Close all file descriptors.
            import resource
            maximumNumberOfFileDescriptors = resource.getrlimit(
                resource.RLIMIT_NOFILE
            )[1]
            if maximumNumberOfFileDescriptors == resource.RLIM_INFINITY:
                maximumNumberOfFileDescriptors = 1024
            for fileDescriptor in xrange(maximumNumberOfFileDescriptors):
                try:
                    os.close(fileDescriptor)
                except OSError:
                    pass
            # Open /dev/null for stdin, stdout and stderr.
            os.open('/dev/null', os.O_RDWR)
            os.dup2(0, 1)
            os.dup2(0, 2)
            os.execve(
                command[0],
                command,
                os.environ
            )
        except:
            try:
                # error in child process
                logger.info("error in child process")
                print("error in child process:", file = sys.stderr)
                traceback.print_exc()
            except:
                pass
            sys.exit(1)

    def XErrorHandler(
        self,
        error,
        request
        ):
        logger.info("X protocol error: {0}".format(error))
        print("X protocol error: {0}".format(error), file = sys.stderr)

class ExceptionNoUnmanagedScreens(Exception):
    pass

def main():
    global program
    program = Program()
    program.run()

if __name__ == '__main__':
    sys.exit(main())
