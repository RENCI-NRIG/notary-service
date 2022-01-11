import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='ns_jwt',
    version='0.1.4',
    author='Ilya Baldin',
    author_email='ibaldin@renci.org',
    description='Notary Service support for JWT',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/RENCI-NRIG/notary-service',
    install_requires=[
        'PyJWT',
        'cryptography',
        'python-dateutil',
    ],
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    license='MIT',
    zip_safe=False
)
