#!/usr/bin/env python3


import webbrowser
import subprocess
import pathlib
import os
import time
import pygame


TYP_FILENAME = "render_image.typ"
OUT_FILENAME = "main.pdf"


def setup():
    pygame.init()
    screen = pygame.display.set_mode()
    clock = pygame.time.Clock()
    pygame.display.flip()

    typ_file = os.open(TYP_FILENAME, os.O_CREAT | os.O_WRONLY | os.O_NONBLOCK)
    #dir_path = str(pathlib.Path(__file__).parent.resolve())
    #print("Dir path:" + str(dir_path))

    pdf_reader = subprocess.Popen(["zathura", OUT_FILENAME])

    return typ_file, clock, pdf_reader


def render_sprite(pos, image_path):
    x, y = pos
    return f"#place(dx: {int(x)}pt, dy: {int(y)}pt)[#image(\"{image_path}\")]\n"


def commit_render(render_str, typst_fd):
    os.truncate(typst_fd, 0)
    os.pwrite(typst_fd, render_str.encode(), 0)


def teardown(typ_fd, pdf_reader):
    # maybe remove files and close browser, idk
    os.close(typ_fd)
    pdf_reader.terminate()
    pygame.quit()


def update_pos(pos, keys):
    if keys[pygame.K_w]: pos[1] -= 1
    if keys[pygame.K_a]: pos[0] -= 1
    if keys[pygame.K_s]: pos[1] += 1
    if keys[pygame.K_d]: pos[0] += 1


if __name__ == "__main__":
    typ_fd, clock, pdf_reader = setup()

    tmp_pos = [100.0, 100.0]
    tmp_img = "teapot.png"

    while True:
        pygame.event.get()
        keys = pygame.key.get_pressed()
        if keys[pygame.K_q]: break

        # UPDATE
        update_pos(tmp_pos, keys)

        # RENDER
        render_str = "#set page(height: 480pt, width: 600pt)\n"
        render_str += render_sprite(tmp_pos, "teapot.png")

        # Make sure not to render if file is empty
        render_str += "\n#let ok = true"
        commit_render(render_str, typ_fd)

        clock.tick(30)

    teardown(typ_fd, pdf_reader)
