Tyou
====

Another Flask based blog

To deploy this blog:

0. install libmysqlclient-dev,python-dev (ubuntu)
1. run `pip install -r requirements.txt`
2. `cp config.py.sample to prj/config.py`, `cp secret_keys.py.sample secret_keys.py` database configuration, secret keys configuration
3. run `export FLASK_APP=path to app.py`.
4. run `flask create_user` to creaet a user
5. try `python app.py`, and open http://127.0.0.1:5000
6. deploy this app to web servers like apache or ngnix
7. create `uploads` folder in project root folde, making sure webserver is able to write. 
