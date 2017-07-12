# commcare-wddcp
*Forked from https://github.com/dimagi/commcare-hq* 
 
<br> 

## Workflow and branch structure
Branch **commcare-wddcp:dimagi** will be kept up to date with dimagi/commcare-hq https://github.com/dimagi/commcare-hq by repository owners. It is locked against Pull Requests, as the only route into it should be by merging from upstream. NB: These merges should all be fast-forward, and if they're not then something has gone wrong.

Branch **:commcare-wddcp/wddcp** is the default branch for commcare-wddcp, and releases will be made from here. We aim to take updates from upstream (dimagi/commcare-hq:master) as soon as practical, limited by available development time, and conflicts with out changes. Upstream changes should be checked out into a new branch for testing, then 

Branch **:commcare-wddcp/wddcp** is protected, therefore all Pull Requests must be approved by a repository owner. It is preferred that Pull Requests are up-to-date with :wddcp.

(Branch **:commcare-wddcp/master** has been removed to avoid confusion)

## Contributions to commcare-wddcp
Contributors to commcare-wddcp should fork the core WDDCP repo (https://github.com/WDDCP/commcare-wddcp), and should make sure their WIP branches are kept up-to-date with branch **commcare-wddcp/:wddcp**.

## Quickstart (local)
### Build
In project root on your local machine:

`vagrant up` Runs from Vagrantfile and provisions everything
 - This also runs `git submodule update --init --recursive`

`vagrant ssh` Get into new vagrant box 

`cd /vagrant` Be in the correct folder 

`./scripts/docker bash` Start and enter CLI to appropriate docker image 

`cd /mnt/commcare` Be in the folder where files are

`./manage.py makemigrations` then `./manage.py migrate` to set up django

### Run
Inside vagrant machine (but not on docker image): 

`./scripts/docker runserver --bootstrap` Build and set up required services 

`./scripts/docker runserver` Application  available from localhost:8000 



