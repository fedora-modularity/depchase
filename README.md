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
