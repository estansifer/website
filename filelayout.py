import sys
import os.path as op

root_dir = op.join(sys.path[0], '..')

input_dir = op.join(root_dir, 'input')
output_dir = op.join(root_dir, 'www')
working_dir = op.join(root_dir, 'working')
latex_dir = op.join(working_dir, 'latex')

pandoc_html_template = op.join(input_dir, 'template.html')
pandoc_cyoa_template = op.join(input_dir, 'template_cyoa.html')
pandoc_blog_template = op.join(input_dir, 'template_blog.html')
pandoc_blog_compact_template = op.join(input_dir, 'template_blog_index_compact.html')
pandoc_blog_expanded_template = op.join(input_dir, 'template_blog_index_expanded.html')
main_dir = op.join(input_dir, 'main')
cyoa_dir = op.join(input_dir, 'cyoa')

output_auto_generated_dir = op.join(output_dir, 'a')
output_resources_dir = op.join(output_dir, 'r')
output_cyoa_dir = op.join(output_dir, 'cyoa')
output_cyoa_index = op.join(output_cyoa_dir, 'index.html')
output_blog_dir = op.join(output_dir, 'posts')
output_blog_index_compact = op.join(output_blog_dir, 'index.html')

def cyoa_target_path(name):
    return op.join(output_cyoa_dir, name)

def blog_target_path(name):
    return op.join(output_blog_dir, name)

def blog_index_expanded_path(year):
    return op.join(output_blog_dir, 'index_{}'.format(year))

def path_to_auto_resource(name):
    return op.join(output_auto_generated_dir, name)

def link_to_auto_resource(name):
    return op.join('/a/', name)
