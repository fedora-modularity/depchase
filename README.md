# depchase

The depchase tool is an simple script to lookup runtime (and/or buildtime)
requirements of package(s).

## Setup

- python3-solv
- python3-click
- python3-smartcols

## Installation

```
$ python3 setup.py install --user
```

You need to download files ending in `-primary.xml.gz` and `-filelists.xml.gz` and a file `repomd.xml` for each architecture you want to search through and for the sources. For Fedora rawhide you can download them from here:
 * https://dl.fedoraproject.org/pub/fedora/linux/development/rawhide/Everything/x86_64/os/repodata/
 * https://dl.fedoraproject.org/pub/fedora/linux/development/rawhide/Everything/source/tree/repodata/

The directory structure should be as follows:
```
repos
├── sources
│   └── repodata
│       ├── 41989692c9d39640c5e9321b3d3b33ac9677d12cbae4c87a51e2f4f9977dee2e-filelists.xml.gz
│       ├── 85006762236a619d384209fda289d0ff02fc296400bdf48bc1c6a524b499c459-primary.xml.gz
│       └── repomd.xml
└── x86_64
    └── repodata
        ├── 4e9d08a9d6ce135fb28c6a4df1fbabed317e16eba21f7acb814cc6c37ef4cca0-primary.xml.gz
        ├── 51a55ad79b12153b8c39b9fcceaa88c4f1d208100e9918f5cdf88e89920dedac-filelists.xml.gz
        └── repomd.xml
```

And the repos.cfg file should contain:

```
[DEFAULT]
basedir = /path/to/the/repos/  # FILL HERE THE CORRECT PATH

[base]
path = ${DEFAULT:basedir}/{arch}
[base-source]
path = ${DEFAULT:basedir}/sources
```

## Usage

```
$ depchase -a x86_64 -c repos.cfg resolve [--selfhost] foo --hint bar
```

`--selfhost` switches to searching of build dependencies

### Output

Output is a list of binary and source packages which were required for
resolution. You can parse them into multiple files using simple bash
script:

```bash
#!/bin/bash -eu

PREFIX=$1
> $PREFIX-binary-packages-full.txt
> $PREFIX-binary-packages-short.txt
> $PREFIX-source-packages-full.txt
> $PREFIX-source-packages-short.txt
while read -r nevra; do
  [[ "$nevra" == *.src || "$nevra" == *.nosrc ]] && type_="source" || type_="binary"
  name=${nevra%-*-*}
  echo "$nevra" >> $PREFIX-$type_-packages-full.txt
  echo "$name" >> $PREFIX-$type_-packages-short.txt
done

export LC_ALL=C
for f in $PREFIX-{binary,source}-packages-{full,short}.txt; do
  sort -u $f -o $f
done
```
