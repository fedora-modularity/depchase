# depchase

The depchase python module is an interface to the DNF API to perform
complicated lookups on package dependencies.

## Setup
This tool requires the following pre-requisites:
* python3-dnf >= 2.0 (See below)
* python3-click

### Installing DNF 2.x on Fedora 24 and 25
```
$ dnf copr enable rpmsoftwaremanagement/dnf-nightly
$ dnf update python3-dnf
```

## Install the package locally
```
$ python3 setup.py install --user
```
This will install the `depchase` command as `~/.local/bin/depchase`

You may wish to add this to your default PATH variable in `~/.bashrc` by doing:
```
$ echo "export PATH=$PATH:$HOME/.local/bin" >> ~/.bashrc
```

## How to run:

### Get the source RPM for one or more packages
```
Usage: depchase getsourcerpm [OPTIONS] [PKGNAMES]...

  Look up the SRPMs from which these binary RPMs were generated.

  This list will be displayed deduplicated and sorted.

Options:
  --full-name / --no-full-name
  --os TEXT                     Specify the operating system.
  --version INTEGER             Specify the version of the OS repodata to
                                compare against.
  --arch TEXT                   Specify the CPU architecture.
  --milestone TEXT              Specify the pre-release milestone. If not
                                provided, the final release will be used.
  --help                        Show this message and exit.
```


### Get the recursive list of all runtime dependencies for one or more packages
```
Usage: depchase neededby [OPTIONS] [PKGNAMES]...

  Look up the dependencies for each specified package and display them in a
  human-parseable format.

Options:
  --hint TEXT                     Specify a package to be selected when more
                                  than one package could satisfy a
                                  dependency.
                                  This option may be specified multiple times.
                                  For example, it is recommended to use
                                  --hint=glibc-minimal-langpack
  --filter TEXT                   Specify a package to be skipped during
                                  processing. This option may be
                                  specified
                                  multiple times.

                                  This is useful when some
                                  packages are provided by a lower-level
                                  module
                                  already contains the package and its
                                  dependencies.
  --whatreqs TEXT                 Specify a package that you want to identify
                                  what pulls it into the complete
                                  set. This
                                  option may be specified multiple times.
  --recommends / --no-recommends
  --pick-first / --no-pick-first  If multiple packages could satisfy a
                                  dependency and no --hint package will
                                  fulfill the requirement, automatically
                                  select one from the list.

                                  Note: this result
                                  may differ between runs depending upon how
                                  the list is
                                  sorted. It is recommended to use
                                  --hint instead, where practical.
  --os TEXT                       Specify the operating system.
  --version INTEGER               Specify the version of the OS repodata to
                                  compare against.
  --arch TEXT                     Specify the CPU architecture.
  --milestone TEXT                Specify the pre-release milestone. If not
                                  provided, the final release will be used.
  --binary-short-file TEXT        The file to contain the short version of the
                                  detected dependencies. (Just the package
                                  name)
  --binary-full-file TEXT         The file to contain the long version of the
                                  detected dependencies. (Package name,
                                  version, architecture, etc.)
  --source-short-file TEXT        The file to contain the short version of the
                                  detected dependencies. (Just the package
                                  name)
  --source-full-file TEXT         The file to contain the long version of the
                                  detected dependencies. (Package name,
                                  version, architecture, etc.)
  --help                          Show this message and exit.

```

### Get the list of packages required to self-host for one or more packages
"Self-hosting" in this context means "all of the packages necessary to be able
to build all the packages listed on the command line, plus recursively any
packages required to build those BuildRequires as well.

```
Usage: depchase neededtoselfhost [OPTIONS] [PKGNAMES]...

  Look up the build dependencies for each specified package and all of their
  dependencies, recursively and display them in a human-parseable format.

Options:
  --hint TEXT                     Specify a package to be selected when more
                                  than one package could satisfy a
                                  dependency.
                                  This option may be specified multiple times.
                                  For example, it is recommended to use
                                  --hint=glibc-minimal-langpack

                                  For build
                                  dependencies, the default is to exclude
                                  Recommends: from the
                                  dependencies of the
                                  BuildRequires.
  --recommends / --no-recommends
  --pick-first / --no-pick-first  If multiple packages could satisfy a
                                  dependency and no --hint package will
                                  fulfill the requirement, automatically
                                  select one from the list.

                                  Note: this result
                                  may differ between runs depending upon how
                                  the list is
                                  sorted. It is recommended to use
                                  --hint instead, where practical.
  --filter TEXT                   Specify a package to be skipped during
                                  processing. This option may be
                                  specified
                                  multiple times.

                                  This is useful when some
                                  packages are provided by a lower-level
                                  module
                                  already contains the package and its
                                  dependencies.
  --whatreqs TEXT                 Specify a package that you want to identify
                                  what pulls it into the complete
                                  set. This
                                  option may be specified multiple times.
  --os TEXT                       Specify the operating system.
  --version INTEGER               Specify the version of the OS repodata to
                                  compare against.
  --arch TEXT                     Specify the CPU architecture.
  --milestone TEXT                Specify the pre-release milestone. If not
                                  provided, the final release will be used.
  --binary-short-file TEXT        The file to contain the short version of the
                                  detected dependencies. (Just the package
                                  name)
  --binary-full-file TEXT         The file to contain the long version of the
                                  detected dependencies. (Package name,
                                  version, architecture, etc.)
  --source-short-file TEXT        The file to contain the short version of the
                                  detected dependencies. (Just the package
                                  name)
  --source-full-file TEXT         The file to contain the long version of the
                                  detected dependencies. (Package name,
                                  version, architecture, etc.)
  --help                          Show this message and exit.
```
