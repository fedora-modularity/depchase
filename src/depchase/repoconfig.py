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


import dnf
import sys

from distutils.version import LooseVersion
if LooseVersion(dnf.const.VERSION) < LooseVersion('2.0.0'):
    raise NotImplementedError("DNF 2.x required.")


def _is_secondary_arch(arch, version):
    if arch is 'x86_64':
        return False

    if arch is 'armhfp' and version >= 20:
        return False

    if arch is 'i386' and version <= 25:
        return False

    # All other architectures are alternative
    return True


def _setup_repo(base, reponame, URI, expire, force_expiration=False):
    repo = dnf.repo.Repo(reponame, base.conf)

    try:
        repo.mirrorlist = None
        repo.metalink = None
        repo.baseurl = URI
        repo.name = reponame
        repo._id = reponame
        repo.metadata_expire = expire
        base.repos.add(repo)
        repo.load()
        repo.enable()

        if force_expiration:
            repo._md_expire_cache()
    except dnf.exceptions.RepoError:
        repo.disable()
        raise


def prep_repositories(os="Fedora", version=25, milestone=None, arch='x86_64'):
    """
    Configures the necessary DNF repositories and returns a dnf.query.Query
    object for interacting with the repositories.
    """

    if os != "Fedora":
        raise NotImplementedError("Only Fedora supported today")

    basearch = dnf.rpm.basearch(arch)

    # Create custom configuration to specify the architecture
    config = dnf.conf.Conf()
    subst = dnf.conf.substitutions.Substitutions()
    subst['arch'] = arch
    subst['basearch'] = basearch
    config.substitutions = subst

    base = dnf.Base(conf=config)

    print_milestone = 'Final'
    if milestone:
        version_path = 'test/%d_%s' % (version, milestone)
        print_milestone = milestone
    else:
        version_path = str(version)

    # The Source RPMs always come from the primary path
    source_uri = "http://dl.fedoraproject.org/pub/fedora/linux/" \
                 "releases/%s/Everything/source/tree" % version_path

    # Keep the repodata for a year to save bandwidth
    # The frozen repositories do not change
    _setup_repo(base,
                'depchase-%s-%s-source' % (os, version_path),
                source_uri,
                365 * 24 * 60 * 60)

    # The primary and alternative architectures are stored separately
    if _is_secondary_arch(basearch, version):
        binary_uri = "http://dl.fedoraproject.org/pub/fedora-secondary/" \
                   "releases/%s/Everything/%s/os" % (version_path, basearch)
    else:
        binary_uri = "http://dl.fedoraproject.org/pub/fedora/linux/" \
                   "releases/%s/Everything/%s/os" % (version_path, basearch)

    # Keep the repodata for a year to save bandwidth
    # The frozen repositories do not change
    _setup_repo(base,
                'depchase-%s-%s' % (os, version_path),
                binary_uri,
                365 * 24 * 60 * 60)

    # Override repositories
    try:
        override_source_uri = \
            "https://fedorapeople.org/groups/modularity/repos/" \
            "fedora/gencore-override/%s/%s/sources" % (version_path, arch)
        # Always update the override repodata
        _setup_repo(base,
                    'depchase-%s-%s-%s-override-source' % (
                        version, print_milestone, arch),
                    override_source_uri, 0)

        override_binary_uri = \
            "https://fedorapeople.org/groups/modularity/repos/" \
            "fedora/gencore-override/%s/%s/os" % (version_path, arch)
        # Always update the override repodata
        _setup_repo(base,
                    'depchase-%s-%s-%s-override' % (
                        version, print_milestone, arch),
                    override_binary_uri, 0)
    except dnf.exceptions.RepoError:
        # Likely no override repo exists
        # Print a warning and continue
        print("WARNING: override repo has not been configured for "
              "%s %s on %s. Proceeding with official repos "
              "only." % (version, print_milestone, arch),
              file=sys.stderr)

    base.fill_sack(load_system_repo=False, load_available_repos=True)

    return base.sack.query()
