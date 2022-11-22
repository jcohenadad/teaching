from setuptools import setup, find_packages

with open('requirements.txt') as f:
    requirements = f.readlines()

setup(
    name='teaching',
    version='0.1',
    author='Julien Cohen-Adad',
    author_email='aac@example.com',
    packages=find_packages(),
    url='',
    license='LICENSE',
    description='Set of tools to manage teaching-related tasks, such as fetch responses from Google Forms, send emails '
                'to students, compute average grades, etc.',
    long_description=open('README.md').read(),
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'send_feedback = teaching.gbm6904_send_feedback:main',
            ]
        }
    )
