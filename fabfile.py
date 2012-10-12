import time
import datetime as date

from fabric import utils
from fabric.api import *
from fabric.contrib.project import rsync_project
from fabric.contrib import files, console
from fabric.operations import *
from fabric.colors import *


# globals
env.colors = True
env.format = True
env.release = time.strftime('%Y%m%d%H%M%S')
env.use_ssh_config = True
env.roledefs = {
    'test': ['localhost'],
    'dev':  ['localhost'],
    'prod': ['localhost']
} 


@task
def dev():
    env.hosts = env.roledefs['dev']
    env.project_path = '/home/path/to/application'
    env.project_name = 'huskyhustle'
    env.module_name  = 'husky'
    env.media_name   = 'static'
    env.settings     = 'settings-dev'
    print_env()

@task
def prod():
    env.hosts = env.roledefs['prod']
    env.project_path = '/home/path/to/application'
    env.project_name = 'huskyhustle'
    env.module_name  = 'husky'
    env.media_name   = 'static'
    env.settings     = 'settings-prod'
    print_env()

@task
def hello(name="world"):
    print("Hello %s, these are your commands!" % name)
    with cd(env.project_path):
        run('whoami')
        run('ls %s' % env.project_path)
        run('pwd')

@task
def deploy():
    release = '%s-%s' % (env.project_name, date.datetime.now().strftime(env.release))
    project = os.path.join(env.project_path, env.project_name)
    module  = os.path.join(project, env.module_name)
    media   = os.path.join(module, env.media_name)
#    print('%s/builds = %s' % (project, files.exists('%s/builds' % env.project_path)))
#    if files.exists('%s/builds' % env.project_path) == False:
    run('mkdir -p %s/builds' % env.project_path)
#    print('%s = %s' % (project, files.exists(project)))
#    if files.exists(project) == True:
    run('mv %s %s/builds/%s' % (project, env.project_path, release))
    local('tar -cvzf /tmp/%s.tgz %s' % (env.project_name, env.project_name))
    put('/tmp/%s.tgz' % env.project_name, env.project_path)
    with cd(env.project_path):
        run('tar -zxf %s.tgz' % env.project_name)
        run('rm %s.tgz' % env.project_name)
    local('tar -cvzf /tmp/%s.tgz %s' % (env.module_name, env.module_name))
    put('/tmp/%s.tgz' % env.module_name, project)
    with cd(project):
        run('tar -zxf %s.tgz' % env.module_name)
        run('rm %s.tgz' % env.module_name)
    run('mv %s/public/%s %s/builds/%s/%s' % (env.project_path, env.media_name, env.project_path, release, env.module_name))
    run('mv %s %s/public/%s' % (media, env.project_path, env.media_name))
    run('mv %s/settings.py %s/settings-local.py' % (project, project))
    run('mv %s/%s.py %s/settings.py' % (project, env.settings, project))
    restart()


def better_put(local_path, remote_path, mode=None):
    put(local_path.format(**env), remote_path.format(**env), mode)

def print_env():
    print(date.datetime.now().strftime(env.release))
    print("Here are your Environment Variables:")
    print("Host: %s" % env.hosts)
    print("Project Path: %s" % env.project_path)
    print("Project Name: %s" % env.project_name)
    print("Module Name: %s" % env.module_name)
    print("Media Name: %s" % env.media_name)
    print("Settings: %s" % env.settings)
    print(" ------------------------------------ ")

@task
def restart():
    run('pkill python')
