# Item Catalog Project

This repository contains the code regarding the "Build an Item Catalog Application"

## Setting-up

1. In order to use the application, one must have installed [Vagrant](https://www.vagrantup.com/downloads.html) and [Virtual Box](https://www.virtualbox.org/).

2. Launch the Vagrant virtual machine inside the root folder (itemcatalog), using the command line and the following commands:
```
vagrant up
vagrant ssh
```
3. Then, one must access the catalog folder.
  Before running the application, you must install two modules that are not yet installed in the vm. Just type:
  ```
  sudo pip install flask.httpauth
  sudo pip install passlib
  ```
  and then finally, run 'python application.py'.

4. When 'http:\\localhost:5000' is accessed, you will see the item catalog. Congrats!

## Functions

You can add new items through the 'add new album' buttom in all pages, and edit / delete de albums inside the album information, clicking in the album cover.
First, though, you must login, using your Google Account, through the link in the superior right corner.

Thanks a lot.
