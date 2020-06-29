import subprocess

def call(cmd, **kwargs):
    # Other useful options:
    #   cwd = path-to-working-directory
    #   input = string-to-pass-as-stdin
    options = {
            'universal_newlines' : True,
            'stdout' : subprocess.PIPE,
            'stderr' : subprocess.PIPE
            }
    for key in kwargs:
        options[key] = kwargs[key]

    result = subprocess.run(cmd, **options)

    if result.returncode != 0:
        print("Error in ", ' '.join(cmd))
        print("***stdout:")
        print(result.stdout)
        print("***stderr:")
        print(result.stderr)
        result.check_returncode()

    return result
