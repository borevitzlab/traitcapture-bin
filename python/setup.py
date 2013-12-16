from setuptools import setup

desc = """
traitcapture-bin:
    A series of scripts that do various stages of the traitcapture pipeline.
"""

setup(
    name="traitcapture-bin",
    py_modules=['exif2timestream', ],
    version="0.1a",
    description=desc,
    author="Kevin Murray",
    author_email="spam@kdmurray.id.au",
    url="https://github.com/borevitzlab/traitcapture-bin",
    keywords=["http", "multipart", "post", "urllib2"],
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "License :: OSI Approved :: GNU General Public License v3 or later " +
            "(GPLv3+)",
        ],
    test_suite="test",
    )
