#
#   Data describing the website is found in input_dir.
#   The website files are placed with their root in output_dir.
#
#
#   Markdown files can contain Latex equations, with $foo$ for inline
#   equations and $$foo$$ for full equations.
#
#   Input files are read from input/main/.
#
#   Files with an extension ending in .md
#   are treated as markdown, and are processed according to the template
#   input/template.html and placed in the corresponding location in the
#   website tree, with the .md extension removed and input/markdown/
#   going to root.
#
#   Other files are copied verbatim to /r/<filename>.
#
#   Files with an extension .hide are ignored.
#
#   Files with an extension .nomove are not moved to /r/, but rather
#   kept in the same relative place.
#
#   Files with an extension .blog are treated as blog source material.
#
#   Files in cyoa/ are treated as a collection of locations in
#   (one or more) choose-your-own-adventure games. The body of these locations
#   are treated as markdown and the processed files are put in /cyoa/
#
#   (TODO: option to compile a cyoa game as a standalone html directory.)
#   
#   Any images generated for Latex figures from markdown files are saved
#   in /a/<xxxx>.png (or svg can be used) where <xxxx> is the
#   first 16 hex digits of the sha256 hash of the image file.
#
#   Hotlinks to externally hosted images in markdown files are downloaded to
#   input/cache/external/.
#
#   The files /weather/cambridge/now.png and /weather/cambridge/now_f.png are
#   to be updated once an hour by some other application.
#
#

import sys
import os
import os.path

import document
import filelayout
import blog
import cyoa

def valid_input_file(filename):
    if filename.endswith('.swp') or filename.endswith('.hide'):
        return False
    return True

# Walks over all input files: paths to blog files are fed into
# process_blog, and other paths into process_other.
def walk_input(process_blog, process_other):
    for dirpath, dirnames, filenames in os.walk(filelayout.main_dir):
        for filename in filenames:
            if not valid_input_file(filename):
                continue

            path = os.path.join(dirpath, filename)
            if filename.endswith('.blog'):
                process_blog(path)
            else:
                process_other(path)

def create_cyoa_documents():
    modtime = 0

    files = []
    for dirpath, dirnames, filenames in os.walk(filelayout.cyoa_dir):
        for filename in filenames:
            if valid_input_file(filename):
                filepath = os.path.join(dirpath, filename)
                filename = os.path.relpath(filepath, filelayout.cyoa_dir)
                files.append((filename, filepath))
                modtime = max(modtime, os.path.getmtime(filepath))

    gd = cyoa.read_game_data(files)

    docs = cyoa.make_markdown(gd)

    for d in docs:
        d.modtime = modtime

    return docs

def create_documents(create_blog = True, create_cyoa = True, create_other = True):
    ignore = lambda x : 0

    if create_blog:
        b = blog.Blog()
        def process_blog(path):
            try:
                b.read_from_file(path)
            except:
                print("Failed to read blog file", path)
                raise
    else:
        process_blog = ignore

    if create_other:
        docs_other = []
        def process_other(path):
            docs_other.append(document.WebDocument.from_source_path(path))
    else:
        process_other = ignore

    walk_input(process_blog, process_other)

    docs_all = []
    if create_other:
        docs_all.extend(docs_other)
    if create_blog:
        docs_all.extend(b.create_documents())
    if create_cyoa:
        docs_all.extend(create_cyoa_documents())

    return docs_all

def create_directories():
    paths = [
            filelayout.working_dir,
            filelayout.latex_dir,
            filelayout.output_dir,
            filelayout.output_auto_generated_dir,
            filelayout.output_resources_dir]

    for path in paths:
        os.makedirs(path, exist_ok = True)

def run():
    args = sys.argv[1:]

    if len(args) == 0:
        create_blog = True
        create_cyoa = True
        create_other = True
        recent = False
    else:
        create_blog = False
        create_cyoa = False
        create_other = False
        recent = False
        for arg in args:
            if arg == 'blog':
                create_blog = True
            elif arg == 'cyoa':
                create_cyoa = True
            elif arg == 'other':
                create_other = True
            elif arg == 'recent':
                recent = True
            else:
                raise ValueException(
                        "Don't understand command line argument \"{}\".".format(arg))

    docs = create_documents(create_blog, create_cyoa, create_other)

    create_directories()
    document.process_all(docs, only_recent = recent)

if __name__ == "__main__":
    run()
