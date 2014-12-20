#!/usr/bin/env python
# coding: utf-8
"""
    models.py
    ~~~~~~~~~~

"""
import os
import json
from flask.ext.sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):

    """setting = {
    page
    }
    """

    __tablename__ = "user"

    username = db.Column(db.String(20), primary_key=True)
    password = db.Column(db.String(256))
    salt = db.Column(db.String(20))
    config = db.Column(db.Text)

    @classmethod
    def get_config(cls):
        user = cls.query.first()
        if user is not None:
            return json.loads(user.config)
        else:
            return None


class Post(db.Model):
    __tablename__ = "post"
    post_id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(512),  primary_key=False)
    title = db.Column(db.String(512))
    # raw_content =content.strip_HTML_tags()
    raw_content = db.Column(db.Text)
    content = db.Column(db.Text)
    keywords = db.Column(db.String(256))
    metacontent = db.Column(db.String(256))
    create_time = db.Column(db.DateTime)
    update_time = db.Column(db.DateTime)
    # tag seperated by comma
    tags = db.Column(db.String(256))
    allow_visit = db.Column(db.Boolean)
    allow_comment = db.Column(db.Boolean)
    need_key = db.Column(db.Boolean)
    is_original = db.Column(db.Boolean)
    num_lookup = db.Column(db.Integer)

    def __init__(self):
        """setup default value
        """
        self.url = ""
        self.title = ""
        self.content = ""
        self.keywords = ""
        self.metacontent = ""
        self.tags = ""
        self.allow_visit = True
        self.allow_comment = True
        self.need_key = False
        self.is_original = True
        self.num_lookup = 0

    @classmethod
    def get_page(cls, offset, limit, public_only=True):
        """If pubic_only == False , return posts even if allow_visit = False
        """
        if public_only is True:
            return cls.query.filter_by(allow_visit=True).\
                order_by(cls.post_id.desc()).limit(limit).offset(offset).all()
        else:
            return cls.query.order_by(cls.post_id.desc()).\
                limit(limit).offset(offset).all()

    @classmethod
    def count(cls, public_only=True):
        if public_only is True:
            return cls.query.filter_by(allow_visit=True).count()
        else:
            return cls.query.count()

    @classmethod
    def get_by_id(cls, post_id, public_only=True):
        if public_only is True:
            return cls.query.filter_by(
                allow_visit=True, post_id=post_id).first()
        else:
            return cls.query.filter_by(
                post_id=post_id).first()

    @classmethod
    def get_by_url(cls, url, public_only=True):
        if public_only is True:
            return cls.query.filter_by(url=url, allow_visit=True).first()
        else:
            return cls.query.filter_by(url=url).first()

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
            query = query.filter(cls.raw_content.like("%"+word+"%"))
        return query.offset(offset).limit(limit).all()

    @classmethod
    def text_search_count(cls, words):
        if len(words) == 0 or len(words) > 5:
            return 0
        query = cls.query.filter_by(allow_visit=True)
        for word in words:
            query = query.filter(cls.raw_content.like("%"+word+"%"))
        return query.count()

    def get_tags(self):
        taglist = self.tags.split(",")
        taglist = [tag for tag in taglist if tag]
        return taglist

    def to_tags(self, taglist):
        tags = ",".join(taglist)
        return "," + tags + ","

    def update_tags(self, new_string):
        """ Post.tags is a string in which multi tags are seperatedi by ",", we
        will seperate them and save to database. Use this method when you want
        to update or create a post
        Input:
            "abc,abc, abc,123"
        Output:
            ",abc,123,"
            count for abc and 123 will increase by 1 ,We append comma before
            and after "abc,123", so we can do teh follwoing mysql search
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
        commentlist = Comment.get_by_post_id(self.post_id)
        for comment in commentlist:
            comment.delete()

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        self.delete_tags()
        self.delete_comments()
        db.session.delete(self)
        db.session.commit()


class Tag(db.Model):
    __tablename__ = "tag"

    name = db.Column(db.String(64), primary_key=True)
    count = db.Column(db.Integer)

    def __init__(self, name, count=1):
        self.name = name
        self.count = count

    @classmethod
    def get_one(cls, name):
        return cls.query.filter_by(name=name).first()

    @classmethod
    def add(cls, taglist):
        """never use this method directly , use Post.save_tags instead
        """
        for item in taglist:
            if item:
                tag = Tag.get_one(item)
                if tag:
                    tag.count += 1
                else:
                    tag = Tag(name=item)
                    db.session.add(tag)
        db.session.commit()

    @classmethod
    def minus(cls, taglist):
        for item in taglist:
            tag = Tag.get_one(item)
            if tag:
                if tag.count > 1:
                    tag.count -= 1
                else:
                    db.session.delete(tag)

        db.session.commit()

    @classmethod
    def get_first_X(cls, count):
        return cls.query.order_by(cls.count.desc()).limit(count).all()


class Comment(db.Model):
    comment_id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer)
    url = db.Column(db.String(64))
    email = db.Column(db.String(64))
    nickname = db.Column(db.String(20))
    content = db.Column(db.String(1024))
    refid = db.Column(db.Integer)
    to = db.Column(db.String(20))
    create_time = db.Column(db.DateTime)
    ip = db.Column(db.String(64))
    website = db.Column(db.String(64))

    @classmethod
    def get_by_post_id(cls, post_id):
        result = cls.query.filter_by(post_id=post_id).all()
        for i in range(len(result)):
            result[i].content = result[i].content.replace(" ", "&nbsp;")
            result[i].content = result[i].content.replace("\n", "<br>")
        return result

    @classmethod
    def get_by_id(cls, comment_id):
        return Comment.query.filter_by(comment_id=comment_id).first()

    @classmethod
    def get_by_url(cls, url):
        post = Post.get_by_url(url)
        if post:
            return cls.get_by_post_id(post.post_id)
        else:
            return None

    @classmethod
    def count(cls, post_id=None):
        if post_id is None:
            return cls.query.count()
        else:
            return cls.query(cls.post_id == post_id).count()

    @classmethod
    def get_last_X(cls, count):
        return cls.query.order_by(cls.comment_id.desc()).limit(count).all()

    @classmethod
    def get_page(cls, offset, limit, post_id=-1):
        if post_id == -1:
            commentlist = cls.query.order_by(cls.comment_id.desc()).\
                offset(offset).limit(limit).all()
        else:
            commentlist = cls.query.order_by(cls.comment_id.desc()).\
                filter_by(post_id=post_id).offset(offset).limit(limit).all()
        return commentlist

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()


class Link(db.Model):
    link_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20))
    href = db.Column(db.String(1024))
    description = db.Column(db.String(64))
    create_time = db.Column(db.DateTime)
    display = db.Column(db.Boolean)

    @classmethod
    def get_page(cls, offset, limit):
        return cls.query.offset(offset).limit(limit).all()

    @classmethod
    def get_X(cls, limit):
        return cls.query.filter_by(display=True).limit(limit).all()

    @classmethod
    def get_by_id(cls, link_id):
        return cls.query.filter_by(link_id=int(link_id)).first()

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()


class Media(db.Model):
    fileid = db.Column(db.String(64), primary_key=True)
    filename = db.Column(db.String(64))
    # For a give filename , there could be multi file exits
    version = db.Column(db.Integer)
    content_type = db.Column(db.String(32))
    size = db.Column(db.Integer)
    create_time = db.Column(db.DateTime)
    display = db.Column(db.Boolean)

    @classmethod
    def count(cls):
        return cls.query.count()

    @classmethod
    def get_page(cls, offset, limit):
        medialist = cls.query.order_by(cls.create_time.desc()).offset(offset).\
            limit(limit).all()
        return medialist

    @classmethod
    def get_by_id(cls, fileid):
        return cls.query.filter_by(fileid=fileid).first()

    @classmethod
    def get_file_count(cls, filename):
        return cls.query.filter_by(filename=filename).count()

    @classmethod
    def new_local_filename(cls, filename):
        """for given filename ,return a filename that can be saved to disk
            input: abc.jpg
            output:

        """
        version = cls.query.filter_by(filename=filename).count()
        return "f" + str(version) + filename

    def filepath(self, upload_folder):
        local_filename = "f" + str(self.version) + self.filename
        return os.path.join(upload_folder, local_filename)

    @property
    def local_filename(self):
        return "f"+str(self.version)+self.filename

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        import config
        filepath = self.filepath(config.UPLOAD_FOLDER)
        try:
            os.remove(filepath)
        except Exception:
            pass
        db.session.delete(self)
        db.session.commit()


def gen_sidebar(config):
    rr = {
        "taglist": None,
        "commentlist": None,
        "linklist": None
    }

    taglist = Tag.get_first_X(config["TAG_COUNT"])
    rr["taglist"] = taglist
    commentlist = Comment.get_last_X(config["COMMENT_COUNT"])
    rr["commentlist"] = commentlist
    linklist = Link.get_X(config["COMMENT_COUNT"])
    rr["linklist"] = linklist
    return rr
