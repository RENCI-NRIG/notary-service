from setuptools import setup

setup(name='ns_jwt',
      version='0.1',
      description='Notary Service support for JWT',
      url='https://github.com/RENCI-NRIG/notary-service',
      author='Ilya Baldin',
      author_email='ibaldin@renci.org',
      license='MIT',
      packages=['ns_jwt'],
      install_requires=[
          'PyJWT',
          'cryptography',
          'python-dateutil',
      ],
      zip_safe=False)
