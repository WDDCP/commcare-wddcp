# commcare-wddcp
*Forked from https://github.com/dimagi/commcare-hq* 
 
This is the GitHub repository for WDDCP, comprising an installation of CommCare HQ forked from [https://github.com/dimagi/commcare-hq](https://github.com/dimagi/commcare-hq). 
 
<br> 

## Workflow and branch structure

Branch **commcare-wddcp:wddcp** is the main branch for WDDCP: Pull Requests should be made into this branch, and releases will be made from here. The branch is protected, so all Pull Requests must be approved by a repository owner.

Branch **commcare-wddcp:dimagi** will be kept up to date with **dimagi:commcare-hq:master** by repository owners. It is locked against Pull Requests, as the only route into it should be by merging from upstream. NB: These merges should all be fast-forward: if they're not then something has gone wrong.

We aim to take updates from upstream (**dimagi/commcare-hq:master**) into **commcare-wddcp:wddcp** as soon as practical, limited by available development time, and conflicts with our changes. Upstream changes should be checked out into a new branch for testing before being incorporated. 

(Branch **commcare-wddcp:master** has been removed to avoid confusion (ha), as it would otherwise be unclear whether commcare-wddcp:master tracked dimagi:master or was the main branch for the WDDCP.)

## Contributions to commcare-wddcp
Contributors to commcare-wddcp should fork the core WDDCP repo (https://github.com/WDDCP/commcare-wddcp), and should make sure their WIP branches are kept up-to-date with branch **commcare-wddcp:wddcp**.

## Quickstart (local)
### Build
In project root:<br>

Start Vagrant
`vagrant up` 
 - Runs from Vagrantfile and provisions everything
 - Also runs `git submodule update --init --recursive`

Get into new vagrant box: <br>
`vagrant ssh`

Be in the correct folder: <br>
`cd /vagrant` 

Build and set up required services: <br>
`./scripts/docker runserver --bootstrap` <br>
(You might need to ctrl^c and restart if it hangs...)

### Run
Inside vagrant machine:<br>
`./scripts/docker runserver` <br>

### Further setup
Get into vagrant box again and be in the project root: <br>
`vagrant ssh`
`cd /vagrant`

Start CLI to appropriate docker image: <br>
`./scripts/docker bash` 

Be in the folder where files are: <br>
`cd /mnt/commcare-hq`

Update django models: <br>
`./manage.py makemigrations` then `./manage.py migrate` <br>
If this doesn't work then try turning the server off and on again (the `./scripts/docker runserver` step) 

**Application should now be available from localhost:8000 (or wherever specified in the `Vagrantfile`)**




