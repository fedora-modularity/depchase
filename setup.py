from setuptools import setup

setup(name="depchase",
      version="1",
      url="https://github.com/fedora-modularity/depchase",
      license="MIT",
      author="Igor Gnatenko",
      author_email="ignatenkobrain@fedoraproject.org",
      install_requires=["click>=6"],
      scripts=["depchase"])
