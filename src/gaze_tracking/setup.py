from distutils.core import setup
from catkin_pkg.python_setup import generate_distutils_setup
d = generate_distutils_setup(
    packages=['gaze_tracking'],
    package_dir={'': 'src'}
)
setup(**d)
