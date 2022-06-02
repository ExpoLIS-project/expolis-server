
import subprocess

subprocess.Popen ([
    '/usr/bin/g++',
    '-Icommon',
    '-Inr',
    '-Wall',
    'kriging/main_kriging.cpp',
    'common/data.cpp',
    'common/log.cpp',
    'common/options.cpp',
    '-o', 'interpolator-kriging',
    '-lm',
    '-lboost_program_options'
]).wait ()
