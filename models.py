#!/usr/bin/env python
# coding: utf-8
"""
    models.py
    ~~~~~~~~~~

"""
import os
import re
import time
import hashlib
import markdown2
from datetime import datetime

from flask import current_app
import peewee
from peewee import fn
from playhouse.kv import JSONField

import config
from helpers import get_or_none
from signals import signal_update_sidebar


db = peewee.SqliteDatabase('tyou.db')


class ModelMixin():
    @classmethod
    @get_or_none
    def get_one(cls, *args):
        return cls.select().where(*args).get() if args else cls.get()

    @classmethod
    def get_list(cls, *args):
        return cls.select().where(*args) if args else cls.select()

    @classmethod
    def get_page(cls, page, *args, **kwargs):
        """
        get paginated records
        eg:
            Model.get_page(page=1, order_by=Model.id, limit=12)
        """
        limit = kwargs.get("limit", 0) or config.PER_PAGE
        parameters = kwargs.get("parameters", {})

        # convert parmeters to peewee language
        additional_args = []
        for key, value in parameters.items():
            additional_args.append(getattr(cls, key) == value)

        query = cls.get_list(*args, *additional_args)
        if "order_by" in kwargs:
            query = query.order_by(kwargs["order_by"])

        count = query.count()
        items = query.paginate(page, limit)
        return count, items


class User(peewee.Model, ModelMixin):
    """setting = {
    page
    }
    """
    id = peewee.PrimaryKeyField()
    username = peewee.CharField(max_length=20, index=True)
    password = peewee.CharField(max_length=256)
    salt = peewee.CharField(max_length=20)
    config = JSONField()
    created_at = peewee.DateTimeField(default=datetime.utcnow)

    class Meta:
        database = db
        db_table = "user"

    @classmethod
    def get_config(cls):
        user = cls.select().first()
        return user.config if user and user.config else None

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
        users = cls.get_list(User.username == username)
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
        user = cls.get_one(User.username == username)
        user.delete_instance()

    @classmethod
    def get_sidebar(cls):
        """
        generate sidebar if it does not exist or it has expired
        """
        if not hasattr(cls, "sidebar"):
            cls.generate_sidebar()
        sidebar = getattr(cls, "sidebar")
        if sidebar["expired_at"] <= time.time():
            sidebar = cls.generate_sidebar()
        return sidebar["data"]

    @classmethod
    def update_sidebar(cls, *args, **kwargs):
        """
        subscribe to a signal and update sidebar when needed
        """
        cls.generate_sidebar()

    @classmethod
    def generate_sidebar(cls):
        """
        User.sidebar = {
            "exipred_at": timestamp,
            "data": {}
        }
        """
        config = cls.get_config() or current_app.config

        rr = {
            "tags": None,
            "comments": None,
            "links": None,
            "announce": None,
            "announce_length": 0
        }

        tags = Tag.select(
            Tag.name, fn.COUNT(Tag.name).alias("count")
        ).group_by(Tag.name).order_by(-fn.COUNT(Tag.name)).limit(config["TAG_COUNT"])
        rr["tags"] = tags

        comments = Comment.get_list().\
            order_by(Comment.id.desc()).limit(config["COMMENT_COUNT"])
        rr["comments"] = comments

        links = Link.get_list(
            Link.display == True
        ).order_by(Link.id.desc()).limit(config["LINK_COUNT"])
        rr["links"] = links

        announce = Post.get_one(Post.id == config["ANNOUNCE_ID"])
        rr["announce"] = announce
        rr["announce_length"] = config["ANNOUNCE_LENGTH"]

        cls.sidebar = {
            "data": rr,
            "expired_at": time.time() + 8 * 60 * 60
        }
        return cls.sidebar


class Post(peewee.Model, ModelMixin):
    id = peewee.PrimaryKeyField()
    url = peewee.CharField(max_length=256, unique=True)
    title = peewee.CharField(max_length=256)
    raw_content = peewee.TextField()
    content = peewee.TextField()
    keywords = peewee.CharField(max_length=256, default="")
    metacontent = peewee.CharField(max_length=256, default="")
    create_time = peewee.DateTimeField(default=datetime.now)
    update_time = peewee.DateTimeField(default=datetime.now)
    # required if need_key is True
    password = peewee.CharField(max_length=20, default="")
    # tag seperated by comma
    tags = peewee.CharField(max_length=256, default="")
    # editor html or markdown
    editor = peewee.CharField(max_length=10, choices=("html", "markdown"))
    allow_visit = peewee.BooleanField(default=False)
    allow_comment = peewee.BooleanField(default=True)
    need_key = peewee.BooleanField(default=False)
    is_original = peewee.BooleanField(default=True)
    num_lookup = peewee.IntegerField(default=0)

    class Meta:
        database = db
        db_table = "post"

    @classmethod
    def tag_search(cls, keyword, offset, limit):
        if not keyword:
            return []
        query = cls.select().join(Tag).where(
            Post.allow_visit == True, Tag.name == keyword
        ).order_by(-Post.id)
        return query.count(), query.offset(offset).limit(limit)

    @classmethod
    def text_search(cls, words, offset, limit):
        if len(words) == 0 or len(words) > 5:
            return []

        query = cls.select().where(Post.allow_visit == True)
        for word in words:
            query = query.where(
                cls.raw_content.contains(word) |
                cls.title.contains(word)
            )
        query = query.order_by(-cls.id)
        return query.count(), query.offset(offset).limit(limit)

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

    def get_tags(self):
        tags = self.tags.split(",")
        tags = [tag for tag in tags if tag]
        return tags

    def to_tags(self, tagnames):
        tagnames = set([i.strip() for i in tagnames])
        tagnames = ",".join(tagnames)
        return "," + tagnames + ","

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
        if self.tags == new_string:
            return

        #  delete old tags
        Tag.delete().where(Tag.post == self).execute()

        # create new tags one by one
        tagnames = new_string.split(",")
        tagnames = [i.strip() for i in tagnames if i]
        for tagname in tagnames:
            Tag.get_or_create_tag(self, tagname)

        self.tags = new_string
        self.save()


class Tag(peewee.Model, ModelMixin):

    id = peewee.PrimaryKeyField()
    name = peewee.CharField(max_length=64)
    post = peewee.ForeignKeyField(Post, related_name="sub_tags")

    class Meta:
        database = db
        db_table = "tag"

        indexes = (
            (("name", "post"), True)
        )

    @classmethod
    def get_or_create_tag(cls, post, tagname):
        if not tagname:
            return
        return Tag.get_or_create(post=post, name=tagname)


class Comment(peewee.Model, ModelMixin):
    id = peewee.PrimaryKeyField()
    post = peewee.ForeignKeyField(Post, related_name="comments")
    email = peewee.CharField(max_length=64)
    nickname = peewee.CharField(max_length=20)
    content = peewee.CharField(max_length=1024)
    parent_comment = peewee.ForeignKeyField('self', null=True, related_name="sub_comments")
    to = peewee.CharField(max_length=20)
    create_time = peewee.DateTimeField(default=datetime.now)
    ip = peewee.CharField(max_length=64)
    website = peewee.CharField(max_length=64)

    class Meta:
        database = db
        db_table = "comment"


class Link(peewee.Model, ModelMixin):

    id = peewee.PrimaryKeyField()
    name = peewee.CharField(max_length=64)
    href = peewee.CharField(max_length=1024)
    description = peewee.CharField(max_length=64)
    create_time = peewee.DateTimeField(default=datetime.utcnow)
    display = peewee.BooleanField()

    class Meta:
        database = db
        db_table = "link"


class Media(peewee.Model, ModelMixin):
    id = peewee.PrimaryKeyField()
    fileid = peewee.CharField(max_length=64, unique=True)
    filename = peewee.CharField(max_length=64)
    # For a give filename , there could be multi file exits
    version = peewee.IntegerField(default=0)
    content_type = peewee.CharField(max_length=32)
    size = peewee.IntegerField()
    create_time = peewee.DateTimeField()
    display = peewee.BooleanField(default=True)

    class Meta:
        database = db
        db_table = "media"

    def filepath(self, upload_folder):
        return os.path.join(upload_folder, self.local_filename)

    @property
    def local_filename(self):
        return self.filename


signal_update_sidebar.connect(User.update_sidebar)
