from flask import Flask, render_template, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import csv
import io
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'pontora-waitlist-2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///waitlist.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class WaitlistEntry(db.Model):
    __tablename__ = 'waitlist_entry'
    id         = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(80), nullable=False)
    last_name  = db.Column(db.String(80), nullable=False)
    email      = db.Column(db.String(120), unique=True, nullable=False)
    phone      = db.Column(db.String(20), nullable=False)
    signed_up  = db.Column(db.DateTime, default=datetime.utcnow)


@app.route('/')
def index():
    return render_template('waitlist.html')


@app.route('/waitlist/signup', methods=['POST'])
def waitlist_signup():
    data = request.get_json()

    first_name = (data.get('first_name') or '').strip()
    last_name  = (data.get('last_name')  or '').strip()
    email      = (data.get('email')      or '').strip().lower()
    phone      = (data.get('phone')      or '').strip()

    if not all([first_name, last_name, email, phone]):
        return jsonify({'error': 'All fields required'}), 400

    if WaitlistEntry.query.filter_by(email=email).first():
        return jsonify({'message': 'Already registered'}), 200

    entry = WaitlistEntry(
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone=phone
    )
    db.session.add(entry)
    db.session.commit()

    return jsonify({'message': 'Success'}), 200


@app.route('/admin')
def admin():
    entries = WaitlistEntry.query.order_by(WaitlistEntry.signed_up.desc()).all()
    count = len(entries)

    rows = ''.join(
        f"""<tr>
              <td>{e.id}</td>
              <td>{e.first_name} {e.last_name}</td>
              <td>{e.email}</td>
              <td>{e.phone}</td>
              <td>{e.signed_up.strftime('%d %b %Y %H:%M')}</td>
            </tr>"""
        for e in entries
    )

    html = f"""<!DOCTYPE html>
<html><head>
  <title>Pontora Waitlist — {count} signups</title>
  <style>
    body {{ font-family: sans-serif; padding: 40px; background: #f8f4ed; }}
    h1 {{ color: #0B5E4A; margin-bottom: 6px; }}
    p  {{ color: #6B7280; margin-bottom: 24px; }}
    table {{ border-collapse: collapse; width: 100%; background: white;
              border-radius: 12px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
    th {{ background: #0B5E4A; color: white; padding: 12px 16px; text-align: left; font-size: 0.85rem; }}
    td {{ padding: 12px 16px; border-bottom: 1px solid #f0ebe1; font-size: 0.9rem; }}
    tr:last-child td {{ border-bottom: none; }}
    tr:hover td {{ background: #f8f4ed; }}
    .export {{ display: inline-block; margin-bottom: 16px; background: #0B5E4A;
               color: white; padding: 10px 20px; border-radius: 8px; text-decoration: none;
               font-size: 0.875rem; font-weight: 600; }}
  </style>
</head><body>
  <h1>Pontora Waitlist 🎉</h1>
  <p>{count} people signed up so far</p>
  <a class="export" href="/export">⬇ Download CSV</a>
  <table>
    <thead><tr><th>#</th><th>Name</th><th>Email</th><th>Phone</th><th>Signed Up</th></tr></thead>
    <tbody>{rows if rows else '<tr><td colspan="5" style="text-align:center;color:#9CA3AF;padding:40px;">No signups yet</td></tr>'}</tbody>
  </table>
</body></html>"""

    return html


@app.route('/export')
def export():
    entries = WaitlistEntry.query.order_by(WaitlistEntry.signed_up).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'First Name', 'Last Name', 'Email', 'Phone', 'Signed Up'])
    for e in entries:
        writer.writerow([e.id, e.first_name, e.last_name, e.email, e.phone,
                         e.signed_up.strftime('%d/%m/%Y %H:%M')])

    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = 'attachment; filename=pontora_waitlist.csv'
    return response

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
