try:
    # don't execute this in sublime text
    import sublime
except ImportError:
    from setuptools import setup, find_packages

    setup(
        name='anaconda_tests',
        packages=find_packages()
    )
