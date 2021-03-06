# Copyright (C) 2013 Internet Systems Consortium.
#
# Permission to use, copy, modify, and distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND INTERNET SYSTEMS CONSORTIUM
# DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS SOFTWARE INCLUDING ALL
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL
# INTERNET SYSTEMS CONSORTIUM BE LIABLE FOR ANY SPECIAL, DIRECT,
# INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING
# FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT,
# NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION
# WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

# Author: Wlodzimierz Wencel

from _pyio import open
from lettuce.registry import world
from locale import str
import sys
import os
from features.softwaresupport.multi_server_functions import fabric_send_file, fabric_download_file,\
        fabric_remove_file_command, remove_local_file, fabric_sudo_command, configuration_file_name
from time import sleep


def forge_sleep(time, time_units):
    divide = 1.0
    if time_units == 'milliseconds' or time_units == 'millisecond':
        divide = 1000.0
    sleep(time * 1.0 / divide)


def test_pause(step):
    """
    Pause the test for any reason. Press any key to continue. 
    """
    def getch():
        import tty
        import termios
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            return sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
    getch()


def copy_file_from_server(step, remote_path):
    """
    Copy file from remote server via ssh. Address/login/password from init_all.py
    Path required.
    """
    fabric_download_file(remote_path, world.cfg["dir_name"] + '/downloaded_file')


def send_file_to_server(step, local_path, remote_path):
    """
    Send file to remote server via ssh. Address/login/password from init_all
    Two paths required. 
    Local - relative to lettuce directory
    Remote - absolute 
    """
    fabric_send_file(local_path, remote_path)


def remove_file_from_server(step, remote_path):
    """
    Remove file from remote server.
    """
    fabric_remove_file_command(remote_path)


def strip_file(file_path):
    tmp_list = []
    tmp = open(file_path, 'r')
    for line in tmp:
        line = line.strip()
        if len(line) < 1:
            continue
        elif line[0] == '#':
            continue
        else:
            tmp_list.append(line.strip())
    tmp.close()
    return tmp_list


def compare_file(step, local_path):
    """
    Compare two files, downloaded and local
    """
    if not os.path.exists(local_path):
        assert False, 'No local file %s' % local_path
    
    outcome = open(world.cfg["dir_name"] + '/file_compare', 'w')
    
    # first remove all commented and blank lines of both files
    downloaded_stripped = strip_file(world.cfg["dir_name"] + '/downloaded_file')
    local_stripped = strip_file(local_path)

    line_number = 1
    error_flag = True
    for i, j in zip(downloaded_stripped, local_stripped):
        if i != j:
            outcome.write('Line number: ' + str(line_number) + ' \n\tDownloaded file line: "' +
                          i.rstrip('\n') + '" and local file line: "' + j.rstrip('\n') + '"\n')
            error_flag = False
        line_number += 1
    if error_flag:
        remove_local_file(world.cfg["dir_name"] + '/file_compare')
        
    assert error_flag, 'Downloaded file is NOT the same as local. Check %s/file_compare for details'\
                       % world.cfg["dir_name"]
    
    if len(downloaded_stripped) != len(local_stripped):
        assert len(downloaded_stripped) > len(local_stripped), 'Downloaded file is part of a local file.'
        assert len(downloaded_stripped) < len(local_stripped), 'Local file is a part of a downlaoded life.'


def file_includes_line(step, condition, line):
    """
    Check if downloaded file contain line.
    """
    downloaded_stripped = strip_file(world.cfg["dir_name"] + '/downloaded_file')
    if condition is not None:
        if line in downloaded_stripped:
            assert False, 'Downloaded file does contain line: "%s" But it should NOT.' % line
    else:
        if line not in downloaded_stripped:
            assert False, 'Downloaded file does NOT contain line: "%s"' % line


def add_variable(step, variable_name, variable_val, type):
    """
    Define variable and add it to temporary list or to init_all.py file. 
    """
    import re
    assert not bool(re.compile('[^A-Z^0-9^_] + ').search(variable_name)),\
        "Variable name contain invalid characters (Allowed are only capital letters, numbers and sign '_')."
    
    if not type:
        #temporary
        if variable_name not in world.define:
            tmp = variable_val if variable_val.isdigit() else variable_val  
            world.define.append([variable_name, tmp])
    elif type:
        #permanent
        # TO: for same name change value
        imported = None
        try:
            imported = getattr(__import__('init_all', fromlist = [variable_name]), variable_name)
        except:
            init_all = open("features/init_all.py", "a")
            init_all.write("\n# USER VARIABLE:\n" + variable_name + " = " +
                           (variable_val if variable_val.isdigit() else '\"' + variable_val + '\"'))
            init_all.close()


def user_victory(step):
    from shutil import copy
    if not os.path.exists(world.cfg["dir_name"]):
        os.makedirs(world.cfg["dir_name"])
    copy('../doc/.victory.jpg', world.cfg["dir_name"] + '/celebrate_success.jpg')


def log_contains(step, server_type, condition, line):
    if server_type == "DHCP":
        log_file = world.cfg["dhcp_log_file"]
    elif server_type == "DNS":
        log_file = world.cfg["dns_log_file"]
    else:
        assert False, "No such name as: {server_type}".format(**locals())

    result = fabric_sudo_command('grep -c \"' + line + '\" ' + log_file)

    if condition is not None:
        if result.succeeded:
            assert False, 'Log contains line: "%s" But it should NOT.' % line
    else:
        if result.failed:
            assert False, 'Log does NOT contain line: "%s"' % line


def log_contains_count(step, server_type, count, line):
    if server_type == "DHCP":
        log_file = world.cfg["dhcp_log_file"]
    elif server_type == "DNS":
        log_file = world.cfg["dns_log_file"]
    else:
        assert False, "No such name as: {server_type}".format(**locals())

    result = fabric_sudo_command('grep -c \"' + line + '\" ' + log_file)

    if count != result:
        assert False, 'Log has {0} of expected {1} of line: "{2}".'.format(result, count, line)


def change_network_variables(value_name, value):
    if value_name == "source_port":
        world.cfg["source_port"] = int(value)
    elif value_name == "destination_port":
        world.cfg["destination_port"] = int(value)
    elif value_name == "client_link_local_address":
        world.cfg["cli_link_local"] = value
    elif value_name == "source_address":
        world.cfg["source_IP"] = value
    elif value_name == "destination_address":
        world.cfg["destination_IP"] = value
    elif value_name == "dns_iface":
        world.cfg["dns_iface"] = value
    elif value_name == "dns_address":
        world.cfg["dns_addr"] = value
    elif value_name == "dns_port":
        world.cfg["dns_port"] = int(value)
    else:
        assert False, "There is no possibility of configuration value named: {value_name}".format(**locals())


def execute_shell_script(path, arguments):
    result = fabric_sudo_command(path + ' ' + arguments, False)

    file_name = path.split("/")[-1] + '_output'
    file_name = configuration_file_name(1, file_name)

    #assert False, type(result.stdout)
    if not os.path.exists(world.cfg["dir_name"]):
        os.makedirs(world.cfg["dir_name"])

    myfile = open(world.cfg["dir_name"] + '/' + file_name, 'w')
    myfile.write('Script: ' + path)
    if arguments == '':
        arguments = "no arguments used!"
    myfile.write(unicode('\nwith arguments: ' + arguments + '\n'))
    if result.failed:
        myfile.write(unicode('\nStatus: FAILED\n'))
    else:
        myfile.write(unicode('\nStatus: SUCCEED\n'))

    myfile.write(unicode('\nScript stdout:\n' + result.stdout))
    myfile.close()