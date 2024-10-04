from setuptools import setup, find_packages

setup(
    name='common_django',
    version='0.1',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[],
    author='Kapil Yadav',
    author_email='kapil.yadav@dhl.com',
    description='A minimal Django package with Email Sending and Logging functionality.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/lpkapil/common.git',
    classifiers=[
        'Framework :: Django',
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
    ],
)
