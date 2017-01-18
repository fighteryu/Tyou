#!/usr/bin/env python
# coding: utf-8
"""
    models.py
    ~~~~~~~~~~

"""
import os
import re
import time
import json
import random
import hashlib
import markdown2
from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
from flask.globals import current_app


db = SQLAlchemy()


class ModelMixin():
    @classmethod
    def get_page(cls, page, **kwargs):
        offset = current_app.config["PER_PAGE"] * (page - 1)
        return cls.query.filter_by(**kwargs).offset(offset).limit(current_app.config["PER_PAGE"])

    def save(self):
        db.session.add(self)

    def delete(self):
        db.session.delete(self)


class User(ModelMixin, db.Model):

    """setting = {
    page
    }
    """

    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), index=True)
    password = db.Column(db.String(256))
    salt = db.Column(db.String(20))
    config = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @classmethod
    def get_config(cls):
        user = cls.query.first()
        if user and user.config:
            return json.loads(user.config)
        return None

    def validate(self, password):
        hashed_password, salt = self.generate_salt_and_hash_password(password, self.salt)
        return hashed_password == self.password

    @classmethod
    def generate_salt_and_hash_password(cls, password, salt=None):
        salt = salt or str(time.time())[:20]
        password = hashlib.sha512(password.encode("utf-8")).hexdigest()
        password = hashlib.sha512(password.encode("utf-8") + salt.encode("utf-8")).hexdigest()
        return password, salt

    @classmethod
    def create_user(cls, username, password):
        users = cls.get_user(username=username)
        if users:
            raise Exception("{} already exists, please choose another".format(username))

        # generate_password
        password, salt = cls.generate_salt_and_hash_password(password)
        user = cls(
            username=username,
            password=password,
            salt=salt
        )
        user.save()

    @classmethod
    def delete_user(cls, username):
        user = cls.get_user(username=username)
        db.session.delete(user)
        db.session.commit()

    @classmethod
    def get_user(cls, **kwargs):
        return cls.query.filter_by(**kwargs).one_or_none()

    @classmethod
    def get_users(cls, **kwargs):
        return cls.query.filter_by(**kwargs)


class Post(ModelMixin, db.Model):
    __tablename__ = "post"
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(512), unique=True)
    title = db.Column(db.String(512))
    raw_content = db.Column(db.Text)
    content = db.Column(db.Text)
    keywords = db.Column(db.String(256), default="")
    metacontent = db.Column(db.String(256), default="")
    create_time = db.Column(db.DateTime, default=datetime.now)
    update_time = db.Column(db.DateTime, default=datetime.now)
    # required if need_key is True
    password = db.Column(db.String(20), default="")
    # tag seperated by comma
    tags = db.Column(db.String(256), default="")
    # editor html or markdown
    editor = db.Column(db.String(10))
    allow_visit = db.Column(db.Boolean, default=True)
    allow_comment = db.Column(db.Boolean, default=True)
    need_key = db.Column(db.Boolean, default=True)
    is_original = db.Column(db.Boolean, default=True)
    num_lookup = db.Column(db.Integer, default=0)

    def __init__(self, **kwargs):
        defaults = {
            "url": "",
            "title": "",
            "raw_content": "",
            "content": "",
            "keywords": "",
            "metacontent": "",
            "password": "",
            "tags": "",
            "editor": "markdown",
            "allow_visit": True,
            "allow_comment": True,
            "need_key": False,
            "is_original": True,
            "num_lookup": False
        }

        for key, value in kwargs.items():
            defaults.set_default(key, value)

        for key, value in defaults.items():
            setattr(self, key, value)

    @classmethod
    def get_post(cls, **kwargs):
        return cls.query.filter_by(**kwargs).one_or_none()

    @classmethod
    def get_posts(cls, **kwargs):
        return cls.query.filter_by(**kwargs)

    @classmethod
    def count(cls, **kargs):
        query = cls.query
        for key in kargs:
            query = query.filter(cls.__dict__[key] == kargs[key])
        return query.count()

    @classmethod
    def tag_search(cls, keyword, offset, limit):
        if not keyword:
            return []
        return cls.query.filter_by(allow_visit=True).\
            filter(cls.tags.like("%,"+keyword+",%")).\
            order_by(cls.post_id.desc()).offset(offset).limit(limit).all()

    @classmethod
    def tag_search_count(cls, keyword):
        if not keyword:
            return 0
        return cls.query.filter_by(allow_visit=True).\
            filter(cls.tags.like("%,"+keyword+",%")).count()

    @classmethod
    def text_search(cls, words, offset, limit):
        if len(words) == 0 or len(words) > 5:
            return []
        query = cls.query.filter_by(allow_visit=True)
        for word in words:
            query = query.filter(or_(
                cls.raw_content.like("%" + word + "%"),
                cls.title.like("%" + word + "%")
            ))
        return query.order_by(
            cls.post_id.desc()).offset(offset).limit(limit).all()

    @classmethod
    def text_search_count(cls, words):
        if len(words) == 0 or len(words) > 5:
            return 0
        query = cls.query.filter_by(allow_visit=True)
        for word in words:
            query = query.filter(or_(
                cls.raw_content.like("%" + word + "%"),
                cls.title.like("%" + word + "%")
            ))
        return query.count()

    @classmethod
    def get_last_x(cls, limit):
        return cls.query.filter_by(allow_visit=True).\
            order_by(cls.post_id.desc()).all()

    @classmethod
    def gen_raw_content(cls, content, editor):
        """Remove unused mark up tags, so that mysql is able to do text search
        a silly way to convert MarkDown to plain text:
            1. MarkDown to HTML
            2. HTML to text
        """
        if editor == "markdown":
            content = markdown2.markdown(content)
            return re.sub('<[^<]+?>', "", content)
        elif editor == "html":
            return re.sub('<[^<]+?>', "", content)

    @classmethod
    def random_post(cls):
        count = cls.query.filter_by(allow_visit=True, need_key=False).count()
        index = random.randint(0, count-1)
        post = cls.query.filter_by(allow_visit=True, need_key=False).offset(index).limit(1)
        return post[0]

    def get_tags(self):
        tags = self.tags.split(",")
        tags = [tag for tag in tags if tag]
        return tags

    def to_tags(self, taglist):
        tags = ",".join(taglist)
        return "," + tags + ","

    @property
    def html_content(self):
        if self.editor == "html":
            return self.content
        elif self.editor == "markdown":
            data = markdown2.markdown(self.content)
            return data
        else:
            return ""

    @property
    def plain_content(self):
            return self.raw_content

    def update_tags(self, new_string):
        """ Post.tags is a string in which tags are seperated by ",", we
        will seperate them and save to database. Use this method when you want
        to update or create a post
        Input:
            "abc,abc, abc,123"
        Output:
            ",abc,123,"
            sum for abc and 123 will increase by 1 ,We append comma before
            and after "abc,123", so we can do the follwoing mysql search
                `select * from tag where name like '%,tagname,%'`
        """
        duptags = new_string.split(",")
        newtags = set()
        for item in duptags:
            if item.strip() and item.strip() not in newtags:
                newtags.add(item.strip())

        oldtags = self.get_tags()
        addlist = [item for item in newtags if item not in oldtags]
        minuslist = [item for item in oldtags if item not in newtags]

        Tag.add(addlist)
        Tag.minus(minuslist)

        self.tags = self.to_tags(newtags)
        return self.tags

    def delete_tags(self):
        """Set Post.tags to "", this function will also deduce the count in Tag
        """
        return self.update_tags("")

    def delete_comments(self):
        comments = Comment.get_comments(post_id=self.id)
        for comment in comments:
            comment.delete()

    def delete(self):
        self.delete_tags()
        self.delete_comments()
        db.session.delete(self)
        db.session.commit()


class Tag(ModelMixin, db.Model):
    __tablename__ = "tag"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    count = db.Column(db.Integer, default=1)

    @classmethod
    def get_tag(self, **kwargs):
        return Tag.query.filter_by(**kwargs).one_or_none()

    @classmethod
    def get_tags(self, **kwargs):
        return Tag.query.filter_by(**kwargs)

    @classmethod
    def add(cls, tags):
        """never use this method directly , use Post.update_tags instead
        """
        for tag_name in tags:
            if tag_name:
                tag = Tag.get_tag(name=tag_name)
                if tag:
                    tag.count += 1
                    # items in uppercase and lowercase are treated as one tag.
                    # update name to get the most recent version
                    tag.name = tag_name
                else:
                    tag = Tag(name=tag_name)
                    db.session.add(tag)

    @classmethod
    def minus(cls, tags):
        for tag_name in tags:
            tag = Tag.get_tag(name=tag_name)
            if tag:
                if tag.count > 1:
                    tag.count -= 1
                else:
                    db.session.delete(tag)


class Comment(ModelMixin, db.Model):
    __tablename__ = "comment"
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
    email = db.Column(db.String(64))
    nickname = db.Column(db.String(20))
    content = db.Column(db.String(1024))
    refid = db.Column(db.Integer, db.ForeignKey('comment.id'))
    to = db.Column(db.String(20))
    create_time = db.Column(db.DateTime, default=datetime.now)
    ip = db.Column(db.String(64))
    website = db.Column(db.String(64))

    @classmethod
    def count(cls):
        return cls.query.count()

    @classmethod
    def get_comment(cls, **kwargs):
        return cls.query.filter_by(**kwargs).one_or_none()

    @classmethod
    def get_comments(cls, **kwargs):
        return cls.query.filter_by(**kwargs)


class Link(ModelMixin, db.Model):
    __tablename__ = "link"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    href = db.Column(db.String(1024))
    description = db.Column(db.String(64))
    create_time = db.Column(db.DateTime)
    display = db.Column(db.Boolean)

    @classmethod
    def get_link(cls, **kwargs):
        return cls.query.filter_by(**kwargs).one_or_none()

    @classmethod
    def get_links(cls, **kwargs):
        return cls.query.filter_by(**kwargs)

    @classmethod
    def count(cls):
        return cls.query.count()


class Media(ModelMixin, db.Model):
    fileid = db.Column(db.String(64), primary_key=True)
    filename = db.Column(db.String(64))
    # For a give filename , there could be multi file exits
    version = db.Column(db.Integer)
    content_type = db.Column(db.String(32))
    size = db.Column(db.Integer)
    create_time = db.Column(db.DateTime)
    display = db.Column(db.Boolean)

    @classmethod
    def get_media(cls, **kwargs):
        return cls.query.filter_by(**kwargs).one_or_none()

    @classmethod
    def get_medias(cls, **kwargs):
        return cls.query.filter_by(**kwargs)

    def filepath(self, upload_folder):
        return os.path.join(upload_folder, self.local_filename)

    @property
    def local_filename(self):
        return "f"+str(self.version)+self.filename

    @classmethod
    def count(cls):
        return cls.query.count()

    def delete(self):
        import config
        filepath = self.filepath(config.UPLOAD_FOLDER)
        try:
            os.remove(filepath)
        except Exception:
            pass
        db.session.delete(self)
        db.session.commit()


class Fail(db.Model):
    """This table is used to keep up with failed password attempt.
    """
    __tablename__ = "fail"
    fail_id = db.Column(db.Integer, primary_key=True)
    ip = db.Column(db.String(15))
    post_id = db.Column(db.Integer)
    count = db.Column(db.Integer, default=0)
    last_try = db.Column(db.DateTime)

    @classmethod
    def validate_client(cls, ip):
        """if one ip address failed for quite a few times, that clinet will have
        to wait for quite a few seconds
        """
        query = cls.query.filter_by(ip=ip).order_by(cls.last_try.desc())
        record = query.first()

        if record and record.is_above_threshold():
            latency = datetime.now() - record.last_try
            if latency.total_seconds() < 5:
                return False
        return True

    @classmethod
    def add_record(cls, ip, post_id):
        record = cls.query.filter_by(ip=ip, post_id=post_id).first()
        if not record:
            record = cls(ip=ip, post_id=post_id)
            record.count = 0
        record.count += 1
        record.last_try = datetime.now()
        db.session.add(record)
        db.session.commit()
        return record

    @classmethod
    def clear_record(cls, ip, post_id):
        record = cls.query.filter_by(ip=ip, post_id=post_id).first()
        if record:
            db.session.delete(record)
            db.session.commit()

    def is_above_threshold(self):
        """if count > 5, the password attempt is above threadshold
        """
        return self.count > 5


def gen_sidebar(config):
    rr = {
        "taglist": None,
        "commentlist": None,
        "linklist": None
    }

    tags = Tag.get_tags().order_by(Tag.count.desc()).limit(config["TAG_COUNT"])
    rr["tasg"] = tags
    comments = Comment.get_comments().order_by(Comment.id.desc()).limit(config["COMMENT_COUNT"])
    rr["comments"] = comments
    links = Link.get_links().order_by(Link.id.desc()).limit(config["LINK_COUNT"])
    rr["links"] = links

    announce = Post.get_post(id=config["ANNOUNCE_ID"])
    rr["announce"] = announce
    rr["announce_length"] = config["ANNOUNCE_LENGTH"]
    return rr


def export_all():
    """export all blog data"""
    postlist = Post.query.all()
    linklist = Link.query.all()
    medialist = Media.query.all()

    ex_post = []
    for post in postlist:
        # Back up all comments
        ex_comment = []
        commentlist = Comment.get_comments(post_id=post.id)
        for comment in commentlist:
            ex_comment.append({
                "id": comment.id,
                "post_id": comment.post_id,
                "email": comment.email,
                "nickname": comment.nickname,
                "content": comment.content,
                "to": comment.to,
                "refid": comment.refid,
                "create_time": int(comment.create_time.strftime("%s")),
                "ip": comment.ip,
                "website": comment.website
            })

        ex_post.append({
            "id": post.id,
            "url": post.url,
            "title": post.title,
            "content": post.content,
            "keywords": post.keywords,
            "metacontent": post.metacontent,
            "create_time": int(post.create_time.strftime("%s")),
            "update_time": int(post.update_time.strftime("%s")),
            "tags": post.tags,
            "allow_visit": post.allow_visit,
            "allow_comment": post.allow_comment,
            "need_key": post.need_key,
            "is_original": post.is_original,
            "editor": post.editor,
            "num_lookup": post.num_lookup,
            "commentlist": ex_comment
        })

    # Backup all links
    ex_link = []
    for link in linklist:
        ex_link.append({
            "link_id": link.link_id,
            "name": link.name,
            "href": link.href,
            "description": link.description,
            "create_time": int(link.create_time.strftime("%s")),
            "display": link.display,
        })

    # Backup all media
    ex_media = []
    for media in medialist:
        ex_media.append({
            "fileid": media.fileid,
            "filename": media.filename,
            "version": media.version,
            "content_type": media.content_type,
            "size": media.size,
            "create_time": int(media.create_time.strftime("%s")),
            "display": media.display
        })

    return json.dumps(
        {
            "links": ex_link,
            "posts": ex_post,
            "medias": ex_media
        },
        sort_keys=True,
        indent=4,
        separators=(',', ': '))
