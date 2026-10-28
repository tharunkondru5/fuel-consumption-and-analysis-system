import os
from datetime import date
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import mysql.connector
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, url_for
from mysql.connector import Error

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'change-this-local-development-key')


def connect_db():
    return mysql.connector.connect(host=os.getenv('DB_HOST', 'localhost'), port=int(os.getenv('DB_PORT', '3306')),
        user=os.getenv('DB_USER', 'root'), password=os.getenv('DB_PASSWORD', ''), database=os.getenv('DB_NAME', 'fuel_analysis'))


def query(sql, params=(), fetch=True):
    conn = connect_db()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, params)
        result = cur.fetchall() if fetch else None
        if not fetch:
            conn.commit()
        return result
    finally:
        conn.close()


def records_frame():
    return pd.DataFrame(query('''SELECT r.record_id, r.vehicle_id, v.vehicle_code, v.vehicle_type, v.fuel_type,
        r.fill_date, r.odometer_km, r.litres, r.total_cost, r.full_tank_flag FROM fuel_records r
        JOIN vehicles v USING(vehicle_id) ORDER BY v.vehicle_id, r.fill_date, r.record_id'''))


def calculate_metrics(frame):
    if frame.empty:
        return frame.assign(distance_km=pd.Series(dtype=float), mileage_kmpl=pd.Series(dtype=float), cost_per_km=pd.Series(dtype=float), calculation=pd.Series(dtype=str))
    frame = frame.copy()
    for col in ['distance_km', 'mileage_kmpl', 'cost_per_km']:
        frame[col] = np.nan
    frame['calculation'] = 'Baseline'
    for _, indices in frame.groupby('vehicle_id', sort=False).groups.items():
        previous_odo = previous_full = None
        litres_since_full = cost_since_full = 0.0
        for idx in list(indices):
            row = frame.loc[idx]
            odo = float(row.odometer_km)
            if previous_odo is not None and odo > previous_odo:
                distance = odo - previous_odo
                frame.loc[idx, ['distance_km', 'mileage_kmpl', 'cost_per_km']] = [distance, distance / float(row.litres), float(row.total_cost) / distance]
                frame.loc[idx, 'calculation'] = 'Approximate (distance / this fill litres)'
            if bool(row.full_tank_flag):
                if previous_full is not None and odo > float(frame.loc[previous_full, 'odometer_km']):
                    distance = odo - float(frame.loc[previous_full, 'odometer_km'])
                    litres = litres_since_full + float(row.litres)
                    cost = cost_since_full + float(row.total_cost)
                    frame.loc[idx, ['distance_km', 'mileage_kmpl', 'cost_per_km']] = [distance, distance / litres, cost / distance]
                    frame.loc[idx, 'calculation'] = 'Full-tank to full-tank (reliable)'
                previous_full = idx
                litres_since_full = cost_since_full = 0.0
            elif previous_full is not None:
                litres_since_full += float(row.litres)
                cost_since_full += float(row.total_cost)
            previous_odo = odo
    return frame


def make_charts(metrics):
    os.makedirs('static/charts', exist_ok=True)
    path = 'static/charts/monthly.png'
    exact = metrics[metrics.calculation == 'Full-tank to full-tank (reliable)'] if not metrics.empty else metrics
    if exact.empty:
        fig, ax = plt.subplots(figsize=(9, 4))
        ax.text(.5, .5, 'Add at least two valid full-tank records\nto see mileage trends', ha='center', va='center'); ax.axis('off')
    else:
        exact = exact.copy(); exact['month'] = pd.to_datetime(exact.fill_date).dt.to_period('M').astype(str)
        monthly = exact.groupby(['month', 'vehicle_code'], as_index=False).mileage_kmpl.mean()
        fig, ax = plt.subplots(figsize=(9, 4))
        for code, group in monthly.groupby('vehicle_code'):
            ax.plot(group.month, group.mileage_kmpl, marker='o', label=code)
        ax.set(title='Monthly fuel efficiency (full-tank calculations)', xlabel='Month', ylabel='Kilometres per litre')
        ax.grid(alpha=.25); ax.legend(); plt.xticks(rotation=35, ha='right')
    fig.tight_layout(); fig.savefig(path, dpi=140); plt.close(fig)


def make_expense_chart(metrics):
    os.makedirs('static/charts', exist_ok=True)
    fig, ax = plt.subplots(figsize=(9, 3.5))
    if metrics.empty:
        ax.text(.5, .5, 'Add fuel records to see monthly spending', ha='center', va='center')
        ax.axis('off')
    else:
        frame = metrics.copy()
        frame['month'] = pd.to_datetime(frame.fill_date).dt.to_period('M').astype(str)
        monthly = frame.groupby('month', as_index=False).total_cost.sum()
        ax.bar(monthly.month, monthly.total_cost, color='#338c7b')
        ax.set(title='Fuel expense by month', xlabel='Month', ylabel='Total cost')
        ax.grid(axis='y', alpha=.25)
        plt.xticks(rotation=35, ha='right')
    fig.tight_layout(); fig.savefig('static/charts/expense.png', dpi=140); plt.close(fig)

@app.route('/')
def dashboard():
    vehicles = query('SELECT * FROM vehicles ORDER BY vehicle_code')
    metrics = calculate_metrics(records_frame())
    if not metrics.empty:
        metrics['fill_date'] = pd.to_datetime(metrics.fill_date).dt.date
        metrics = metrics.sort_values(['fill_date', 'record_id'], ascending=False)
        report = metrics.to_dict('records')
        exact = metrics[metrics.calculation == 'Full-tank to full-tank (reliable)']
        summary = exact.groupby(['vehicle_code', 'vehicle_type', 'fuel_type'], as_index=False).agg(
            mileage_kmpl=('mileage_kmpl', 'mean'), cost_per_km=('cost_per_km', 'mean'), trips=('record_id', 'count')) if not exact.empty else pd.DataFrame()
        monthly = exact.copy()
        if not monthly.empty:
            monthly['month'] = pd.to_datetime(monthly.fill_date).dt.strftime('%Y-%m')
            monthly_summary = monthly.groupby(['month', 'vehicle_code'], as_index=False).mileage_kmpl.mean().to_dict('records')
        else: monthly_summary = []
        spend = float(metrics.total_cost.sum())
        invalid = metrics[(metrics.distance_km.isna()) | (metrics.distance_km <= 0)].to_dict('records')
    else:
        report, summary, monthly_summary, spend, invalid = [], pd.DataFrame(), [], 0, []
    make_charts(metrics)
    make_expense_chart(metrics)
    return render_template('dashboard.html', vehicles=vehicles, records=report,
        vehicle_summary=summary.to_dict('records') if not summary.empty else [], monthly_summary=monthly_summary,
        spend=spend, invalid=invalid, today=date.today().isoformat())


@app.route('/vehicles', methods=['POST'])
def add_vehicle():
    code = request.form.get('vehicle_code', '').strip().upper()
    kind, fuel = request.form.get('vehicle_type', '').strip(), request.form.get('fuel_type', '').strip()
    if not code or not kind or not fuel: flash('Enter a code, vehicle type and fuel type.', 'error')
    else:
        try:
            query('INSERT INTO vehicles(vehicle_code, vehicle_type, fuel_type) VALUES(%s,%s,%s)', (code, kind, fuel), fetch=False)
            flash('Vehicle added.', 'success')
        except Error: flash('Could not add vehicle. The code may already be in use.', 'error')
    return redirect(url_for('dashboard'))


@app.route('/records', methods=['POST'])
def add_record():
    try:
        vehicle_id = int(request.form['vehicle_id']); fill_date = date.fromisoformat(request.form['fill_date'])
        odo, litres, cost = float(request.form['odometer_km']), float(request.form['litres']), float(request.form['total_cost'])
        full = 1 if request.form.get('full_tank_flag') == 'on' else 0
        if odo < 0 or litres <= 0 or cost < 0: raise ValueError('Odometer and cost must be non-negative; litres must be greater than zero.')
        previous = query('SELECT fill_date, odometer_km FROM fuel_records WHERE vehicle_id=%s ORDER BY fill_date DESC, record_id DESC LIMIT 1', (vehicle_id,))
        if previous:
            prev = previous[0]
            if fill_date < prev['fill_date']: raise ValueError("Record date must be on or after the vehicle's latest record.")
            if odo <= float(prev['odometer_km']): raise ValueError("Odometer must be greater than the vehicle's latest reading.")
        query('INSERT INTO fuel_records(vehicle_id, fill_date, odometer_km, litres, total_cost, full_tank_flag) VALUES(%s,%s,%s,%s,%s,%s)',
            (vehicle_id, fill_date, odo, litres, cost, full), fetch=False)
        flash('Fuel record added.', 'success')
    except (ValueError, KeyError) as exc: flash(str(exc) or 'Please complete every fuel record field.', 'error')
    except Error: flash('Could not save the record. Check the database connection and selected vehicle.', 'error')
    return redirect(url_for('dashboard'))


@app.route('/records/<int:record_id>/delete', methods=['POST'])
def delete_record(record_id):
    query('DELETE FROM fuel_records WHERE record_id=%s', (record_id,), fetch=False)
    flash('Fuel record deleted.', 'success')
    return redirect(url_for('dashboard'))


if __name__ == '__main__':
    app.run(debug=os.getenv('FLASK_DEBUG', 'true').lower() == 'true')

