
#
#  - Autorun script for Mac -
#
# change formatted_path to the location of ripsnort
# and change disk_device to the device of the dvd drive
# example:
#     set formatted_path to "/Users/ryan/Desktop/ripsnort"
#     set disk_device to "/dev/disk2"
#


set formatted_path to "/path/to/ripsnort"
set disk_device to "/dev/mydisk"


tell application "Terminal"
    activate
    set run_cmd to "/usr/bin/python " & formatted_path & "/ripsnort.py " & disk_device
    do script run_cmd
end tell
