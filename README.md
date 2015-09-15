Tyou
====

Another Flask based blog

To deploy this blog:

0. install libmysqlclient-dev,python-dev (ubuntu)
1. run `pip install -r requirements.txt`
2. cp server/config.sample to prj/config.py, add username,password,database to config 
3. run `python manage.py generatekey` to generate a session key
4. run `python manage.py createuser <username> <password>` to creaet a user
5. try `python app.py`, and open http://127.0.0.1:5000
6. deploy this app to web servers like apache or ngnix
7. create `upload` folder in project root folde, making sure webserver is able to write. 
8. run `python manage.py backup` as cron job to backup your blog data to `uploads` folder 

To deploy app to apache
======
0. cp server/apache/tyou.conf to /etc/apache2/sites-available, enable this site
1. cp server/apache/tyou.wsgi to prj/app.wsgi, make sure wsgi file coudl be found by apache

To deploy app to nginx
======
0. install nginx,uwsgi
1. cp server/nginx/tyou_service.conf to /etc/init/, make sure uwsgi is running in the backend
2. cp server/nginx/tyou.conf to /etc/nginx/sites-available/, enable this site
