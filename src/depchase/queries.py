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

import platform
import dnf

from depchase.util import get_multi_arch
from depchase.util import splitFilename

from depchase.exceptions import NoSuchPackageException
from depchase.exceptions import TooManyPackagesException


def get_pkg_by_name(q, pkgname, arch):
    """
    Try to find the package name as primary_arch, multi_arch and then noarch.
    This function will return exactly one result. If it finds zero or multiple
    packages that match the name, it will throw an error.
    """

    # Check the primary arch, multi-arch and noarch packages
    matched = q.filter(name=pkgname, latest=True, arch=arch)
    if len(matched) > 1:
        raise TooManyPackagesException(pkgname)

    if len(matched) == 1:
        # Exactly one package matched. We'll prioritize the archful package if
        # the same package would satisfy a multi-arch version as well.
        # Technically it's possible for there to also be a noarch package
        # with the same name, which is an edge case I'm not optimizing for
        # yet.
        return matched[0]

    multi_arch = get_multi_arch(arch)
    if multi_arch:
        matched = q.filter(name=pkgname, latest=True, arch=multi_arch)
        if len(matched) > 1:
            raise TooManyPackagesException(pkgname)

        if len(matched) == 1:
            # Exactly one package matched
            # Technically it's possible for there to also be a noarch package
            # with the same name, which is an edge case I'm not optimizing for
            # yet.
            return matched[0]

    matched = q.filter(name=pkgname, latest=True, arch='noarch')
    if len(matched) > 1:
        raise TooManyPackagesException(pkgname)

    if len(matched) == 1:
        # Exactly one package matched
        return matched[0]
    raise NoSuchPackageException(pkgname)


def get_srpm_for_package(query, pkg):
    # Get just the base name of the SRPM
    try:
        (sourcename, _, _, _, _) = splitFilename(pkg.sourcerpm)
    except Exception:
        print("Failure: %s(%s)" % (pkg.sourcerpm, pkg.name))
        raise

    matched = query.filter(name=sourcename, latest=True, arch='src')
    if len(matched) > 1:
        raise TooManyPackagesException(pkg.name)

    if len(matched) == 1:
        # Exactly one package matched
        return matched[0]

    raise NoSuchPackageException(pkg.name)


def get_srpm_for_package_name(query, pkgname):
    """
    For a given package, retrieve a reference to its source RPM
    """
    pkg = get_pkg_by_name(query, pkgname)

    return get_srpm_for_package(query, pkg)


def _append_requirement(reqs, parent, pkg, filters, whatreqs):
    """
    Check if this package is in the filter list. If it is, then
    do not add it to the list of packages to recurse into.
    """
    if whatreqs is not None and pkg.name in whatreqs:
        print("%s is pulled in by %s" % (pkg.name, parent.name),
              file=sys.stderr)

    if filters is None or pkg.name not in filters:
        reqs.append(pkg)

def get_requirements(parent, reqs, dependencies, ambiguities,
                     query, hints, filters, whatreqs, pick_first):
    """
    Share code for recursing into requires or recommends
    """
    requirements = []

    for require in reqs:
        required_packages = query.filter(provides=require, latest=True,
                                         arch=primary_arch)

        # Check for multi-arch packages satisfying it
        if len(required_packages) == 0 and multi_arch:
            required_packages = query.filter(provides=require, latest=True,
                                             arch=multi_arch)

        # Check for noarch packages satisfying it
        if len(required_packages) == 0:
            required_packages = query.filter(provides=require, latest=True,
                                             arch='noarch')

        # If there are no dependencies, just return
        if len(required_packages) == 0:
            print("No package for [%s] required by [%s-%s-%s.%s]" % (
                str(require),
                parent.name, parent.version,
                parent.release, parent.arch),
                  file=sys.stderr)
            continue

        # Check for multiple possible packages
        if len(required_packages) > 1:
            # Handle 'hints' list
            found = False
            for choice in hints:
                for rpkg in required_packages:
                    if rpkg.name == choice:
                        # This has been disambiguated; use this one
                        found = True
                        _append_requirement(requirements, parent, rpkg,
                                           filters, whatreqs)
                        break
                if found:
                    # Don't keep looking once we find a match
                    break

            if not found:
                if pick_first:
                    # First try to use something we've already discovered
                    for rpkg in required_packages:
                        if rpkg.name in dependencies:
                            return

                    # The user instructed processing to just take the first
                    # entry in the list.
                    for rpkg in required_packages:
                        if rpkg.arch == 'noarch' or rpkg.arch == \
                                primary_arch or rpkg.arch == multi_arch:
                            _append_requirement(requirements, parent, rpkg,
                                               filters, whatreqs)
                            break
                    continue
                # Packages not solved by 'hints' list
                # should be added to the ambiguities list
                unresolved = {}
                for rpkg in required_packages:
                    unresolved["%s#%s" % (rpkg.name, rpkg.arch)] = rpkg
                ambiguities.append(unresolved)

            continue

        # Exactly one package matched, so proceed down into it.
        _append_requirement(requirements, parent, required_packages[0],
                           filters, whatreqs)

    return requirements

