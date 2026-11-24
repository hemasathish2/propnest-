import os
import sqlite3
from datetime import datetime
from flask import Flask, flash, redirect, render_template, request, url_for, jsonify

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'demo-only-change-in-production')
app.config['DATABASE'] = os.environ.get('DATABASE', os.path.join(os.path.dirname(__file__), 'propnest.db'))

CITIES = {'Bengaluru': 7500, 'Mysuru': 4200, 'Chennai': 6500, 'Hyderabad': 6200, 'Pune': 6800}
TYPES = {'Apartment': 1.0, 'Villa': 1.5, 'Independent House': 1.2}

def db():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with db() as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS properties (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, city TEXT NOT NULL, locality TEXT NOT NULL, property_type TEXT NOT NULL, area REAL NOT NULL, bedrooms INTEGER NOT NULL, price REAL NOT NULL, description TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL)''')
        conn.execute('''CREATE TABLE IF NOT EXISTS enquiries (id INTEGER PRIMARY KEY AUTOINCREMENT, property_id INTEGER NOT NULL, name TEXT NOT NULL, email TEXT NOT NULL, message TEXT NOT NULL, FOREIGN KEY(property_id) REFERENCES properties(id))''')

def estimate_price(city, property_type, area, bedrooms, age=0):
    if city not in CITIES or property_type not in TYPES:
        raise ValueError('Choose a valid city and property type.')
    try:
        area, bedrooms, age = float(area), int(bedrooms), int(age)
    except (ValueError, TypeError):
        raise ValueError('Enter valid numeric values.') from None
    if not 100 <= area <= 20000 or not 1 <= bedrooms <= 12 or not 0 <= age <= 100:
        raise ValueError('Area, bedrooms or age is out of range.')
    return round(area * CITIES[city] * TYPES[property_type] * (1 + .025 * (bedrooms - 1)) * max(.65, 1 - .008 * age))

def parse_property(form):
    title = form.get('title', '').strip()
    city = form.get('city', '')
    locality = form.get('locality', '').strip()
    kind = form.get('property_type', '')
    desc = form.get('description', '').strip()
    if not title or not locality or city not in CITIES or kind not in TYPES:
        raise ValueError('Enter a title, locality, valid city and property type.')
    try:
        area, bedrooms, price = float(form.get('area', '')), int(form.get('bedrooms', '')), float(form.get('price', ''))
    except (TypeError, ValueError):
        raise ValueError('Enter valid numeric property values.') from None
    if not 100 <= area <= 20000 or not 1 <= bedrooms <= 12 or not 100000 <= price <= 1000000000:
        raise ValueError('Area, bedrooms or price is out of range.')
    return title, city, locality, kind, area, bedrooms, price, desc

@app.route('/')
def home():
    with db() as conn:
        count = conn.execute('SELECT COUNT(*) FROM properties').fetchone()[0]
        latest = conn.execute('SELECT * FROM properties ORDER BY id DESC LIMIT 3').fetchall()
    return render_template('index.html', count=count, latest=latest)

@app.route('/properties')
def properties():
    city = request.args.get('city', '')
    kind = request.args.get('property_type', '')
    search = request.args.get('q', '').strip()
    query, args = 'SELECT * FROM properties WHERE 1=1', []
    if city:
        query += ' AND city=?'; args.append(city)
    if kind:
        query += ' AND property_type=?'; args.append(kind)
    if search:
        query += ' AND (title LIKE ? OR locality LIKE ?)'; args.extend([f'%{search}%', f'%{search}%'])
    query += ' ORDER BY id DESC'
    with db() as conn:
        rows = conn.execute(query, args).fetchall()
    return render_template('properties.html', properties=rows, cities=CITIES, types=TYPES, city=city, kind=kind, q=search)

@app.route('/properties/new', methods=['GET', 'POST'])
def add_property():
    if request.method == 'POST':
        try:
            values = parse_property(request.form)
            with db() as conn:
                conn.execute('INSERT INTO properties (title,city,locality,property_type,area,bedrooms,price,description,created_at) VALUES (?,?,?,?,?,?,?,?,?)', (*values, datetime.now().isoformat(timespec='seconds')))
            flash('Property listed successfully!', 'success')
            return redirect(url_for('properties'))
        except ValueError as exc:
            flash(str(exc), 'error')
    return render_template('add.html', cities=CITIES, types=TYPES)

@app.route('/properties/<int:property_id>')
def property_detail(property_id):
    with db() as conn:
        prop = conn.execute('SELECT * FROM properties WHERE id=?', (property_id,)).fetchone()
    if not prop:
        return render_template('404.html'), 404
    return render_template('detail.html', prop=prop)

@app.route('/properties/<int:property_id>/enquire', methods=['POST'])
def enquire(property_id):
    with db() as conn:
        prop = conn.execute('SELECT id FROM properties WHERE id=?', (property_id,)).fetchone()
        if not prop:
            return render_template('404.html'), 404
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        message = request.form.get('message', '').strip()
        if not name or '@' not in email or '.' not in email.split('@')[-1] or not message:
            flash('Enter a valid name, email and message.', 'error')
        else:
            conn.execute('INSERT INTO enquiries(property_id,name,email,message) VALUES (?,?,?,?)', (property_id, name, email, message))
            flash('Enquiry saved locally (no email sent).', 'success')
    return redirect(url_for('property_detail', property_id=property_id))

@app.route('/estimate', methods=['GET', 'POST'])
def estimate():
    result, error = None, None
    if request.method == 'POST':
        try:
            result = estimate_price(request.form.get('city'), request.form.get('property_type'), request.form.get('area'), request.form.get('bedrooms'), request.form.get('age', 0))
        except ValueError as exc:
            error = str(exc)
    return render_template('estimate.html', cities=CITIES, types=TYPES, result=result, error=error)

@app.route('/dashboard')
def dashboard():
    with db() as conn:
        count = conn.execute('SELECT COUNT(*) FROM properties').fetchone()[0]
        enquiries = conn.execute('SELECT COUNT(*) FROM enquiries').fetchone()[0]
        average = conn.execute('SELECT AVG(price) FROM properties').fetchone()[0] or 0
        by_city = conn.execute('SELECT city,COUNT(*) AS count FROM properties GROUP BY city ORDER BY count DESC').fetchall()
    return render_template('dashboard.html', count=count, enquiries=enquiries, average=average, by_city=by_city)

@app.route('/api/health')
def health():
    with db() as conn:
        conn.execute('SELECT 1')
    return jsonify(status='ok', service='PropNest')

@app.route('/api/metrics')
def metrics():
    with db() as conn:
        return jsonify(properties=conn.execute('SELECT COUNT(*) FROM properties').fetchone()[0], enquiries=conn.execute('SELECT COUNT(*) FROM enquiries').fetchone()[0])

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
