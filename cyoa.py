#!/usr/bin/python

import random
import json
import hashlib
import os.path as op

import document
import filelayout

#
# I first wrote the parsing code in 2012, although it was
# completely re-written in 2016, and has been updated since
# then. I don't have a full recollection of my intention
# behind the somewhat unusual format and parsing.
#

# If a name appears in a given file, resolve where it is referring to
def resolve_name(filename, name):
    if '/' in name:
        return name
    else:
        return filename + '/' + name

class GameTransition:
    def __init__(self, raw_data, filename):
        self.target = resolve_name(filename, raw_data['name'])
        self.prompt_text = raw_data['text']

class GameLocation:
    def __init__(self, raw_data, filename):
        self.name = resolve_name(filename, raw_data['name'])
        self.text = raw_data['text']
        self.links = []
        for link in raw_data['subobjects']:
            self.links.append(GameTransition(link, filename))

def random_6_digit_number(l, failures):
    return str(random.randint(100000, 999999))

def hash_hex(l, failures):
    text = [l.name, l.text] + [t.target for t in l.links] + [t.prompt_text for t in l.links]
    data = bytes('@@'.join(text) + '#' + str(failures), 'utf8')
    return hashlib.sha256(data).hexdigest()[:16]


class GameData:
    # location_files is a list of pairs
    #   (filename, raw_data)
    # where raw_data is a json object which is a list of dictionaries
    #   each dictionary has:
    #       name - name of a location
    #       text - text displayed at that location
    #       subobjects - a list of dictionaries
    #           each dictionary has:
    #               name - name of a target location
    #               text - text displayed for that choice
    def __init__(self, location_files, start_name = 'menu/start'):
        self.name2location = {}
        for filename, raw_data in location_files:
            for l in raw_data:
                location = GameLocation(l, filename)
                if location.name in self.name2location:
                    raise ValueError("Duplicate location name " + location.name)
                self.name2location[location.name] = location

        self.assign_random_ids()

        assert start_name in self.name2location
        self.start_name = start_name
        self.start = self.name2location[self.start_name]

    def assign_random_ids(self, generator = hash_hex):
        self.ids = {}
        for l in self.name2location.values():
            failures = 0
            while True:
                u = generator(l, failures)
                if u in self.ids:
                    failures += 1
                else:
                    self.ids[u] = l
                    l.unique_name = u
                    break

special_char = ';'
subobjects = 'subobjects'
def parse_semi_json(s):
    lines = s.split('\n')

    result = []
    list_stack = [result]
    cur_text_block = []
    cur_obj = None

    for line in lines:
        count = 0
        while len(line) > count and line[count] == special_char:
            count += 1

        if count > 0:
            # Finish any text block we were in
            if cur_obj is not None:
                cur_obj['text'] = '\n'.join(cur_text_block)
            cur_text_block = []

            # Parse the new object
            if line.find('{') == -1:
                # just a plain string
                cur_obj = {'name' : line[count:].strip()}
            else:
                # This line should be interpreted as json syntax
                cur_obj = json.loads(line[count:])
                assert (type(obj) is dict)
            if subobjects not in cur_obj:
                cur_obj[subobjects] = []

            if count > len(list_stack):
                raise ValueError("Incorrect indentation: " + line)

            # Attach the new object to a suitable list
            list_stack = list_stack[:count]
            list_stack[-1].append(cur_obj)
            list_stack.append(cur_obj[subobjects])
        else:
            cur_text_block.append(line)

    if cur_obj is not None:
        cur_obj['text'] = '\n'.join(cur_text_block)

    return result

def read_game_data(files):

    locations = []
    for filename, filepath in files:
        with open(filepath, 'r') as r:
            locations.append((filename, parse_semi_json(r.read())))
    return GameData(locations)

def make_markdown(gd):
    title = 'Choose your own adventure'

    docs = []
    for loc in gd.name2location.values():
        haslinks = (len(loc.links) > 0)

        markdown = []

        if haslinks:
            # YAML header block to set various variables
            markdown.append('---')
            markdown.append('link:')
            for i, link in enumerate(loc.links):
                i = i + 1
                if i < 10:
                    # digits
                    # charcode = str(48 + i)
                    key = str(i)
                elif i < 36:
                    # letters
                    # charcode = str(97 + i - 10)
                    key = chr(97 + i - 10)
                else:
                    break

                markdown.append('- key: ' + key)
                markdown.append('  target: ' + gd.name2location[link.target].unique_name)
                if '\n' in link.prompt_text:
                    markdown.append('  text: |')
                    for line in link.prompt_text.split('\n'):
                        markdown.append('    ' + line)
                else:
                    markdown.append('  text: ' + link.prompt_text)
            markdown.append('...')
            markdown.append('')

        markdown.append(loc.text)

        # This doesn't work because of multi-paragraph links.
        # if haslinks:
            # markdown.append('')
            # for link in loc.links:
                # markdown.append('#.  [{}]({}){{.choice}}'.format(link.prompt_text,
                    # gd.name2location[link.target].unique_name))
                # markdown.append('')


        d = document.WebDocument()
        d.name = loc.unique_name
        d.source_data = '\n'.join(markdown)
        d.set_target_path(filelayout.cyoa_target_path(d.name))
        d.is_markdown = True
        d.template = filelayout.pandoc_cyoa_template

        if haslinks:
            d.add_variable('haslinks')
        d.add_variable('pagetitle', title)

        docs.append(d)

    docs.append(make_index(gd))

    return docs

def make_index(gd):
    html = ['<!DOCTYPE html>',
            '<html>',
            '<head>',
            '<meta http-equiv="refresh" content="0; URL=\'' +
                gd.start.unique_name + '\'" />',
            '</head>',
            '</html>']

    d = document.WebDocument()
    d.name = 'index.html'
    d.target_data = '\n'.join(html)
    d.set_target_path(filelayout.output_cyoa_index)
    d.is_markdown = False

    return d
