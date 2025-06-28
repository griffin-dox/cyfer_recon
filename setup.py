from setuptools import setup, find_packages

setup(
    name='cyfer-recon',
    version='0.1.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'typer',
        'rich',
        'questionary',
    ],
    entry_points={
        'console_scripts': [
            'cyfer-recon=cyfer_recon.main:main',
        ],
    },
    author='Griffin Dox',  # Update to your real name or organization
    description='Cybersecurity Recon Automation CLI Tool',
    url='https://github.com/griffin-dox/cyfer_recon',  # Update to your real repo URL
    python_requires='>=3.7',  # Recommended for modern Python packages
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    long_description=open('README.md', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
)
