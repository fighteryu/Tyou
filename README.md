Tyou
====

Another Flask based blog

To deploy this blog:

0. install libmysqlclient-dev,python-dev (ubuntu)
1. run `pip install -r requirements.txt`
2. edit config.py, add username,password,database to config 
3. run `python manage.py generatekey` to generate a session key
4. run `python manage.py createuser <username> <password>` to creaet a user
5. try `python app.py`, and open http://127.0.0.1:5000
6. deploy this app to web servers like apache or ngnix
7. run `python manage.py backup` as cron job to backup your blog data to `uploads` folder 
