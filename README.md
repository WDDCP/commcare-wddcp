# commcare-wddcp
*Forked from https://github.com/dimagi/commcare-hq* 
 
<br> 

## Worflow and branch structure
Branch **:dimagi** will be kept up to date with https://github.com/dimagi/commcare-hq.

Branch **:wddcp** is the default branch for commcare-wddcp, and releases will be made from here. This branch will reflect updates in branch **:dimagi** as closely as possible.

(Branch **:master** has been removed to avoid confusion)

## Contributions to commcare-wddcp
Contributors to commcare-wddcp should fork **this** repo (https://github.com/WDDCP/commcare-wddcp), and should make sure their WIP branches are kept up-to-date with branch **:wddcp**.

Branch **:wddcp** is protected, so all Pull Requests should be made into an unprotected branch and then merged after being accepted.

## Quickstart (local)
`vagrant up` Runs from Vagrantfile and provisions everything

`vagrant ssh` Get into new vagrant box 

`cd /vagrant` Be in the correct folder 

`./scripts/docker runserver --bootstrap` Build and set up required services 

`./scripts/docker runserver` Run -- available from localhost:8000 
