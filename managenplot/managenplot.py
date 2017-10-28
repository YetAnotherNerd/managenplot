import logging
import re
import random
from datetime import datetime, timedelta, date
from flask import Flask, render_template, request, url_for
from calendar import Calendar
from werkzeug.utils import redirect

from managenplot.colorhash import ColorHash

app = Flask(__name__)
DATA_FILE = '/tmp/data.txt'
PATTERN = re.compile('from (\d+-\d+-\d+) to (\d+-\d+-\d+) (\w+) does (\w+).', re.I)


@app.route('/', defaults={'year': datetime.now().year, 'month': datetime.now().month})
@app.route('/<int:year>/', defaults={'month': None})
@app.route('/<int:year>/<int:month>/')
def managenplot(year, month):
    cal = Calendar(0).yeardatescalendar(year, 1)
    if month:
        cal = [cal[month - 1]]
    data = read_data()
    model = {prj: [(guy, ColorHash(guy).hex, days)
                   for guy, days in sorted(guys.items()) if days
                   and any(d.year == year and (not month or d.month == month)
                           for d in days)]
             for prj, guys in data.items()}
    sort = [(prj, guys) for prj, guys in sorted(model.items()) if guys]
    return render_template('managenplot.html', year=year, month=month,
                           now=datetime.now(), cal=cal, data=sort)


@app.route('/edit')
def edit():
    return render_template('edit.html', text=read_file())


@app.route('/save', methods=['POST'])
def save():
    with open(DATA_FILE, 'w') as file_:
        file_.write(request.form['text'])
    return redirect(url_for('managenplot'))


@app.route('/testdata')
def test_data():
    lines = []
    for i in range(100):
        guy = random.choice(['aa', 'bb', 'cc', 'dd', 'ee'])
        prj = random.choice(['prj1', 'prj2', 'prj3', 'urlaub'])
        year = datetime.now().year + random.randrange(2)
        month = random.randrange(1, 13)
        day = random.randrange(1, 29)
        start = date(year, month, day)
        end = start + timedelta(days=random.randrange(2, 14))
        lines.append('from ' + start.strftime('%Y-%m-%d') +
                     ' to ' + end.strftime('%Y-%m-%d') +
                     ' ' + guy + ' does ' + prj + '.\n')
    with open(DATA_FILE, 'a') as file_:
        file_.writelines(lines)
    return redirect(url_for('edit'))


def read_file(path=DATA_FILE):
    try:
        with open(path, 'r+') as file_:
            return file_.read()
    except FileNotFoundError:
        return None


def read_data():
    prjs = {}
    lines = read_file(DATA_FILE)
    if lines:
        lines = lines.splitlines()
    for line in lines or []:
        try:
            match = PATTERN.fullmatch(line)
            if not match:
                continue
            start, end, guy, prj = match.groups()
            start = datetime.strptime(start, '%Y-%m-%d')
            end = datetime.strptime(end, '%Y-%m-%d')
            days = [(start + timedelta(days=i)).date() for i in range((end - start).days + 1)]
            if prj not in prjs:
                prjs[prj] = {}
            if guy not in prjs[prj]:
                prjs[prj][guy] = set()
            prjs[prj][guy].update(days)
        except Exception as e:
            logging.error(e)
            continue
    return prjs
