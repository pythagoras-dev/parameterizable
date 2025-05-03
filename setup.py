import setuptools

with open("README.md", "r") as f:
    long_description = f.read()

setuptools.setup(
    name="parameterizable"
    ,version="0.2.4"
    ,author="Vlad (Volodymyr) Pavlov"
    ,author_email="vlpavlov@ieee.org"
    ,description= "Library for work with parameterizable classes."
    ,long_description=long_description
    ,long_description_content_type="text/markdown"
    ,url="https://github.com/pythagoras-dev/parameterizable"
    ,packages=["parameterizable"]
    ,classifiers=[
        "Development Status :: 3 - Alpha"
        , "Intended Audience :: Developers"
        , "Intended Audience :: Science/Research"
        , "Programming Language :: Python"
        , "Programming Language :: Python :: 3"
        , "License :: OSI Approved :: MIT License"
        , "Operating System :: OS Independent"
        , "Topic :: Software Development :: Libraries"
        , "Topic :: Software Development :: Libraries :: Python Modules"
    ]
    ,keywords='parameters'
    ,python_requires='>=3.10'
    ,install_requires=[
        'pytest'
    ]

)