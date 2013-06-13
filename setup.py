from distutils.core import setup

setup(
    name='administrator',
    version='0.2',
    author='Fil Krynicki',
    author_email='filipkrynicki@gmail.com',
    packages=['administrator'],
    package_data={'administrator': ['administrator/schema/*']},
    license='LICENSE.txt',
    description='A server with an API for handing out generic JSON jobs to requesters.',
    long_description=open('README.md').read(),
    install_requires=[
		"flask >= 0.8-1",
            ],
)
