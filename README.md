# commcare-wddcp
*Forked from https://github.com/dimagi/commcare-hq* 
 
<br> 

## Workflow and branch structure
Branch **:dimagi** will be kept up to date with https://github.com/dimagi/commcare-hq by repository owners. It is locked against Pull Requests, as the only route into it should be by merging from upstream.

Branch **:wddcp** is the default branch for commcare-wddcp, and releases will be made from here. This branch will reflect updates in branch **:dimagi** as closely as possible, and therefore **:wddcp** will be N->inf commits ahead but n->0 commits behind **:dimagi**.

Branch **:wddcp** is protected, so all Pull Requests should be made into an unprotected branch and will be merged by a repository owner after being accepted.

(Branch **:master** has been removed to avoid confusion)

## Contributions to commcare-wddcp
Contributors to commcare-wddcp should fork **this** repo (https://github.com/WDDCP/commcare-wddcp), and should make sure their WIP branches are kept up-to-date with branch **:wddcp**.

## Quickstart (local)
### Build
`vagrant up` Runs from Vagrantfile and provisions everything
 - This also runs `git submodule update --init --recursive`

`vagrant ssh` Get into new vagrant box 

`cd /vagrant` Be in the correct folder 

`./scripts/docker runserver --bootstrap` Build and set up required services 

`./scripts/docker runserver` Run -- available from localhost:8000 

### Development
`vagrant ssh` Be inside vagrant box

`./scripts/docker bash` For CLI inside appropriate docker image 

Files are in /mnt/commcare

`./manage.py makemigrations` then `./manage.py migrate`

