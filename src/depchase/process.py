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

from depchase.queries import get_requirements

def recurse_package_deps(pkg, dependencies, ambiguities,
                         query, hints, filters, whatreqs,
                         pick_first, follow_recommends):
    """
    Recursively search through dependencies and add them to the list
    """
    depname = "%s#%s" % (pkg.name, pkg.arch)
    if depname in dependencies:
        # Don't recurse the same dependency twice
        return
    dependencies[depname] = pkg

    # Process Requires:
    deps = get_requirements(pkg, pkg.requires, dependencies,
                            ambiguities, query, hints,
                            filters, whatreqs,
                            pick_first)

    try:
        # Process Requires(pre|post)
        prereqs = get_requirements(pkg, pkg.requires_pre, dependencies,
                                   ambiguities, query, hints,
                                   filters, whatreqs,
                                   pick_first)
        deps.extend(prereqs)
    except AttributeError:
        print("DNF 2.x required.", file=sys.stderr)
        sys.exit(1)

    if follow_recommends:
        recommends = get_requirements(pkg, pkg.recommends, dependencies,
                                      ambiguities, query, hints,
                                      filters, whatreqs,
                                      pick_first)
        deps.extend(recommends)

    for dep in deps:
        recurse_package_deps(dep, dependencies, ambiguities, query,
                             hints, filters, whatreqs,
                             pick_first, follow_recommends)


def recurse_self_host(binary_pkg, binaries, sources,
                      ambiguities, query, hints,
                      filters, whatreqs,
                      pick_first, follow_recommends):
    """
    Recursively determine all build dependencies for this package
    """

    depname = "%s#%s" % (binary_pkg.name, binary_pkg.arch)
    if depname in binaries:
        # Don't process the same binary RPM twice
        return

    binaries[depname] = binary_pkg

    # Process strict Requires:
    deps = get_requirements(binary_pkg, binary_pkg.requires, binaries,
                            ambiguities, query, hints,
                            filters, whatreqs, pick_first)

    # Process Requires(pre|post):
    prereqs = get_requirements(binary_pkg, binary_pkg.requires_pre,
                               binaries, ambiguities, query, hints,
                               filters, whatreqs, pick_first)
    deps.extend(prereqs)

    if follow_recommends:
        # Process Recommends:
        recommends = get_requirements(binary_pkg, binary_pkg.recommends,
                                      binaries, ambiguities, query, hints,
                                      filters, whatreqs, pick_first)
        deps.extend(recommends)

    # Now get the build dependencies for this package
    source_pkg = get_srpm_for_package(query, binary_pkg)

    if source_pkg.name not in sources:
        # Don't process the same Source RPM twice
        sources[source_pkg.name] = source_pkg

        # Get the BuildRequires for this Source RPM
        buildreqs = get_requirements(source_pkg, source_pkg.requires,
                                     binaries, ambiguities, query, hints,
                                     filters, whatreqs, pick_first)
        deps.extend(buildreqs)

    for dep in deps:
        recurse_self_host(dep, binaries, sources, ambiguities, query, hints,
                          filters, whatreqs, pick_first, follow_recommends)


def resolve_ambiguity(dependencies, ambiguity):
    """
    Determine if any of the contents of an ambiguous lookup
    is already resolved by something in the dependencies.
    """
    for key in sorted(ambiguity, key=ambiguity.get):
        if key in dependencies:
            return True
    return False

