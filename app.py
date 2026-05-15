from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3, os, hashlib
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = 'ai-solutions-secret-key-2024-sunderland-xK9mP2'

ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD_HASH = hashlib.sha256('AISolutions2024!'.encode()).hexdigest()
DATABASE = 'ai_solutions.db'


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS inquiries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL, email TEXT NOT NULL, phone TEXT NOT NULL,
        company TEXT NOT NULL, country TEXT NOT NULL,
        job_title TEXT NOT NULL, job_details TEXT NOT NULL,
        submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL, company TEXT NOT NULL, role TEXT NOT NULL,
        rating INTEGER NOT NULL, review TEXT NOT NULL, project TEXT,
        submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS portfolio (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL, industry TEXT NOT NULL, description TEXT NOT NULL,
        outcome TEXT, icon TEXT DEFAULT 'fa-chart-bar', featured INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL, location TEXT NOT NULL, event_date TEXT NOT NULL,
        description TEXT NOT NULL, icon TEXT DEFAULT 'fa-calendar',
        color TEXT DEFAULT 'primary',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    # Seed portfolio
    if c.execute('SELECT COUNT(*) FROM portfolio').fetchone()[0] == 0:
        c.executemany('INSERT INTO portfolio (title,industry,description,outcome,icon,featured) VALUES (?,?,?,?,?,?)', [
            ('NHS Trust Reduces IT Tickets by 68%','Healthcare',
             'A large NHS Trust deployed our Virtual Assistant integrated with ServiceNow and Teams. Within 90 days, 68% of tickets were resolved autonomously, freeing the IT team for critical work.',
             '68% ticket reduction · £240K annual savings · 90 days to deploy','fa-hospital',1),
            ('FinServe Global Launches 3 AI Prototypes in 6 Weeks','Financial Services',
             'FinServe needed to validate three AI-driven concepts before committing to full development. All three were delivered in 6 weeks with live user testing and stakeholder demos.',
             '3 prototypes built · 6-week delivery · 75% cost reduction','fa-building-columns',1),
            ('ManuAI Prevents £1.2M in Downtime','Manufacturing',
             'A Sunderland-based manufacturer deployed our DEX Analytics Platform integrated with their SCADA system. Predictive alerting flagged 23 critical incidents before they caused line stoppages.',
             '£1.2M downtime prevented · 23 incidents flagged · 99.7% uptime','fa-industry',1),
        ])
    # Seed events
    if c.execute('SELECT COUNT(*) FROM events').fetchone()[0] == 0:
        c.executemany('INSERT INTO events (title,location,event_date,description,icon,color) VALUES (?,?,?,?,?,?)', [
            ('AI-Solutions Product Showcase','Sunderland Software Centre','2024-06-15',
             'Exclusive preview of our next-gen Virtual Assistant and DEX Analytics Platform. Live demos, Q&A, and networking dinner.','fa-rocket','primary'),
            ('DEX Summit 2024','ExCeL London','2024-07-22',
             'Our CEO delivers the opening keynote on "The AI-Powered Workforce of 2030" at the UK\'s largest DEX conference.','fa-microphone','warning'),
            ('Global Partner Forum','Sunderland & Virtual','2024-09-10',
             'Invite-only forum for partners to explore joint go-to-market opportunities and co-innovation programmes.','fa-globe','secondary'),
        ])
    conn.commit()
    conn.close()


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'admin_logged_in' not in session:
            flash('Please log in to access the admin area.', 'error')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated


# ── PUBLIC ROUTES ────────────────────────────
@app.route('/')
def index():
    conn = get_db()
    highlights = conn.execute(
        'SELECT * FROM feedback WHERE rating >= 4 ORDER BY submitted_at DESC LIMIT 3').fetchall()
    conn.close()
    return render_template('index.html', highlights=highlights)

@app.route('/solutions')
def solutions():
    return render_template('solutions.html')

@app.route('/portfolio')
def portfolio():
    conn = get_db()
    items = conn.execute('SELECT * FROM portfolio ORDER BY featured DESC, created_at DESC').fetchall()
    conn.close()
    return render_template('portfolio.html', items=items)

@app.route('/case-studies')
def case_studies():
    return redirect(url_for('portfolio'))

@app.route('/articles')
def articles():
    return render_template('articles.html')

@app.route('/gallery')
def gallery():
    conn = get_db()
    events = conn.execute('SELECT * FROM events ORDER BY event_date ASC').fetchall()
    conn.close()
    return render_template('gallery.html', events=events)

@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    conn = get_db()
    if request.method == 'POST':
        name    = request.form.get('name', '').strip()
        company = request.form.get('company', '').strip()
        role    = request.form.get('role', '').strip()
        rating  = request.form.get('rating', '5').strip()
        review  = request.form.get('review', '').strip()
        project = request.form.get('project', '').strip()
        if not all([name, company, role, review]):
            flash('Please fill in all required fields.', 'error')
            conn.close()
            return redirect(url_for('feedback'))
        try:
            rating_int = max(1, min(5, int(rating)))
        except (ValueError, TypeError):
            rating_int = 5
        conn.execute(
            'INSERT INTO feedback (name,company,role,rating,review,project) VALUES (?,?,?,?,?,?)',
            (name, company, role, rating_int, review, project))
        conn.commit()
        flash('Thank you! Your review has been published.', 'success')
        conn.close()
        return redirect(url_for('feedback'))
    feedbacks = conn.execute('SELECT * FROM feedback ORDER BY submitted_at DESC').fetchall()
    total = len(feedbacks)
    avg   = round(sum(f['rating'] for f in feedbacks) / total, 1) if total else 0
    conn.close()
    return render_template('feedback.html', feedbacks=feedbacks, total_reviews=total, avg_rating=avg)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        fields = ['name','email','phone','company','country','job_title','job_details']
        data = {f: request.form.get(f,'').strip() for f in fields}
        if not all(data.values()):
            flash('All fields are required.', 'error')
            return render_template('contact.html', form_data=request.form)
        conn = get_db()
        conn.execute(
            'INSERT INTO inquiries (name,email,phone,company,country,job_title,job_details) VALUES (?,?,?,?,?,?,?)',
            tuple(data.values()))
        conn.commit()
        conn.close()
        flash('Enquiry received! We will be in touch within 1 business day.', 'success')
        return redirect(url_for('contact'))
    return render_template('contact.html', form_data={})


#ADMIN ROUTES 
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if 'admin_logged_in' in session:
        return redirect(url_for('admin_dashboard'))
    if request.method == 'POST':
        username = request.form.get('username','').strip()
        password = request.form.get('password','')
        if username == ADMIN_USERNAME and hashlib.sha256(password.encode()).hexdigest() == ADMIN_PASSWORD_HASH:
            session['admin_logged_in'] = True
            flash('Welcome back, Administrator!', 'success')
            return redirect(url_for('admin_dashboard'))
        flash('Invalid credentials.', 'error')
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('admin_login'))

@app.route('/admin')
@login_required
def admin_dashboard():
    conn = get_db()
    inquiries = conn.execute('SELECT * FROM inquiries ORDER BY submitted_at DESC').fetchall()
    total     = conn.execute('SELECT COUNT(*) FROM inquiries').fetchone()[0]
    today     = datetime.now().strftime('%Y-%m-%d')
    today_count = conn.execute(
        "SELECT COUNT(*) FROM inquiries WHERE DATE(submitted_at)=?", (today,)).fetchone()[0]
    by_country = conn.execute(
        'SELECT country,COUNT(*) as count FROM inquiries GROUP BY country ORDER BY count DESC LIMIT 8').fetchall()
    by_job = conn.execute(
        'SELECT job_title,COUNT(*) as count FROM inquiries GROUP BY job_title ORDER BY count DESC LIMIT 6').fetchall()
    monthly = conn.execute(
        "SELECT strftime('%Y-%m',submitted_at) as month,COUNT(*) as count FROM inquiries GROUP BY month ORDER BY month DESC LIMIT 6").fetchall()
    feedbacks = conn.execute('SELECT * FROM feedback ORDER BY submitted_at DESC').fetchall()
    fb_count  = len(feedbacks)
    avg_rating = round(sum(f['rating'] for f in feedbacks)/fb_count,1) if fb_count else 0
    conn.close()
    return render_template('admin_dashboard.html',
        inquiries=inquiries, total=total, today_count=today_count,
        by_country=by_country, by_job=by_job, monthly=monthly,
        feedbacks=feedbacks, feedback_count=fb_count, avg_rating=avg_rating)

@app.route('/admin/inquiry/<int:iid>')
@login_required
def admin_inquiry_detail(iid):
    conn = get_db()
    inquiry = conn.execute('SELECT * FROM inquiries WHERE id=?', (iid,)).fetchone()
    conn.close()
    if not inquiry:
        flash('Enquiry not found.', 'error')
        return redirect(url_for('admin_dashboard'))
    return render_template('admin_inquiry_detail.html', inquiry=inquiry)

@app.route('/admin/delete/<int:iid>', methods=['POST'])
@login_required
def admin_delete_inquiry(iid):
    conn = get_db()
    conn.execute('DELETE FROM inquiries WHERE id=?', (iid,))
    conn.commit(); conn.close()
    flash('Enquiry deleted.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/feedback/delete/<int:fid>', methods=['POST'])
@login_required
def admin_delete_feedback(fid):
    conn = get_db()
    conn.execute('DELETE FROM feedback WHERE id=?', (fid,))
    conn.commit(); conn.close()
    flash('Review removed.', 'success')
    return redirect(url_for('admin_dashboard'))

# Portfolio CRUD
@app.route('/admin/portfolio')
@login_required
def admin_portfolio():
    conn = get_db()
    items = conn.execute('SELECT * FROM portfolio ORDER BY featured DESC,created_at DESC').fetchall()
    conn.close()
    return render_template('admin_portfolio.html', items=items)

@app.route('/admin/portfolio/add', methods=['GET','POST'])
@login_required
def admin_portfolio_add():
    if request.method == 'POST':
        title=request.form.get('title','').strip()
        industry=request.form.get('industry','').strip()
        desc=request.form.get('description','').strip()
        outcome=request.form.get('outcome','').strip()
        icon=request.form.get('icon','fa-chart-bar').strip()
        featured=1 if request.form.get('featured') else 0
        if not all([title,industry,desc]):
            flash('Title, industry and description are required.','error')
            return redirect(url_for('admin_portfolio_add'))
        conn=get_db()
        conn.execute('INSERT INTO portfolio (title,industry,description,outcome,icon,featured) VALUES (?,?,?,?,?,?)',
                     (title,industry,desc,outcome,icon,featured))
        conn.commit(); conn.close()
        flash('Portfolio item added.','success')
        return redirect(url_for('admin_portfolio'))
    return render_template('admin_portfolio_form.html', item=None, action='Add')

@app.route('/admin/portfolio/edit/<int:pid>', methods=['GET','POST'])
@login_required
def admin_portfolio_edit(pid):
    conn=get_db()
    item=conn.execute('SELECT * FROM portfolio WHERE id=?',(pid,)).fetchone()
    if not item:
        conn.close(); flash('Not found.','error')
        return redirect(url_for('admin_portfolio'))
    if request.method == 'POST':
        title=request.form.get('title','').strip()
        industry=request.form.get('industry','').strip()
        desc=request.form.get('description','').strip()
        outcome=request.form.get('outcome','').strip()
        icon=request.form.get('icon','fa-chart-bar').strip()
        featured=1 if request.form.get('featured') else 0
        conn.execute('UPDATE portfolio SET title=?,industry=?,description=?,outcome=?,icon=?,featured=? WHERE id=?',
                     (title,industry,desc,outcome,icon,featured,pid))
        conn.commit(); conn.close()
        flash('Portfolio item updated.','success')
        return redirect(url_for('admin_portfolio'))
    conn.close()
    return render_template('admin_portfolio_form.html', item=item, action='Edit')

@app.route('/admin/portfolio/delete/<int:pid>', methods=['POST'])
@login_required
def admin_portfolio_delete(pid):
    conn=get_db()
    conn.execute('DELETE FROM portfolio WHERE id=?',(pid,))
    conn.commit(); conn.close()
    flash('Portfolio item deleted.','success')
    return redirect(url_for('admin_portfolio'))

# Events CRUD
@app.route('/admin/events')
@login_required
def admin_events():
    conn=get_db()
    events=conn.execute('SELECT * FROM events ORDER BY event_date ASC').fetchall()
    conn.close()
    return render_template('admin_events.html', events=events)

@app.route('/admin/events/add', methods=['GET','POST'])
@login_required
def admin_events_add():
    if request.method == 'POST':
        title=request.form.get('title','').strip()
        location=request.form.get('location','').strip()
        event_date=request.form.get('event_date','').strip()
        desc=request.form.get('description','').strip()
        icon=request.form.get('icon','fa-calendar').strip()
        color=request.form.get('color','primary').strip()
        if not all([title,location,event_date,desc]):
            flash('All fields required.','error')
            return redirect(url_for('admin_events_add'))
        conn=get_db()
        conn.execute('INSERT INTO events (title,location,event_date,description,icon,color) VALUES (?,?,?,?,?,?)',
                     (title,location,event_date,desc,icon,color))
        conn.commit(); conn.close()
        flash('Event added.','success')
        return redirect(url_for('admin_events'))
    return render_template('admin_events_form.html', event=None, action='Add')

@app.route('/admin/events/edit/<int:eid>', methods=['GET','POST'])
@login_required
def admin_events_edit(eid):
    conn=get_db()
    event=conn.execute('SELECT * FROM events WHERE id=?',(eid,)).fetchone()
    if not event:
        conn.close(); flash('Not found.','error')
        return redirect(url_for('admin_events'))
    if request.method == 'POST':
        title=request.form.get('title','').strip()
        location=request.form.get('location','').strip()
        event_date=request.form.get('event_date','').strip()
        desc=request.form.get('description','').strip()
        icon=request.form.get('icon','fa-calendar').strip()
        color=request.form.get('color','primary').strip()
        conn.execute('UPDATE events SET title=?,location=?,event_date=?,description=?,icon=?,color=? WHERE id=?',
                     (title,location,event_date,desc,icon,color,eid))
        conn.commit(); conn.close()
        flash('Event updated.','success')
        return redirect(url_for('admin_events'))
    conn.close()
    return render_template('admin_events_form.html', event=event, action='Edit')

@app.route('/admin/events/delete/<int:eid>', methods=['POST'])
@login_required
def admin_events_delete(eid):
    conn=get_db()
    conn.execute('DELETE FROM events WHERE id=?',(eid,))
    conn.commit(); conn.close()
    flash('Event deleted.','success')
    return redirect(url_for('admin_events'))

# Analytics API for Chart.js
@app.route('/admin/api/analytics')
@login_required
def admin_api_analytics():
    conn=get_db()
    by_country=conn.execute(
        'SELECT country,COUNT(*) as count FROM inquiries GROUP BY country ORDER BY count DESC LIMIT 8').fetchall()
    monthly=conn.execute(
        "SELECT strftime('%Y-%m',submitted_at) as month,COUNT(*) as count FROM inquiries GROUP BY month ORDER BY month ASC LIMIT 6").fetchall()
    by_job=conn.execute(
        'SELECT job_title,COUNT(*) as count FROM inquiries GROUP BY job_title ORDER BY count DESC LIMIT 6').fetchall()
    conn.close()
    return jsonify({
        'countries':{'labels':[r['country'] for r in by_country],'data':[r['count'] for r in by_country]},
        'monthly':  {'labels':[r['month']   for r in monthly],   'data':[r['count'] for r in monthly]},
        'jobs':     {'labels':[r['job_title'] for r in by_job],  'data':[r['count'] for r in by_job]},
    })

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5001)
