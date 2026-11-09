#!/usr/bin/env python3


import webbrowser
import subprocess
import pathlib
import os
from pynput import keyboard


TYP_FILENAME = "render_image.typ"
PDF_FILENAME = "render_image.pdf"


# mutable global state is fine, actually
input_state = {}


def on_press(key):
    print(key.char)
    input_state[key.char] = True
    

def on_release(key):
    print(key.char)
    if input_state[key.char]: input_state[key.char] = False


def setup():
    listener = keyboard.Listener(
        on_press=on_press,
        on_release=on_release)

    typ_file = os.open(TYP_FILENAME, os.O_CREAT | os.O_WRONLY | os.O_NONBLOCK)
    dir_path = str(pathlib.Path(__file__).parent.resolve())
    print("Dir path:" + str(dir_path))
    if not webbrowser.open_new("file://home" + dir_path + "/" + PDF_FILENAME):
        print("failed to open browser")
    else:
        print("opened browser")

    subprocess.Popen(["typst", "watch", TYP_FILENAME])

    input_state['q'] = False
    return typ_file, listener


def render_sprite(pos, image_path):
    x, y = pos
    return f"#place(dx: {int(x)}pt, dy: {int(y)}pt)[#image(\"{image_path}\")]\n"


def commit_render(render_str, typst_fd):
    os.pwrite(typst_fd, render_str.encode(), 0)


def teardown(typ_fd):
    # maybe remove files and close browser, idk
    os.close(typ_fd)


def update_pos(pos):
    x, y = pos
    #NOTE: local variables dumb dumb, fix
    if input_state.get('w'): y -= 1
    if input_state.get('a'): x -= 1
    if input_state.get('s'): y += 1
    if input_state.get('d'): x += 1


if __name__ == "__main__":
    typ_fd, listener = setup()
    listener.start()

    tmp_pos = [100.0, 100.0]
    tmp_img = "teapot.png"

    while True:
        if input_state.get('q'): break
        
        # UPDATE
        update_pos(tmp_pos)
        tmp_pos[0] -= 0.00005
        tmp_pos[1] -= 0.00005
        print(tmp_pos)

        # RENDER
        render_str = "#set page(height: 480pt, width: 600pt)\n"
        render_str += render_sprite(tmp_pos, "teapot.png")
        commit_render(render_str, typ_fd)

    teardown(typ_fd)
