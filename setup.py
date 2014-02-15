from distutils.core import setup

setup(
    name='pyra',
    version='0.2.6dev',
    description="A python implementation of the GCL region algebra and query language described by Clarke et al.",
    author = "Adam Fourney",
    url = "http://github.com/afourney/pyra",
    packages=['pyra',],
    license=open('LICENSE').read(),
    long_description=open('README.txt').read(),
)
