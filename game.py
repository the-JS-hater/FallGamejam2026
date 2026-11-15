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

ALL_SKILLS = ["interesting_fact_skill", "test1", "test2", "test3", "#lorem(50)"]

TEXT_WIDTH = 300


class DialogueOption:
    text = ""
    effect = 0.0
    font = None
    response = None
    requrement = ""

    def __init__(self, text, effect, response, requirement=None, font=None):
        self.text = text
        self.effect = effect
        self.response = response
        if requirement: self.requrement = requirement
        if font: self.font = font


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

    pdf_reader = subprocess.Popen(["zathura", OUT_FILENAME])

    return typ_file, clock, pdf_reader


def init_date():
    responseA = DialogueNode("Wow, that's rude", [])
    responseB = DialogueNode("Wow, that's so funny", [])
    responseC = DialogueNode("Wow that's interesting", [])
    root = DialogueNode("Hello, i am date\n#lorem(50)", [DialogueOption("fuck off", -5.0, responseA), DialogueOption("hello date, i am dad", 5.0, responseB), DialogueOption("Did you know _interesting fact_", 5.0, responseC, "interesting_fact_skill")])
    return root


def render_object(pos, typ_object, width = None):
    x, y = pos
    width_str = f"#box(width: {width}pt)[{typ_object}]" if width else typ_object
    return f"#place(dx: {int(x)}pt, dy: {int(y)}pt)[{width_str}]\n"


def render_sprite(pos, image_path, size = None):
    size_s = ""
    if size:
        size_s = f", width: {size[0]}pt"
        if size[1]:
            size_s += f", height: {size[1]}pt"
    return render_object(pos, f"#image(\"{image_path}\", scaling: \"pixelated\"{size_s})")


def commit_render(render_str, typst_fd):
    render_str += "\n#let ok = true"
    os.truncate(typst_fd, 0)
    os.pwrite(typst_fd, render_str.encode(), 0)


def teardown(typ_fd, pdf_reader):
    os.close(typ_fd)
    pdf_reader.terminate()
    pygame.quit()
    os._exit(0)


def splash_screen(typ_fd):
    with open("splash_screen.typ") as file:
        render_str = file.read()
    commit_render(render_str, typ_fd)
    get_input()


def get_input(num_options = None):
    while True:
        pygame.event.get()
        keys = pygame.key.get_pressed()
        if not any(keys): break

    while True:
        pygame.event.get()
        keys = pygame.key.get_pressed()
        if keys[pygame.K_q]: break
        if keys[pygame.K_SPACE]: return -1
        if not num_options:
            if any(keys) and not keys[pygame.K_LSUPER]: break
        else:
            for key in range(num_options):
                if keys[pygame.key.key_code(str(key+1))]:
                    return key
    return -2


def input_text(render_str, typ_fd, clock):
    pygame.key.start_text_input()
    input_string = ""
    while True:
        for event in pygame.event.get():
            if event.type == pygame.TEXTINPUT:
                input_string += event.text
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE:
                    input_string = input_string[:-1]
                elif event.key == pygame.K_RETURN:
                    pygame.key.stop_text_input()
                    return input_string
        commit_render(render_str + render_object((100, 15), input_string, TEXT_WIDTH), typ_fd)
        clock.tick(30)


def get_skill(typ_fd, owned_skills, clock):
    skills = ALL_SKILLS.copy()
    rng = random.Random()
    while len(skills) > 3:
        index = rng.randint(0, len(skills))
        skills = skills[:index] + skills[index+1:]

    render_str = TYP_TEMPLATE

    out_str = "Choose a skill:\n"
    for option in skills:
        out_str += f"+ {option}\n"
    render_str += render_object((100, 0), out_str, TEXT_WIDTH)

    skills_str = "Skills:\n"
    for skill in owned_skills:
        skills_str += f"- {skill}\n"
    render_str += render_object((400, 0), skills_str, 100)

    commit_render(render_str, typ_fd)
    choice = get_input(3)
    while choice < 0:
        commit_render(render_str + render_object((100, 180), "\ninvalid choice, try again\n"), typ_fd)
        clock.tick(30)

        choice = get_input(3)
    return skills[choice]


def timetravel(typ_fd, timewarp_counter, skills, template, typ_template, root, clock):
    timewarp_counter[0] += 1
    skills.add(get_skill(typ_fd, skills, clock))
    skills_str = "Skills:\n"
    for skill in skills:
        skills_str += f"- {skill}\n"
    typ_template = template + render_object((400, 0), skills_str, 100)
    date_excitement = 5.0
    tree = root
    out_str = tree.text + "\n"
    return out_str, tree, date_excitement, typ_template

def main():
    typ_fd, clock, pdf_reader = setup()

    splash_screen(typ_fd)

    template = TYP_TEMPLATE
    render_str = template

    render_str += render_object((100, 0), "Enter your name:")
    commit_render(render_str, typ_fd)
    name = input_text(render_str, typ_fd, clock)

    date_excitement = 5.0
    root = init_date()
    tree = root
    skills = set()
    timewarp_counter = [0]
    template += render_sprite((0, 0), "Assets/WomanPortrait.png", (50, None))
    typ_template = template + render_object((400, 0), "Skills:\n")
    render_str = typ_template
    output_str = tree.text + "\n"

    while True:
        unavailable = []
        if not tree: break
        for i, option in enumerate(tree.options):
            if (option.requrement and option.requrement not in skills):
                output_str += "+ Hidden option\n"
                unavailable += [i]
            else:
                output_str += f"+ {option.text}\n"

        render_str += render_object((100, 0), output_str, TEXT_WIDTH)
        commit_render(render_str, typ_fd)
        clock.tick(30)

        choice = get_input(len(tree.options))
        while choice in unavailable:
            commit_render(render_str + render_object((100, 180), "\ninvalid choice, try again\n"), typ_fd)
            clock.tick(30)

            choice = get_input(len(tree.options))

        render_str = typ_template
        if choice == -1:
            output_str, tree, date_excitement, typ_template = timetravel(typ_fd, timewarp_counter, skills, template, typ_template, root, clock)
            render_str = typ_template
            continue

        if choice == -2:
            break

        date_excitement += tree.options[choice].effect
        tree = tree.options[choice].response 
        if not tree: break

        output_str = tree.text + "\n"

        if date_excitement <= 0.0:
            render_str += render_object((100, 0), output_str, TEXT_WIDTH)
            render_str += render_object((100, 200), "Date got bored and you lose.\n\nTo timetravel, press space. Otherwise, press any button")
            commit_render(render_str, typ_fd)
            do_timetravel = get_input() == -1
            if do_timetravel:
                output_str, tree, date_excitement, typ_template = timetravel(typ_fd, timewarp_counter, skills, template, typ_template, root, clock)
                render_str = typ_template
                continue
            break

        if date_excitement >= 10.0:
            render_str += render_object((100, 0), output_str, TEXT_WIDTH)
            render_str += render_object((100, 200), "you win date, awooga!\n\nTo timetravel, press space. Otherwise, press any button")
            commit_render(render_str, typ_fd)
            do_timetravel = get_input() == -1
            if do_timetravel:
                output_str, tree, date_excitement, typ_template = timetravel(typ_fd, timewarp_counter, skills, template, typ_template, root, clock)
                render_str = typ_template
                continue
            break

        if not tree.options:
            render_str += render_object((100, 0), output_str, TEXT_WIDTH)
            render_str += render_object((100, 200), "dialogue tree ends here\n\nTo timetravel, press space. Otherwise, press any button")
            commit_render(render_str, typ_fd)
            do_timetravel = get_input() == -1
            if do_timetravel:
                output_str, tree, date_excitement, typ_template = timetravel(typ_fd, timewarp_counter, skills, template, typ_template, root, clock)
                render_str = typ_template
                continue
            break

        # RENDER
        commit_render(render_str, typ_fd)
        render_str = typ_template

        clock.tick(30)


    teardown(typ_fd, pdf_reader)


if __name__ == "__main__":
    main()
