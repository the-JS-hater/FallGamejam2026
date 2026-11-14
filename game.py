#!/usr/bin/env python3


import webbrowser
import subprocess
import pathlib
import os
import time
import pygame
import random


TYP_FILENAME = "render_image.typ"
OUT_FILENAME = "main.pdf"

TYP_TEMPLATE = "#set page(height: 480pt, width: 600pt)\n"

ALL_SKILLS = ["interesting_fact_skill", "test", "test2", "test3"]


class DialogueOption:
    text = ""
    effect = 0.0
    response = None
    requrement = ""

    def __init__(self, text, effect, response, requirement=None):
        self.text = text
        self.effect = effect
        self.response = response
        if requirement: self.requrement = requirement
        

class DialogueNode:
    text = ""
    options = []

    def __init__(self, text, options):
        self.text = text
        self.options = options


def setup():
    pygame.init()
    screen = pygame.display.set_mode(size=(1, 1))
    clock = pygame.time.Clock()

    typ_file = os.open(TYP_FILENAME, os.O_CREAT | os.O_WRONLY | os.O_NONBLOCK)
    #dir_path = str(pathlib.Path(__file__).parent.resolve())
    #print("Dir path:" + str(dir_path))

    pdf_reader = subprocess.Popen(["zathura", OUT_FILENAME])

    return typ_file, clock, pdf_reader


def init_date():
    responseA = DialogueNode("Wow, that's rude", [])
    responseB = DialogueNode("Wow, that's so funny", [])
    responseC = DialogueNode("Wow that's interesting", [])
    root = DialogueNode("Hello, i am date", [DialogueOption("fuck off", -5.0, responseA), DialogueOption("hello date, i am dad", 5.0, responseB), DialogueOption("Did you know _interesting fact_", 5.0, responseC, "interesting_fact_skill")])
    return root

def render_sprite(pos, image_path, size = None):
    size_s = ""
    if size:
        size_s = f", width: {size[0]}pt"
        if size[1]:
            size_s += f", height: {size[1]}pt"
    return render_object(pos, f"#image(\"{image_path}\", scaling: \"pixelated\"{size_s})")


def render_object(pos, typ_object):
    x, y = pos
    return f"#place(dx: {int(x)}pt, dy: {int(y)}pt)[{typ_object}]\n"


def commit_render(render_str, typst_fd):
    render_str += "\n#let ok = true"
    os.truncate(typst_fd, 0)
    os.pwrite(typst_fd, render_str.encode(), 0)


def teardown(typ_fd, pdf_reader):
    # maybe remove files and close browser, idk
    os.close(typ_fd)
    pdf_reader.terminate()
    pygame.quit()


def splash_screen(typ_fd):
    with open("splash_screen.typ") as file:
        render_str = file.read()
    commit_render(render_str, typ_fd)
    while True:
        pygame.event.get()
        keys = pygame.key.get_pressed()
        if not any(keys):
            break
    while True:
        pygame.event.get()
        keys = pygame.key.get_pressed()
        if any(keys) and not keys[pygame.K_LSUPER]:
            break


def get_input(num_options):
    pressed = True
    while pressed:
        pygame.event.get()
        keys = pygame.key.get_pressed()
        if keys[pygame.K_q]: break
        pressed = False
        for key in range(num_options):
            if keys[pygame.key.key_code(str(key+1))] or keys[pygame.K_SPACE]:
                pressed = True
                continue

    while True:
        pygame.event.get()
        keys = pygame.key.get_pressed()
        if keys[pygame.K_q]: break
        if keys[pygame.K_SPACE]: return -1
        for key in range(num_options):
            if keys[pygame.key.key_code(str(key+1))]:
                return key
    return -2


def get_skill(typ_fd, clock):
    skills = ALL_SKILLS.copy()
    rng = random.Random()
    while len(skills) > 3:
        index = rng.randint(0, len(skills))
        skills = skills[:index] + skills[index+1:]

    render_str = TYP_TEMPLATE
    render_str += render_object((100, 0), "Choose a skill:")
    for i, option in enumerate(skills):
        render_str += render_object((100, 10+10*i), f"{str(i + 1)}: " + option)

    commit_render(render_str, typ_fd)
    choice = get_input(3)
    while choice < 0:
        print(render_str)
        commit_render(render_str + render_object((100, 180), "\ninvalid choice, try again\n"), typ_fd)
        clock.tick(30)

        choice = get_input(3)
    return skills[choice]


def main():
    typ_fd, clock, pdf_reader = setup()

    splash_screen(typ_fd)

    date_excitement = 5.0
    root = init_date()
    tree = root
    skills = []
    typ_template = TYP_TEMPLATE
    typ_template += render_sprite((0, 0), "Assets/WomanPortrait.png", (50, None))
    render_str = typ_template
    render_str += render_object((100, 0), tree.text)

    while True:
        unavailable = []
        if not tree: break
        for i, option in enumerate(tree.options):
            if (option.requrement and option.requrement not in skills):
                render_str += render_object((100, 10+10*i), f"{str(i + 1)}: Hidden option")
                unavailable += [i]
            else:
                render_str += render_object((100, 10+10*i), f"{str(i + 1)}: " + option.text)

        print(render_str)
        commit_render(render_str, typ_fd)
        clock.tick(30)

        choice = get_input(len(tree.options))
        while choice in unavailable:
            print(render_str)
            commit_render(render_str + render_object((100, 180), "\ninvalid choice, try again\n"), typ_fd)
            clock.tick(30)

            choice = get_input(len(tree.options))

        render_str = typ_template
        if choice == -1:
            skills.append(get_skill(typ_fd, clock))
            tree = root
            render_str += render_object((100, 0), tree.text)
            continue

        if choice == -2:
            break

        date_excitement += tree.options[choice].effect
        tree = tree.options[choice].response 
        if not tree: break

        render_str += render_object((100, 0), tree.text)

        if date_excitement <= 0.0:
            render_str += render_object((100, 200), "Date got bored and you lose")
            break

        if date_excitement >= 10.0:
            render_str += render_object((100, 200), "you win date, awooga")
            break

        if not tree.options:
            render_str += render_object((100, 210), "dialogue tree ends here")
            break

        # RENDER
        print(render_str)
        commit_render(render_str, typ_fd)
        render_str = typ_template

        clock.tick(30)


    print(render_str)
    commit_render(render_str, typ_fd)
    while True:
        pygame.event.get()
        keys = pygame.key.get_pressed()
        if not any(keys):
            break
    while True:
        pygame.event.get()
        keys = pygame.key.get_pressed()
        if any(keys):
            break


    teardown(typ_fd, pdf_reader)


if __name__ == "__main__":
    main()
