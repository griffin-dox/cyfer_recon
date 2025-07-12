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
        'typer>=0.7.0',
        'rich>=13.0.0',
        'questionary>=1.10.0',
        'requests>=2.28.0',
        'linkfinder>=0.3.0',
        'beautifulsoup4>=4.11.0',
        'lxml>=4.9.0',
        'colorama>=0.4.0',
        'urllib3>=1.26.0',
        'certifi>=2022.0.0',
        'charset-normalizer>=2.1.0',
        'pyyaml>=6.0.0',
        'python-dateutil>=2.8.0',
    ],
    entry_points={
        'console_scripts': [
            'cyfer-recon=cyfer_recon.main:main',
        ],
    },
    author='Griffin Dox',  # Update to your real name or organization
    description='Cybersecurity Recon Automation CLI Tool',
    url='https://github.com/griffin-dox/cyfer_recon',  # Update to your real repo URL
    python_requires='>=3.8',  # Updated for better compatibility with modern dependencies
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    long_description=long_description,
    long_description_content_type='text/markdown',
)
