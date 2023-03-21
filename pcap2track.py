#!/usr/bin/env python
# coding:utf-8
import argparse
import os
from tempfile import NamedTemporaryFile
import struct
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D


def unpack_mouse_data(data: bytearray):
    # 解包鼠标数据包
    button_state = data[0]
    if len(data) == 4:
        (x, y) = struct.unpack_from("<bb", data, offset=1)
    elif len(data) == 8:
        (x, y) = struct.unpack_from("<bb", data, offset=1)
    elif len(data) == 13:
        (x, y) = struct.unpack_from("<hh", data, offset=2)

    # 返回解包的数据
    return button_state, x, y


def state2text(button_state: int) -> str:
    button_map = {
        0x0: 'No Button',
        0x1: 'Left Click',
        0x2: 'Right Click',
        0x4: 'Middle Click',
    }
    states = []
    if button_state == 0:
        states.append(button_map[0])
    else:
        for key in button_map:
            if button_state & key:
                states.append(button_map[key])

    return " And ".join(states)


def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(
        description='Read mouse data from pcapng file and plot mouse trajectory.')
    parser.add_argument('pcapng_file', help='path to the pcapng file')
    parser.add_argument('button_mask', metavar='button_mask', default=15, type=int, choices=range(16), nargs='?',
                        help='a mask of mouse button states to be included in the trace to display, default is 15')
    parser.add_argument('-o', '--output', default='output.png',
                        help='output file path, default is "output.png"')
    args = parser.parse_args()

    # 通过tshark解析pcapng文件，获取鼠标数据包
    tmpfile = NamedTemporaryFile(delete=False)
    tmpfile.close()

    command = "tshark -r %s -T fields -e usbhid.data -e usb.capdata > %s" % (
        args.pcapng_file, tmpfile.name)
    os.system(command)

    with open(tmpfile.name, 'r') as f:
        lines = f.readlines()

    os.unlink(tmpfile.name)

    x_position = y_position = 0
    last_button_state = -1

    # 绘制鼠标轨迹图
    fig, ax = plt.subplots()
    colormap = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f',
                '#bcbd22', '#17becf', '#aec7e8', '#ffbb78', '#98df8a', '#ff9896', '#c5b0d5', '#c49c94']

    x_values = [x_position]
    y_values = [y_position]

    states = []

    # 解析鼠标数据包，获取鼠标轨迹坐标
    for line in lines:
        capdata = line.strip().replace(':', '')
        if capdata:
            data = bytearray.fromhex(capdata)
            button_state, x_offset, y_offset = unpack_mouse_data(data)
            x_position += x_offset
            y_position -= y_offset

            if button_state != last_button_state:
                if len(x_values) > 1:
                    color = colormap[last_button_state]
                    ax.plot(x_values, y_values, color=color)
                    x_values = [x_values[-1]]
                    y_values = [y_values[-1]]
                last_button_state = button_state

            # 筛选符合条件的按钮状态
            if button_state & args.button_mask or (args.button_mask & 0b1000 and not button_state):
                if button_state not in states:
                    states.append(button_state)
            else:
                x_values = []
                y_values = []

            x_values.append(x_position)
            y_values.append(y_position)
        else:
            pass

    if len(x_values) > 1:
        color = colormap[last_button_state]
        ax.plot(x_values, y_values, color=color)

    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_title('Mouse Trajectory')

    handles = [Line2D([], [], color=colormap[i], label=state2text(i))
               for i in states]
    plt.legend(handles=handles)
    plt.savefig(args.output)
    plt.show()


if __name__ == "__main__":
    main()
