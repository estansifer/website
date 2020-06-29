import os
import os.path as op
import shutil
import gzip
import time

import filelayout
import processmarkdown

def is_parent_path(parent, child):
    parent = op.realpath(parent)
    child = op.realpath(child)
    return parent == op.commonpath([parent, child])

# Represents a single file on the website
class WebDocument:
    #
    # source_path       absolute, or relative to the working directory
    # target_path       absolute (in output dir)
    #
    # source_data       in memory copy of the source data
    # target_data       in memory copy of the target data
    #
    def __init__(self):
        self.name = None

        self.source_path = None
        self.target_path = None

        self.source_data = None
        self.target_data = None

        self.is_markdown = False

        self.template = filelayout.pandoc_html_template
        self.meta_variables = []

        self.modtime = None

    # static
    #
    # path is either absolute path to the source file, or relative to the working directory
    # If there is an extension .md or .nomove, acts appropriately
    def from_source_path(path, root = None):
        if root is None:
            root = filelayout.main_dir

        assert op.isfile(path)

        self = WebDocument()
        self.name = op.basename(path)
        self.source_path = path
        self.modtime = op.getmtime(path)
        assert len(self.name) > 0

        nomove = False

        if self.name.endswith('.md'):
            self.is_markdown = True
            nomove = True

            self.name = self.name[:-3]
        elif self.name.endswith('.nomove'):
            nomove = True

            self.name = self.name[:-7]

        assert len(self.name) > 0

        if nomove:
            target_path = op.join(filelayout.output_dir,
                    op.relpath(op.dirname(path), root), self.name)
        else:
            target_path = op.join(filelayout.output_resources_dir, self.name)
        self.set_target_path(target_path)

        return self

    def set_target_path(self, target_path):
        target_dir = op.dirname(target_path)
        assert is_parent_path(filelayout.output_dir, target_dir)
        self.target_path = target_path

        self.relroot = op.relpath(filelayout.output_dir, target_dir)
        self.add_variable('relroot', self.relroot)

    def add_variable(self, key, value = None):
        self.meta_variables.append((key, value))

    def pandoc_variable_arguments(self):
        args = []
        for key, value in self.meta_variables:
            args.append('-V')
            if value is None:
                args.append(key)
            else:
                args.append('{}={}'.format(key, value))
        return args

    def save_target(self):
        os.makedirs(op.dirname(self.target_path), exist_ok = True)
        if self.target_data is None:
            shutil.copyfile(self.source_path, self.target_path)
        else:
            with open(self.target_path, 'w') as f:
                f.write(self.target_data)

        size = op.getsize(self.target_path)
        target_gz = self.target_path + '.gz'

        if size >= 500:
            with open(self.target_path, 'rb') as f_in:
                with gzip.GzipFile(target_gz, 'wb', mtime = 0) as f_out:
                    shutil.copyfileobj(f_in, f_out)
            # with open(self.target_path, 'rb') as f_in:
                # with gzip.open(target_gz, 'wb') as f_out:

        else:
            if op.isfile(target_gz):
                os.remove(target_gz)

    def process_markdown(self):
        processmarkdown.process_markdown(self)

    def process(self):
        print("Processing {} -> {}".format(self.name,
            op.relpath(self.target_path, filelayout.output_dir)))

        if self.is_markdown:
            self.process_markdown()
        self.save_target()

def check_target_conflicts(documents):
    duplicates = False

    targets = set()
    for d in documents:
        assert d.target_path is not None
        target = str(op.realpath(d.target_path))
        if target in targets:
            print("**Duplicate target:", target)
            duplicates = True
        targets.add(target)

    if duplicates:
        raise Exception("Duplicate targets")

def process_all(documents, only_recent = False):
    check_target_conflicts(documents)

    recent = time.time() - 7 * 24 * 60 * 60

    for d in documents:
        if (not only_recent) or (d.modtime > recent):
            d.process()
