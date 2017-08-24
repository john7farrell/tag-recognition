#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import cv2
import sqlite3
from collections import OrderedDict
from flask import Flask, request, session, g, \
    redirect, url_for, render_template, flash
from flask_uploads import UploadSet, configure_uploads, \
    IMAGES, patch_request_class
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import SubmitField, SelectField, validators
from flaskr.tag_recognition.preprocess \
    import getResizedImage, getEnhancedImage, getDeskewedImage
from flaskr.tag_recognition.json_analyze import json_result
from flaskr.tag_recognition.gcv_api import gcv_result
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config.from_object(__name__)

app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'flaskr.db'),
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='admin'
))
app.config.from_envvar('FLASKR_SETTINGS', silent=True)


def connect_db():
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv


def get_db():
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db


@app.teardown_appcontext
def close_db(error=''):
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()
    else:
        print(error)


def init_db():
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as file_opened:
        db.cursor().executescript(file_opened.read())
    db.commit()


@app.cli.command('initdb')
def initdb_command():
    init_db()
    print('Initialized the database.')


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            error = 'Invalid username'
        elif request.form['password'] != app.config['PASSWORD']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            flash('You were logged in')
            return redirect(url_for('upload_file'))
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('login'))


app.config['UPLOADED_PHOTOS_DEST'] = os.getcwd() + '/upload'
with open('.apikey', 'r') as f:
    app.config['API_KEY'] = f.read()
photos = UploadSet('photos', IMAGES)
configure_uploads(app, photos)
patch_request_class(app)  # set maximum file size, default is 16MB
id_rule_dict = OrderedDict()
id_rule_dict['Unknown13'] = [13]
id_rule_dict['BEAMS'] = [2, 2, 4, 3, 2, 2]
id_rule_dict['OWD'] = [12]
id_rule_dict['SHIPS'] = [3, 2, 4, 4]
id_rule_dict['TML'] = [2, 2, 2, 7]
id_rule_dict['UA'] = [4, 3, 4, 4]
id_rule_dict['Sanyo'] = [5, 3, 2]
id_rule_dict['alcali'] = [11]
id_rule_dict['CONVERSE TOKYO'] = [11]
id_rule_dict['Liess'] = [11]
id_rule_dict['martinique'] = [11]
id_rule_dict['MENS MELROSE'] = [10]
id_rule_dict['Soffitto'] = [10]


def get_id_rule_choice(k):
    v = id_rule_dict[k]
    return k + ': ' + '-'.join(['X' * vi for vi in v])


class UploadForm(FlaskForm):
    photo = FileField(validators=[
        FileAllowed(photos, 'Only pictures are allowed'),
        FileRequired('Please select file！')])
    submit = SubmitField('Upload')
    select = SelectField(
        'ID Rule:',
        choices=[
            (0, get_id_rule_choice('Unknown13')),
            (1, get_id_rule_choice('BEAMS')),
            (2, get_id_rule_choice('OWD')),
            (3, get_id_rule_choice('SHIPS')),
            (4, get_id_rule_choice('TML')),
            (5, get_id_rule_choice('UA')),
            (6, get_id_rule_choice('Sanyo')),
            (7, get_id_rule_choice('alcali')),
            (8, get_id_rule_choice('CONVERSE TOKYO')),
            (9, get_id_rule_choice('Liess')),
            (10, get_id_rule_choice('martinique')),
            (11, get_id_rule_choice('MENS MELROSE')),
            (12, get_id_rule_choice('Soffitto'))
        ],
        default=5,
        validators=[validators.optional()],
        coerce=int
    )


def replace_into_db(res, file_name, fullname):
    columns = ['title', 'ProductId', 'Origin',
               'Part', 'Material', 'Percent',
               'Filename', 'FullText']
    query_executed = 'replace into entries (' + \
                     ','.join(columns) + \
                     ') values (?, ?, ?, ?, ?, ?, ?, ?)'
    db = get_db()
    db.execute(query_executed,
               [file_name] + [res['ID'][1],
                              ', '.join(res['Origin']),
                              ', '.join(res['Part']),
                              ', '.join(res['Material']),
                              ', '.join(res['Percent']),
                              fullname,
                              res['FullText']])
    db.commit()


def get_entries(fullname):
    db = get_db()
    fetch_query = "select * from entries where title='" + \
                  fullname.split('.')[0] + "';"
    cur = db.execute(fetch_query)
    entries = cur.fetchall()
    db.commit()
    return entries


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    form = UploadForm()
    entries = []
    if form.validate_on_submit():
        # check if already existed
        file_dir = app.config['UPLOADED_PHOTOS_DEST']
        file_list = os.listdir(file_dir)
        fullname = secure_filename(form.photo.data.filename)
        if fullname not in file_list:
            fullname = photos.save(form.photo.data)
        # get preprocessed image
        file_name, file_ext = os.path.splitext(fullname)
        image_proc = getEnhancedImage(file_dir + '/' + file_name + file_ext)
        image_proc = getDeskewedImage('', image_proc)
        image_proc = getResizedImage('', image_proc,
                                     maxHeight=900)
        cv2.imwrite(file_dir + '/' + file_name + '_proc' + file_ext,
                    image_proc)
        del image_proc
        # get file_name, file_extension, json_file_name
        fname_proc = file_name + '_proc'
        fname_json = fname_proc + file_ext + '.json'
        # if json file is not existed, get json by google vision api
        if fname_json not in os.listdir(file_dir):
            gcv_result(file_dir + '/' + fname_proc + file_ext,
                       api_key=app.config['API_KEY'])
        # get json analysis result with selected id-rule
        id_rule = id_rule_dict[list(id_rule_dict.keys())[int(form.select.data)]]
        res = json_result(fname_json, id_rule)
        # insert(replace) the result into database
        replace_into_db(res, file_name, fullname)
        entries = get_entries(fullname)
        # form photo's url to preview
        file_url = photos.url(fullname)
        file_proc_url = photos.url(fname_proc + file_ext)
    else:
        file_url = None
        file_proc_url = None
    return render_template('upload.html',
                           form=form,
                           file_url=file_url,
                           file_proc_url=file_proc_url,
                           entries=entries)