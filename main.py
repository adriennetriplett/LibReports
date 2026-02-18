from pathlib import Path
from nicegui import ui,app
from fastapi import Request
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
import threading

BASE_DIR = Path(__file__).parent
app.add_static_files('/static', BASE_DIR / 'static')

def button_row(label: str, help_text: str, on_click=None):
    """Create a button with hover-text to the right."""
    with ui.element('div').classes('button-row'):
        ui.button(label, on_click=on_click, color=None).style(
            'background-color: #0C5449; color: white; font-weight:500; border-radius:5px; border:3px solid #FFCC33;'
        )
        ui.label(help_text).classes('info-text')

def run_report(func, button_label):
    def target():
        ui.notify(f'{button_label} started...')
        try:
            func()
            ui.notify(f'{button_label} finished!')
        except Exception as e:
            ui.notify(f'{button_label} failed: {e}')
    threading.Thread(target=target).start()

def generate_loc_report():
    import time; time.sleep(2)

def generate_accession_report():
    import time; time.sleep(3)

def generate_paid_report():
    import time;
    time.sleep(3)

def generate_linked_report():
    import time; time.sleep(3)

def generate_checkout_report():
    import time; time.sleep(3)

def generate_reserves_report():
    import time; time.sleep(3)

@ui.page('/')
def main_page():
    ui.add_css("""
    .button-row { display:flex; align-items:center; margin-bottom:12px; }
    .button-row .info-text {
        margin-left: 20px;
        opacity:0;
        transition: opacity 0.15s ease-in-out;
        background:#f2f2f2;
        padding:8px 12px;
        border-radius:6px;
        min-width:320px;
    }
    .button-row:hover .info-text { opacity:1; }
    """, shared=True)

    with ui.element('div').style('''
        background:#0C5449;
        width:100vw;
        margin-left:calc(50% - 50vw);
        margin-top:calc(50% - 50vw);
    '''):
        with ui.row().classes('items-center').style('padding:10px 20px;'):
            ui.image('/static/wsuls.png').style('width:40%')

    ui.label('Library Reporting').style('font-size:32px; color:#0C5449; margin-bottom:20px')

    button_row(
        'Sort By LOC Call Number',
        'Sort a Sierra list of records by Library of Congress call number.',
        on_click=lambda: run_report(generate_loc_report, 'Sort By LOC Call Number')
    )

    button_row(
        'Sort By Accession Call Number',
        'Sort a Sierra list of records by accession call number.',
        on_click=lambda: run_report(generate_accession_report, 'Sort By Accession Call Number')
    )

    button_row(
        'Paid Order Record Report',
        'Generate a report of paid order records for the year to date.',
        on_click=lambda: run_report(generate_paid_report, 'Paid Order Record Report')
    )

    button_row(
        'Linked Records',
        'View relationships between bib, item, order, and checkin records.',
        on_click=lambda: run_report(generate_linked_report, 'Linked Records')
    )

    button_row(
        'Checkout Statistics',
        'View checkout metrics for items in a location.',
        on_click=lambda: run_report(generate_checkout_report, 'Checkout Statistics')
    )

    button_row(
        'Course Reserves',
        'Generate report of all items currently on course reserve.',
        on_click=lambda: run_report(generate_reserves_report, 'Course Reserves')
    )

ui.run(
    title='Library Reports',
    favicon='static/wsulogo2017_favicon.ico'
)
