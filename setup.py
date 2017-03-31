import os, sys

from setuptools import setup, find_packages

###############################################################################
#
# Copyright (c) 2017 Stephen Gallagher
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
###############################################################################

__author__ = 'Stephen Gallagher <sgallagh@redhat.com>'

setup(
    name='depchase',
    version='0.1',
    url='https://github.com/sgallagher/depchase',
    #cmdclass = {'build_py': build_py},
    license='MIT',
    description='depchase - DNF repository analyzer',
    author='Stephen Gallagher',
    author_email='sgallagh@redhat.com',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    install_requires=['click>=6'],
    entry_points="""\
    [console_scripts]
    depchase = depchase.depchase:main
    """,
    )

