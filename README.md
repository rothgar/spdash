[WIP] System Provisioning Dashboard
========

Dashboard for viewing systems that are building or pending a rebuild.

View hosts at index.html or only pending systems at /pending

###API endpoints

`/api/v1/build/<status>/<hostname>`

Change the hosts status to <status>

`api/v1/delete/<hostname>`

Deletes host from current host list

`/apy/v1/refresh`

Refreshes TFTP folder to look for PXE files. Works with HEX IP files or hostnames

###Integrate with spdash

To integrate with spdash you can make curl calls to the api. Add the commands to your kickstart or preseed.

eg to integrate with cobbler

`curl -s -L --max-time 3 -X GET http://spdash:5000/api/v1/build/pre/$system_name`

It is recommended to run a /refresh at the end of the kickstart file to re-read PXE files.

`curl -s -L --max-time 3 -X GET http://spdash:5000/api/v1/refresh`

Run with Docker

Build the container

`sudo docker build -t spdash .`

Run the container

`sudo docker run -d --name spdash -p 5000:5000 -v /tftpboot/pxelinux.cfg:/pxe:ro spdash`

You can also run the application in debug mode by using the SPDASH_SETTINGS environment variable. There is a debug.cfg included which turns on debug mode.

`sudo docker run -d --name -pdash -p 5000:5000 -v /tftpboot/pxelinux.cfg:/pxe:ro -e SPDASH_SETTINGS=debug.cfg spdash`
