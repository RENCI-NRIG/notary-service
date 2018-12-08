from setuptools import setup

setup(name='ns_workflow',
      version='0.1',
      description='Notary Service Workflow using Neo4j/APOC',
      url='https://github.com/RENCI-NRIG/notary-service',
      author='Ilya Baldin',
      author_email='ibaldin@renci.org',
      license='MIT',
      packages=['ns_workflow'],
      install_requires=[
          'neo4j',
          'networkx',
      ],
      zip_safe=False)
