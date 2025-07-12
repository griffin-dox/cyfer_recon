from setuptools import setup, find_packages
import os

# Use absolute path for README.md
here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='cyfer-recon',
    version='0.1.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'typer>=0.6.0',
        'rich>=12.0.0',
        'questionary>=1.8.0',
    ],
    entry_points={
        'console_scripts': [
            'cyfer-recon=cyfer_recon.main:main',
        ],
    },
    author='Griffin Dox',  # Update to your real name or organization
    description='Cybersecurity Recon Automation CLI Tool',
    url='https://github.com/griffin-dox/cyfer_recon',  # Update to your real repo URL
    python_requires='>=3.7',  # Compatible with Python 3.7 through 3.13+
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    long_description=long_description,
    long_description_content_type='text/markdown',
)
