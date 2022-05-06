from setuptools import setup

setup(
    name='TextCorporaReaders',
    version='1.0.0',
    keywords='nlp, text, json',
    url='https://github.com/sag111/TextCorporaReaders',
    description='Readers and writers for text corpora in different formats',
    packages=['TextCorporaReaders', 'TextCorporaReaders.Readers', 'TextCorporaReaders.Readers.Dialogue', 'TextCorporaReaders.Readers.jsons', 'TextCorporaReaders.Readers.Webanno'],
    #package_dir = {'TextCorporaReaders': ''},
    include_package_data=False,
    install_requires=[
        'dkpro-cassis'
    ]
)
