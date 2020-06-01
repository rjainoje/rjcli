import setuptools
from setuptools import setup, find_packages

install_requirements = [
    "click>=7.1.2",
    "click-shell>=2.0",
    "DateTime>=4.3",
    "pyfiglet>=0.8.post1",
    "requests>=2.23.0",
    "tabulate>=0.8.7",
    "urllib3>=1.25.9",
]

# calling the setup function  
setuptools.setup( 
        name ='rjcli',
        version ='1.0.1',
        author ='Raghava Jainoje',
        author_email ='raghavachary_j@yahoo.com',
        url ='https://github.com/rjainoje/rjcli',
        description ='CLI Interface for PPDM',
        long_description = open("README.rst").read(),
        long_description_content_type ="text/markdown", 
        license ='MIT',
        packages=setuptools.find_packages(),
        install_requires = install_requirements,
        entry_points="""
        [console_scripts]
        rjcli=ppdm.rjcli:my_app
        """,
        classifiers =[
            "Programming Language :: Python :: 3.8", 
            "License :: OSI Approved :: MIT License", 
            "Operating System :: OS Independent", 
        ],
        
) 