![](images/logo_ucom.png)

UCOM is a minimal computer graphical user interface. It is written in Python and uses [Xlib](http://xorg.freedesktop.org/wiki/ProgrammingDocumentation/) via the [Python X Library](http://python-xlib.sourceforge.net/).

Xlib is an X Window System protocol client library written in C. It features functions for interacting with an X server. The Python X Library is an X client library for Python programs written in Python.

# screenshots

![](images/screenshot_1.png)

# setup

For running on Ubuntu, a prerequisite is the Python X Library.

```Bash
sudo apt-get -y install python-xlib
```

In order to have the Xphoon background, install Xphoon.

```Bash
sudo apt-get -y install xphoon
```

# running

## running in a new X session (via login)

In order to make UCOM available as session option at login, the file UCOM.desktop should be added to the directory `/usr/share/xsessions`. Its contents should be something like the following (with changes to the user name and directories as necessary):

```Bash
[Desktop Entry]
Encoding=UTF-8
Name=UCOM                          
Comment=UCOM -- X11 desktop environment
Exec=/usr/bin/python /home/user/ucom/ucom.py
Icon=/home/user/ucom/images/icon_ucom.png
Type=Application
```

## running from an existing X session

To manually run UCOM in an X server from within an X server session, start a new X server on display 1 (as opposed to display 0). To do this, engage another teletype (tty) device (`Ctrl` `Alt` `F1`) and enter a command such as the following:

```Bash
xinit /usr/bin/python /home/user/ucom/ucom.py -- :1
```

# usage

To focus on a window, hover on it. To bring a window to the foreground, right-click it. To move a window, right-click it and drag. To open a new terminal, press `Alt` `Enter`.

# testing

UCOM can be tested using [Xephyr](http://www.freedesktop.org/wiki/Software/Xephyr/).

```Bash
sudo apt-get -y install xserver-xephyr
```

UCOM can be run in Xephyr in a way such as the following:

```Bash
Xephyr -screen 1024x768 -br :1
DISPLAY=:1 python ucom.py
```

# useful programs

Some programs are of particular use with UCOM.

## Maximus

Maximus is a program that is designed to maximise the windows of running programs. It can be useful for clarity and for efficient use of space.

```Bash
sudo apt-get -y install maximus
```

## ranger

Ranger is a text-based file and directory manager written in Python.

```Bash
sudo apt-get -y install ranger
```

# future

Tiling capabilities are under consideration.
