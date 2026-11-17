from ._common import *

# *************************************************** Tv Cast Dashboard HTTP Endpoint Section ************************************
@anvil.server.http_endpoint("/tv", methods=["GET"], enable_cors=True)
def dashboard_tv_endpoint():
    html = _build_dashboard_html()
    full_html = f"""<!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>BMA Auto Accessories - Dashboard</title>
        <style>
            body {{
                margin: 0;
                padding: 0;
                background-color: #f0f0f0;
            }}
            #status-bar {{
                display: none;
                background-color: #cc0000;
                color: white;
                text-align: center;
                padding: 8px;
                font-family: sans-serif;
                font-size: 14px;
                position: fixed;
                top: 0;
                width: 100%;
                z-index: 999;
            }}
            #status-bar.visible {{
                display: block;
            }}
            #dashboard-content {{
                padding-top: 0;
            }}
            #dashboard-content.offset {{
                padding-top: 36px;
            }}
        </style>
    </head>
    <body>
        <div id="status-bar">⚠️ Connection lost — retrying... Last updated: <span id="last-updated">—</span></div>
        <div id="dashboard-content">
            {html}
        </div>

        <script>
            const REFRESH_INTERVAL_MS = 60000; // 60 seconds
            const statusBar = document.getElementById('status-bar');
            const content = document.getElementById('dashboard-content');
            const lastUpdated = document.getElementById('last-updated');

            function formatTime(date) {{
                return date.toLocaleTimeString([], {{ hour: '2-digit', minute: '2-digit', second: '2-digit' }});
            }}

            async function refreshDashboard() {{
                try {{
                    const response = await fetch(window.location.href);
                    if (!response.ok) throw new Error('Server returned ' + response.status);

                    const fullHtml = await response.text();

                    // Parse the returned full HTML and extract only the dashboard-content div
                    const parser = new DOMParser();
                    const doc = parser.parseFromString(fullHtml, 'text/html');
                    const newContent = doc.getElementById('dashboard-content');

                    if (newContent) {{
                        content.innerHTML = newContent.innerHTML;
                    }}

                    // Hide error bar on success
                    statusBar.classList.remove('visible');
                    content.classList.remove('offset');
                    lastUpdated.textContent = formatTime(new Date());

                }} catch (err) {{
                    // Show error bar but keep last good data visible
                    statusBar.classList.add('visible');
                    content.classList.add('offset');
                    console.warn('Dashboard refresh failed:', err);
                }}
            }}

            // Kick off the refresh loop
            setInterval(refreshDashboard, REFRESH_INTERVAL_MS);
        </script>
    </body>
    </html>"""
    return anvil.server.HttpResponse(200, full_html, {"Content-Type": "text/html"})


def _build_dashboard_html(font_path: str = os.getenv("FONT_PATH")):
    # === Embed MozillaHeadline font as base64 ===
    #font_path = r"D:\BMAAutoAccessories\venv\Lib\site-packages\BMALocal\theme\assets\fonts\MozillaHeadline.ttf"
    font_base64 = ""
    if os.path.exists(font_path):
        with open(font_path, "rb") as f:
            font_base64 = base64.b64encode(f.read()).decode("utf-8")

    # =============================
    # 1. DASHBOARD QUERY
    # =============================
    with db_cursor() as cursor:
        dashboard_query = """
        SELECT ID, MakeAndModel, JobCardRef, RegNo, DueDate, ClientInstruction, Status
        FROM tbl_jobcarddetails 
        WHERE Status IN (
            'Checked In', 'Create Quote', 'Confirm Quote',
            'In Service', 'Verify Task', 'Issue Invoice', 'Ready for Pickup'
        )
        ORDER BY DueDate DESC
        """
        cursor.execute(dashboard_query)
        dashboard_rows = cursor.fetchall()

    # Group jobcards by status
    counts = {
        "Checked In": 0,
        "Create Quote": 0,
        "Confirm Quote": 0,
        "In Service": 0,
        "Verify Task": 0,
        "Issue Invoice": 0,
        "Ready for Pickup": 0
    }

    for r in dashboard_rows:
        status = r[6]
        if status in counts:
            counts[status] += 1

    # =============================
    # 2. Build DASHBOARD HTML
    # =============================
    dashboard_html = f"""
    <style>
        @font-face {{
            font-family: 'Mozilla Headline';
            src: url(data:font/ttf;base64,{font_base64}) format('truetype');
        }}
      body {{
        font-family: 'Headline', sans-serif;
        font-size: 16px;
      }}
      .dashboard-container {{
        text-align: center;
        margin: 10px;
      }}
      .dashboard-title {{
        background-color: #0066cc;
        color: white;
        padding: 10px;
        font-weight: bold;
        font-size: 20px;
        font-family: 'Mozilla Headline';
      }}
      .dashboard-grid {{
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 10px;
        margin-top: 10px;
      }}
      .dashboard-card {{
        border: 1px solid #ccc;
        padding: 20px;
        background: #f9f9f9;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.2);
        border-radius: 5px;
        font-size: 20px;
        font-family: 'Mozilla Headline';
      }}
      .card-icon {{
        font-size: 40px;
        margin-bottom: 4px;
        display: block;
      }}
      .dashboard-footer {{
        grid-column: span 3;
        border: 1px solid #ccc;
        padding: 20px;
        background: #f9f9f9;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.2);
        border-radius: 5px;
        font-size: 20px;
        font-family: 'Mozilla Headline';
      }}
    </style>

    <div class="dashboard-container">
      <div class="dashboard-title">Workflow Status Snapshot</div>
      <div class="dashboard-grid">
        <div class="dashboard-card"><span class="card-icon">✔️</span> 1. Checked In: {counts["Checked In"]}</div>
        <div class="dashboard-card"><span class="card-icon">📝</span> 2. Create Quote: {counts["Create Quote"]}</div>
        <div class="dashboard-card"><span class="card-icon">📄</span> 3. Confirm Quote: {counts["Confirm Quote"]}</div>
        <div class="dashboard-card"><span class="card-icon">🔧</span> 4. In Service: {counts["In Service"]}</div>
        <div class="dashboard-card"><span class="card-icon">✅</span> 5. Verify Task: {counts["Verify Task"]}</div>
        <div class="dashboard-card"><span class="card-icon">💰</span> 6. Issue Invoice: {counts["Issue Invoice"]}</div>
        <div class="dashboard-footer"><span class="card-icon">🚚</span> 7. Ready for Pickup: {counts["Ready for Pickup"]}</div>
      </div>
    </div>
    """

    # =============================
    # 3. ASSIGNED JOBS QUERY
    # =============================
    with db_cursor() as cursor:
        jobs_query = """
            SELECT 
                tbl_jobcarddetails.ReceivedDate,
                tbl_technicians.Fullname,
                tbl_jobcarddetails.RegNo,
                tbl_jobcarddetails.ClientInstruction,
                tbl_jobcarddetails.Status
            FROM 
                tbl_pendingassignedjobs
            JOIN 
                tbl_jobcarddetails 
                ON tbl_pendingassignedjobs.JobCardRefID = tbl_jobcarddetails.ID
            JOIN 
                tbl_technicians
                ON tbl_pendingassignedjobs.TechnicianID = tbl_technicians.ID
            WHERE 
                tbl_jobcarddetails.Status IN (
            'Checked In', 'Create Quote', 'Confirm Quote',
            'In Service', 'Verify Task', 'Issue Invoice', 'Ready for Pickup'
        )
            ORDER BY 
                tbl_jobcarddetails.ReceivedDate DESC;
        """
        cursor.execute(jobs_query)
        assigned_rows = cursor.fetchall()

    # =============================
    # 4. Assigned Jobs Table CSS
    # =============================
    assigned_css = f"""
    <style>
        @font-face {{
            font-family: 'Mozilla Headline';
            src: url(data:font/ttf;base64,{font_base64}) format('truetype');
        }}
        .items-table {{
            font-family: 'Mozilla Headline';
            border-collapse: collapse;
            width: 100%;
            margin: 20px 24px 24px 0;
            background-color: white;
            border-radius: 2px;
            overflow: hidden;
            box-shadow: 0 2px 2px 0 rgba(0, 0, 0, 0.14),
                        0 3px 1px -2px rgba(0, 0, 0, 0.2),
                        0 1px 5px 0 rgba(0, 0, 0, 0.12);
        }}
        .items-table th {{
            font-family: 'Mozilla Headline';
            background-color: #f5f5f5;
            border-bottom: 1px solid #e0e0e0;
            padding: 16px;
            text-align: left;
            font-weight: bold;
            font-size: 12px;
            color: rgba(0,0,0,0.87);
            text-transform: uppercase;
            letter-spacing: .5px;
        }}
        .items-table td {{
            border-bottom: 1px solid rgba(0,0,0,0.12);
            padding: 16px;
            font-size: 12px;
            color: rgba(0,0,0,0.87);
        }}
        .items-table .item-row:hover {{
            background-color: rgba(0,0,0,0.04);
        }}
    </style>
    """

    # =============================
    # 5. Build Assigned Jobs HTML Table
    # =============================
    assigned_html = assigned_css + """
    <h2 style="margin-left:20px;font-family: 'Mozilla Headline';">Assigned Jobs</h2>
    <table class="items-table">
        <thead>
            <tr>
                <th>No</th>
                <th>Received Date</th>
                <th>Technician</th>
                <th>Reg No</th>
                <th>Client Instruction</th>
                <th>Status</th>
            </tr>
        </thead>
        <tbody>
    """

    for i, row in enumerate(assigned_rows, start=1):
        received_date = row[0].strftime("%Y-%m-%d") if row[0] else ""
        technician = row[1]
        reg_no = row[2]
        raw_instruction = row[3] or ""
        status_raw = row[4]

        # Clean instructions
        text_only = re.sub(r'<[^>]+>', '', raw_instruction)
        lines = [line.strip() for line in text_only.splitlines() if line.strip()]
        safe_lines = [html_module.escape(line) for line in lines]
        formatted_instruction = "<br>".join(safe_lines)

        # Status
        status_display = status_raw if status_raw in [
            'Checked In', 'Create Quote', 'Confirm Quote',
            'In Service', 'Verify Task', 'Issue Invoice', 'Ready for Pickup'
        ] else "Unknown Status"

        assigned_html += f"""
            <tr class="item-row">
                <td>{i}</td>
                <td>{received_date}</td>
                <td>{technician}</td>
                <td>{reg_no}</td>
                <td>{formatted_instruction}</td>
                <td>{status_display}</td>
            </tr>
        """

    assigned_html += "</tbody></table>"

    # =============================
    # 6. RETURN COMBINED HTML
    # =============================
    return dashboard_html + "<br>" + assigned_html

__all__ = [
    'dashboard_tv_endpoint',
    '_build_dashboard_html',
]

from . import BMALocal as _compatibility_facade
