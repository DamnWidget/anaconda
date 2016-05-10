import sys
import pkg_resources
sys.path.insert(0, 'anaconda_lib')
sys.path.insert(1, 'anaconda_server')
pkg_resources.declare_namespace(__name__)
