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

from depchase.util import get_multi_arch


def output_results(binaries, sources, arch,
                   binary_short_file, binary_full_file,
                   source_short_file, source_full_file):
    """
    Output all of the results into four separate files.
    In older versions (whatpkgs), this required four separate
    runs of the program, but there's no reason for that.
    """
    binary_short_f = open(binary_short_file, 'w')
    binary_full_f = open(binary_full_file, 'w')
    source_short_f = open(source_short_file, 'w')
    source_full_f = open(source_full_file, 'w')

    try:
        # Print the complete set of dependencies together
        for key in sorted(binaries, key=binaries.get):
            printpkg = binaries[key]
            binary_full_f.write("%d:%s-%s-%s.%s\n" % (
                                printpkg.epoch,
                                printpkg.name,
                                printpkg.version,
                                printpkg.release,
                                printpkg.arch))
            if binaries[key].arch == get_multi_arch(arch):
                binary_short_f.write("%s#%s\n" % (
                                     printpkg.name,
                                     printpkg.arch))
            else:
                binary_short_f.write("%s\n" % printpkg.name)

        for key in sorted(sources, key=sources.get):
            printpkg = sources[key]
            source_full_f.write("%d:%s-%s-%s.%s\n" % (
                                printpkg.epoch,
                                printpkg.name,
                                printpkg.version,
                                printpkg.release,
                                printpkg.arch))
            source_short_f.write("%s\n" % printpkg.name)

    finally:
        source_full_f.close()
        source_short_f.close()
        binary_full_f.close()
        binary_short_f.close()
    
