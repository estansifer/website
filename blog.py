import os
import os.path as op

import document
import filelayout

months = [
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December'
        ]
def date_human_readable(y, m, d):
    if y is None:
        return '{} {:02d}'.format(months[m - 1], d)
    else:
        return '{:04d} {} {:02d}'.format(y, months[m - 1], d)

# The order that tags are given here are the order they will be printed in the tagline
alltags = [
        ('facebook', 'originally posted on facebook'),
        ('gtalk', 'originally shared via google talk'),
        ('notgtalk', 'not actually shared via google talk but tagged like it for weird technical reasons')
    ]

class BlogPost:
    def __init__(self):
        self.name = None
        self.source_text = None

        self.date = None
        self.date_string = None
        self.title = None
        self.markdown = None
        self.older = None
        self.newer = None
        self.name_postfix = ''
        self.tags = []
        self.modtime = None

        self.document = None

    def parse_header_date(self, date):
        parts = date.split()
        assert len(parts) == 3
        self.date = (int(parts[0]), int(parts[1]), int(parts[2])) # Year, month, day
        self.date_string = '{:04d}{:02d}{:02d}'.format(*self.date)

    def parse_header_tag(self, tag):
        self.tags.append(tag)

    def parse_header_title(self, title):
        self.title = title

    def parse_header(self, name, data):
        if name == 'date':
            self.parse_header_date(data)
        elif name == 'tag':
            self.parse_header_tag(data)
        elif name == 'title':
            self.parse_header_title(data)
        else:
            print("Unrecognized header command '{}' with data '{}'".format(name, data))

    # static
    # Creates a BlogPost from the given raw text
    def from_source_text(headers, body):
        self = BlogPost()
        for header in headers:
            name, data = header.split(maxsplit = 1)
            if name.startswith('20'):
                name = 'date'
                data = header
            self.parse_header(name, data.strip())

        self.markdown = body

        return self

    def tagline(self):
        tags = []
        for tag, tag_display in alltags:
            if tag in self.tags:
                tags.append(tag_display)
        return ', '.join(tags)

    def make_document(self):
        d = document.WebDocument()
        self.document = d
        d.name = self.name
        d.source_data = self.markdown
        d.set_target_path(filelayout.blog_target_path(self.name))
        d.modtime = self.modtime
        d.is_markdown = True
        d.template = filelayout.pandoc_blog_template

        date_human = date_human_readable(*self.date)

        if self.title is None:
            d.add_variable('pagetitle', date_human)
        else:
            d.add_variable('pagetitle', self.title)
            d.add_variable('title', self.title)

        d.add_variable('date-human', date_human)
        if len(self.tags) > 0:
            d.add_variable('tagline', self.tagline())

        if self.newer is not None:
            d.modtime = max(d.modtime, self.newer.modtime)
        if self.older is not None:
            d.modtime = max(d.modtime, self.older.modtime)




linknames = {
            'wikipedia.org' : 'Wikipedia',
            'theguardian.com' : 'The Guardian',
            'bbc.com' : 'BBC',
            'bcc.co.uk' : 'BBC',
            'telegraph.co.uk' : 'The Telegraph',
            'nytimes.com' : 'NYT',
            'slate.com' : 'Slate',
            'washingtonpost.com' : 'Washington Post',
            'newyorker.com' : 'The New Yorker',
            'theatlantic.com' : 'The Atlantic',
            'pnas.org' : 'PNAS',
            'youtube.com' : 'YouTube',
            'vox.com' : 'Vox',
            'lawfareblog.com' : 'Lawfare',
            'openargs.com' : 'Opening Arguments',
            'fivethirtyeight.com' : '538',
            'cnn.com' : 'CNN'
        }

def auto_link(line):
    if line.startswith('http'):
        split = line.split(maxsplit = 1)
        if len(split) == 1:
            url = split[0]
            rest = ''
        else:
            url = split[0]
            rest = ' ' + split[1]

        ul = url.lower()
        is_image = ul.endswith('.png') or ul.endswith('.jpg') or ul.endswith('.jpeg')
        if 'wikipedia' in ul:
            is_image = False

        if is_image:
            # return '![]({}){{max-width=100%}}{}'.format(url, rest)
            if len(rest) == 0:
                return '![]({}){{.image_center}}'.format(url)
            else:
                return '![]({}){{.image}}{}'.format(url, rest)
        else:
            for keyword in linknames:
                if keyword in url:
                    return '[{}]({}){}'.format(linknames[keyword], url, rest)

            return '<{}>{}'.format(url, rest)
    else:
        return line

esc = set('\\`*_{}[]()<>#+-.!()$%^&=|:;"\',/~')
def escape_markdown(text):
    res = []
    for c in text:
        if c in esc:
            res.append('\\' + c)
        else:
            res.append(c)
    return ''.join(res)

collision_postfix = 'abcdefghijklmnopqrstuvwxyz'

class Blog:
    def __init__(self):
        self.posts = []
        self.years = None
        self.modtime = 0

    def read_from_file(self, source):
        modtime = op.getmtime(source)
        self.modtime = max(self.modtime, modtime)

        h = '@'
        is_social = ('facebook' in source) or ('gtalk' in source)

        with open(source, 'r') as f:
            lines = f.read().split('\n')

        blocks = []

        start = 0
        for i in range(1, len(lines)):
            if lines[i].startswith(h) and (not lines[i - 1].startswith(h)):
                blocks.append(lines[start : i])
                start = i
        blocks.append(lines[start : ])

        for block in blocks:
            headers = []
            body = []
            for line in block:
                if line.startswith(h):
                    line = line[1:].strip()
                    if len(line) > 0:
                        headers.append(line)
                else:
                    body.append(line)

            if is_social:
                for i in range(len(body)):
                    body[i] = auto_link(body[i])

            body = '\n'.join(body).strip()

            if len(body) > 0:
                post = BlogPost.from_source_text(headers, body)
                post.modtime = modtime
                if 'facebook' in source:
                    post.parse_header_tag('facebook')
                if 'gtalk' in source:
                    post.parse_header_tag('gtalk')

                if post.date is None:
                    print("Blog post missing date!")
                    print(">>{}<<>>{}<<".format('@'.join(headers), body))
                else:
                    self.posts.append(post)

    def sort_and_name(self):
        # Note that "sort" is guaranteed to be stable, so if there are multiple
        # posts with the same date they maintain the order they came in.
        # For this reason, posts with the same date should be in the same input
        # file so that their relative order can be guaranteed.

        self.posts = list(filter(lambda p : not ('hidden' in p.tags), self.posts))
        self.posts.reverse()
        self.posts.sort(key = lambda p : p.date)

        n = len(self.posts)
        collisions = [False] * n
        for i in range(n - 1):
            self.posts[i].newer = self.posts[i + 1]
            self.posts[i + 1].older = self.posts[i]
            collisions[i] = (self.posts[i + 1].date == self.posts[i].date)

        collision_index = 0
        for i in range(n - 1):
            if collisions[i]:
                self.posts[i].name_postfix = collision_postfix[collision_index]
                self.posts[i + 1].name_postfix = collision_postfix[collision_index + 1]
                collision_index += 1
            else:
                collision_index = 0

        for post in self.posts:
            post.name = post.date_string + post.name_postfix

        for post in self.posts:
            post.make_document()
            if post.newer is not None:
                post.document.add_variable('newer', post.newer.name)
            if post.older is not None:
                post.document.add_variable('older', post.older.name)

        self.years = []
        for p in self.posts:
            if not (p.date[0] in self.years):
                self.years.append(p.date[0])
        self.years.sort(reverse = True)

    def make_index_compact(self):
        markdown = []

        line = ' '.join(["[{}](#year_{})".format(y, y) for y in self.years])
        markdown.append(line)
        markdown.append('')

        for y in self.years:
            markdown.append('## [{}](index_{}) {{#year_{}}}'.format(y, y, y))
            markdown.append('')
            markdown.append('|  |  |')
            markdown.append('|{}:|:{}|'.format('-' * 12, '-' * 80))
            for p in reversed(self.posts):
                if p.date[0] == y:
                    date = date_human_readable(None, p.date[1], p.date[2])
                    if p.title is None:
                        # tease = '``` ' + p.markdown[:60].replace('\n', ' ') + ' ```'
                        tease = escape_markdown(p.markdown[:70].replace('\n', ' '))
                    else:
                        tease = p.title
                    line = '|[{}]({}){{.indexdate}}|[{}]({}){{.tease}}|'.format(
                            date, p.name, tease, p.name)
                    markdown.append(line)
            markdown.append('')

        d = document.WebDocument()
        d.name = 'index.html.md'
        d.set_target_path(filelayout.output_blog_index_compact)
        d.source_data = '\n'.join(markdown)
        d.modtime = self.modtime
        d.is_markdown = True
        d.template = filelayout.pandoc_blog_compact_template

        d.add_variable('pagetitle', "Blog")

        return d

    def make_index_expanded(self, year):
        markdown = []

        modtime = 0

        for p in reversed(self.posts):
            if p.date[0] == year:
                date = date_human_readable(*p.date)
                if p.title is None:
                    markdown.append('## [{}]({})'.format(date, p.name))
                    markdown.append('')
                else:
                    markdown.append('## [{}]({})'.format(p.title, p.name))
                    markdown.append('')
                    markdown.append('[{}]{{.date}}'.format(date))
                    markdown.append('')

                if len(p.tags) > 0:
                    markdown.append('[{}]{{.tagline}}'.format(p.tagline()))
                    markdown.append('')

                markdown.append(p.markdown)
                markdown.append('')

                modtime = max(modtime, p.modtime)

        d = document.WebDocument()
        d.name = 'index_{}.md'.format(year)
        d.set_target_path(filelayout.blog_index_expanded_path(year))
        d.source_data = '\n'.join(markdown)
        d.modtime = modtime
        d.is_markdown = True
        d.template = filelayout.pandoc_blog_expanded_template

        d.add_variable('pagetitle', 'Blog - {}'.format(year))
        if year + 1 in self.years:
            d.add_variable('newer', 'index_{}'.format(year + 1))
        if year - 1 in self.years:
            d.add_variable('older', 'index_{}'.format(year - 1))

        return d

    def create_documents(self):
        self.sort_and_name()

        docs = [post.document for post in self.posts]
        docs.append(self.make_index_compact())
        for year in self.years:
            docs.append(self.make_index_expanded(year))

        return docs
