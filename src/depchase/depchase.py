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

import click
import pprint
import sys

from depchase.io import output_results
from depchase.process import recurse_package_deps
from depchase.process import resolve_ambiguity
from depchase.queries import get_pkg_by_name
from depchase.queries import get_srpm_for_package_name
from depchase.repoconfig import prep_repositories
from depchase.util import split_pkgname

@click.group()
def main():
    pass


@main.command(short_help="Get package dependencies")
@click.argument('pkgnames', nargs=-1)
@click.option('--hint', multiple=True,
              help="""
Specify a package to be selected when more than one package could satisfy a
dependency. This option may be specified multiple times.

For example, it is recommended to use --hint=glibc-minimal-langpack
""")
@click.option('--filter', multiple=True,
              help="""
Specify a package to be skipped during processing. This option may be
specified multiple times.

This is useful when some packages are provided by a lower-level module
already contains the package and its dependencies.
""")
@click.option('--whatreqs', multiple=True,
              help="""
Specify a package that you want to identify what pulls it into the complete
set. This option may be specified multiple times.
""")
@click.option('--recommends/--no-recommends', default=True)
@click.option('--pick-first/--no-pick-first', default=False,
              help="""
If multiple packages could satisfy a dependency and no --hint package will
fulfill the requirement, automatically select one from the list.

Note: this result may differ between runs depending upon how the list is
sorted. It is recommended to use --hint instead, where practical.
""")
@click.option('--os', default='Fedora',
              help="Specify the operating system.")
@click.option('--version', default=25,
              help="Specify the version of the OS sampledata to compare "
                   "against.")
@click.option('--arch', default='x86_64',
              help="Specify the CPU architecture.")
@click.option('--milestone', default=None,
              help="Specify the pre-release milestone. If not provided, "
                   "the final release will be used.")
@click.option('--binary-short-file', default='binaries-short.txt',
              help="The file to contain the short version of the detected "
                   "dependencies. (Just the package name)")
@click.option('--binary-full-file', default='binaries-full.txt',
              help="The file to contain the long version of the detected "
                   "dependencies. (Package name, version, architecture, "
                   "etc.)")
@click.option('--source-short-file', default='sources-short.txt',
              help="The file to contain the short version of the detected "
                   "dependencies. (Just the package name)")
@click.option('--source-full-file', default='sources-full.txt',
              help="The file to contain the long version of the detected "
                   "dependencies. (Package name, version, architecture, "
                   "etc.)")
def neededby(pkgnames, hint, filter, whatreqs, recommends,
             pick_first, os, version, arch, milestone,
             binary_short_file, binary_full_file,
             source_short_file, source_full_file):
    """
    Look up the dependencies for each specified package and
    display them in a human-parseable format.
    """

    query = prep_repositories(os, version, milestone, arch)

    dependencies = {}
    ambiguities = []
    for fullpkgname in pkgnames:
        (pkgname, pkgarch) = split_pkgname(fullpkgname, arch)

        if pkgname in filter:
            # Skip this if we explicitly filtered it out
            continue

        pkg = get_pkg_by_name(query, pkgname, pkgarch)

        recurse_package_deps(pkg, dependencies, ambiguities, query, hint,
                             filter, whatreqs, pick_first, recommends)

        # Check for unresolved deps in the list that are present in the
        # dependencies. This happens when one package has an ambiguous dep but
        # another package has an explicit dep on the same package.
        # This list comprehension just returns the set of dictionaries that
        # are not resolved by other entries
        ambiguities = [x for x in ambiguities
                       if not resolve_ambiguity(dependencies, x)]

    # Get the source packages for all the dependencies
    srpms = {}
    for key, pkg in dependencies.items():
        srpm_pkg = get_srpm_for_package_name(query, pkg.name)
        srpms[srpm_pkg.name] = srpm_pkg

    # Print the complete set of dependencies together
    output_results(dependencies, srpms, arch,
                   binary_short_file, binary_full_file,
                   source_short_file, source_full_file)

    if len(ambiguities) > 0:
        print("=== Unresolved Requirements ===",
              file=sys.stderr)
        pp = pprint.PrettyPrinter(indent=4)
        pp.pprint(ambiguities)

