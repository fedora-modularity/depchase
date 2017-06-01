# depchase

The depchase tool is an simple script to lookup runtime (and/or buildtime)
requirements of package(s).

## Setup

- python3-solv
- python3-click

## Installation

```
$ python3 setup.py install --user
```

## Usage

```
$ depchase -a x86_64 -c repos.cfg resolve [--selfhost] foo --hint bar
```

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
