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
            'gbm6904_send_feedback = teaching.gbm6904_send_feedback:main',
            'gbm6125_send_feedback = teaching.gbm6125_send_feedback:main',
            'find_fill_excel = teaching.find_fill_excel:main',
            'find_corresponding_cells = teaching.find_corresponding_cells:main',
            'seuil_lettre = teaching.seuil_lettre:main',
            ]
        }
    )
