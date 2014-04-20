#!/usr/bin/python
import subprocess, os
from glob import glob

for src in glob('*.coffee') + glob('*.jade') + glob('*.styl'):
    dest = 'build/%s' % src.replace('.coffee', '.js').replace('.jade', '.html').replace('.styl', '.css')
    try:
        if os.path.getmtime(dest) > os.path.getmtime(src):
            continue
    except OSError:
        pass

    print "building %s" % dest
    try:
        os.unlink(dest)
    except OSError:
        pass
    if '.styl' in src:
       subprocess.call('node_modules/stylus/bin/stylus -u autoprefixer-stylus < %(src)s > %(dest)s' % vars(), shell=True)
    elif '.jade' in src:
       subprocess.call('node_modules/jade/bin/jade.js < %(src)s > %(dest)s' % vars(), shell=True)
    elif '.coffee' in src:
       subprocess.call(['coffee', '-o', 'build/', '-c', src])

