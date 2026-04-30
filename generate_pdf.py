#!/usr/bin/env python3
"""
ED AI Agent — Technical Architecture PDF Generator
Produces a multi-page architecture & integration reference document.
"""
import math
from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    HRFlowable, KeepTogether, PageBreak, Paragraph,
    SimpleDocTemplate, Spacer, Table, TableStyle,
)
from reportlab.platypus.flowables import Flowable
from reportlab.graphics.shapes import (
    Drawing, Rect, String, Line, Circle, Polygon, Group,
)

# ── Palette ────────────────────────────────────────────────────────────────────
INK    = colors.HexColor('#131414')
PAPER  = colors.HexColor('#fbf9f4')
BG     = colors.HexColor('#f4f1ea')
ACCENT = colors.HexColor('#c8341f')
MUTED  = colors.HexColor('#8b8a85')
RULE   = colors.HexColor('#d0cdc4')
WHITE  = colors.white

# Layer colours
FRONT  = colors.HexColor('#1a3a5c')   # Browser / Frontend
FAST   = colors.HexColor('#1a4a2a')   # FastAPI backend
AI_C   = colors.HexColor('#3d1258')   # LangChain / AI
MCP_C  = colors.HexColor('#6b2d00')   # MCP server
DB_C   = colors.HexColor('#1a3a4a')   # SQLite / database

# ESI colours
ESI = {1:'#ff4d3d', 2:'#ff8a3d', 3:'#ffd23d', 4:'#6fcf6f', 5:'#4d9eff'}

W, H = A4   # 595 × 842 pt

# ── Drawing primitives ─────────────────────────────────────────────────────────

def _box(d, x, y, w, h, fill=FAST, lbl=None, sub=None,
         tc=WHITE, border=INK, bw=1, fs=9, fs2=7):
    d.add(Rect(x, y, w, h, fillColor=fill, strokeColor=border, strokeWidth=bw))
    if lbl:
        yo = y + h/2 + (5 if sub else 0)
        d.add(String(x+w/2, yo, lbl, fontSize=fs, fillColor=tc,
                     textAnchor='middle', fontName='Helvetica-Bold'))
    if sub:
        d.add(String(x+w/2, y+h/2-9, sub, fontSize=fs2, fillColor=tc,
                     textAnchor='middle', fontName='Helvetica'))


def _txt(d, x, y, s, fs=8, c=INK, anc='start', bold=False):
    d.add(String(x, y, s, fontSize=fs, fillColor=c,
                 textAnchor=anc, fontName='Helvetica-Bold' if bold else 'Helvetica'))


def _arr(d, x1, y1, x2, y2, c=INK, lw=1.5, lbl=None, dashed=False):
    """Draw an arrowed line from (x1,y1) → (x2,y2)."""
    dash = [5, 3] if dashed else None
    kw = dict(strokeColor=c, strokeWidth=lw)
    if dash:
        kw['strokeDashArray'] = dash
    d.add(Line(x1, y1, x2, y2, **kw))
    ang = math.atan2(y2 - y1, x2 - x1)
    sz = 7
    qx = x2 - sz * math.cos(ang - 0.45)
    qy = y2 - sz * math.sin(ang - 0.45)
    rx = x2 - sz * math.cos(ang + 0.45)
    ry = y2 - sz * math.sin(ang + 0.45)
    d.add(Polygon([x2, y2, qx, qy, rx, ry],
                  fillColor=c, strokeColor=c, strokeWidth=0))
    if lbl:
        mx, my = (x1+x2)/2, (y1+y2)/2
        d.add(String(mx+3, my+3, lbl, fontSize=6.5, fillColor=c, textAnchor='start'))


def _darr(d, x1, y1, x2, y2, c=MUTED, lbl=None):
    _arr(d, x1, y1, x2, y2, c=c, lw=1, lbl=lbl, dashed=True)


def _bracket(d, x, y, w, fill=BG):
    d.add(Rect(x, y, w, 14, fillColor=fill, strokeColor=None))


# ── Styles ─────────────────────────────────────────────────────────────────────
_ss = getSampleStyleSheet()

def _ps(base='Normal', **kw):
    return ParagraphStyle('_', parent=_ss[base], **kw)

S_H1  = _ps('Heading1', fontName='Times-Bold',  fontSize=22, textColor=INK,
             spaceAfter=6, spaceBefore=14)
S_H2  = _ps('Heading2', fontName='Times-Bold',  fontSize=15, textColor=INK,
             spaceAfter=4, spaceBefore=10, borderPad=0)
S_H3  = _ps('Heading3', fontName='Helvetica-Bold', fontSize=10,
             textColor=ACCENT, spaceAfter=3, spaceBefore=6)
S_BODY = _ps(fontName='Helvetica', fontSize=9, textColor=INK,
             spaceAfter=3, leading=13)
S_MONO = _ps('Code', fontName='Courier', fontSize=8, textColor=INK,
             backColor=BG, spaceAfter=2, leading=12)
S_CAP  = _ps(fontName='Helvetica', fontSize=7.5, textColor=MUTED,
             alignment=TA_CENTER, spaceAfter=8)
S_TOC  = _ps(fontName='Helvetica', fontSize=9, textColor=INK, leading=16)
S_TOCN = _ps(fontName='Helvetica-Bold', fontSize=9, textColor=ACCENT, leading=16)


# ── Page header/footer ─────────────────────────────────────────────────────────

def _on_page(cv, doc):
    cv.saveState()
    cv.setFillColor(MUTED)
    cv.setFont('Helvetica', 7)
    cv.drawString(cm, 0.65*cm, 'ED AI Agent — Technical Architecture & Integration Reference — Adviava Regional Medical Center')
    cv.drawRightString(W - cm, 0.65*cm, f'Page {doc.page}')
    cv.setStrokeColor(RULE)
    cv.setLineWidth(0.5)
    cv.line(cm, 0.95*cm, W - cm, 0.95*cm)
    cv.restoreState()


def _on_cover(cv, doc):
    """Cover page has no footer."""
    pass


# ══════════════════════════════════════════════════════════════════════════════
#  DIAGRAM 1 — COVER
# ══════════════════════════════════════════════════════════════════════════════

def make_cover(dw):
    d = Drawing(dw, 680)
    DH = 680

    # Background
    d.add(Rect(0, 0, dw, DH, fillColor=PAPER, strokeColor=None))

    # Red top bar
    d.add(Rect(0, DH-72, dw, 72, fillColor=ACCENT, strokeColor=None))

    # Cross symbol
    cx, cy = dw/2, DH - 36
    d.add(Rect(cx-4, cy-20, 8, 40, fillColor=WHITE, strokeColor=None))
    d.add(Rect(cx-16, cy-4, 32, 8, fillColor=WHITE, strokeColor=None))

    # Org label
    _txt(d, dw/2, DH-90, 'MERCY REGIONAL MEDICAL CENTER', 10, ACCENT, 'middle', True)
    _txt(d, dw/2, DH-103, 'Emergency Department  ·  24-Hour Acute Care  ·  Level I Trauma', 8, MUTED, 'middle')

    # Main title
    d.add(String(dw/2, DH-148, 'ED AI Agent Platform', fontSize=34,
                 fillColor=INK, textAnchor='middle', fontName='Times-Bold'))
    d.add(String(dw/2, DH-172, 'Technical Architecture & Integration Reference', fontSize=13,
                 fillColor=INK, textAnchor='middle', fontName='Times-Roman'))

    # Red rule
    d.add(Rect(1.5*cm, DH-185, dw - 3*cm, 2, fillColor=ACCENT, strokeColor=None))

    # Architecture preview — stacked layers
    bx = 1.5*cm
    bw = dw - 3*cm
    bh = 38
    gap = 6
    layers = [
        (FRONT, 'BROWSER / CLIENT LAYER',      '3 HTML pages  ·  Vanilla JS  ·  CSS Paper Aesthetic'),
        (FAST,  'FASTAPI APPLICATION SERVER',   'Python 3.14  ·  Uvicorn ASGI  ·  5 REST endpoints  ·  Port 8000'),
        (AI_C,  'LANGCHAIN AI AGENT',           'Claude Sonnet 4.6  ·  ReAct  ·  LangGraph  ·  Tool Calling'),
        (MCP_C, 'MYSQL MCP SERVER (FastMCP)',   'Model Context Protocol  ·  stdio Transport  ·  9 Database Tools'),
        (DB_C,  'SQLITE DATA LAYER',            '7 Tables  ·  10 Patients  ·  12 Triage Records  ·  90+ Rows'),
    ]
    top_y = DH - 205
    for i, (fill, lbl, sub) in enumerate(layers):
        by = top_y - i*(bh + gap)
        _box(d, bx, by, bw, bh, fill=fill, lbl=lbl, sub=sub, fs=10, fs2=8)
        if i < len(layers)-1:
            mid = bx + bw/2
            ay = by - gap/2
            d.add(Polygon([mid, ay-1, mid-6, ay+4, mid+6, ay+4],
                          fillColor=MUTED, strokeColor=None))

    # Bottom metadata grid
    meta_y = top_y - len(layers)*(bh+gap) - 16
    d.add(Rect(bx, meta_y - 30, bw, 32, fillColor=BG, strokeColor=RULE, strokeWidth=0.5))
    meta = [
        ('Version', '1.0'), ('Date', datetime.now().strftime('%B %d, %Y')),
        ('Model', 'claude-sonnet-4-6'), ('Protocol', 'MCP stdio (FastMCP 1.27)'),
    ]
    col_w = bw / 4
    for i, (k, v) in enumerate(meta):
        mx = bx + i*col_w + 8
        _txt(d, mx, meta_y - 12, k+':', 7, MUTED, bold=True)
        _txt(d, mx, meta_y - 23, v, 7, INK)

    # Tech badges at bottom
    badges = ['Python 3.14', 'FastAPI', 'LangChain', 'LangGraph', 'MCP', 'SQLite', 'ReportLab']
    bx2 = 1.5*cm
    by2 = 22
    for label in badges:
        bw2 = len(label)*5.2 + 10
        d.add(Rect(bx2, by2, bw2, 14, fillColor=INK, strokeColor=None))
        _txt(d, bx2+bw2/2, by2+4, label, 7, WHITE, 'middle', True)
        bx2 += bw2 + 6

    return d


# ══════════════════════════════════════════════════════════════════════════════
#  DIAGRAM 2 — HIGH-LEVEL SYSTEM ARCHITECTURE
# ══════════════════════════════════════════════════════════════════════════════

def make_arch_overview(dw):
    DH = 520
    d = Drawing(dw, DH)
    d.add(Rect(0, 0, dw, DH, fillColor=PAPER, strokeColor=None))

    # ── Row Y positions (bottom of each row box)
    R = [DH-60, DH-145, DH-235, DH-325, DH-415]
    BH = 64
    M = 20
    BW = dw - 2*M

    # ── Row 0: Browser
    _box(d, M, R[0], BW, BH, fill=FRONT, lbl='BROWSER / CLIENT', sub='Dashboard  ·  Chat UI  ·  Intake Form', fs=11, fs2=8)
    # Sub-boxes
    sub_w = (BW - 24) / 3
    for i, lbl in enumerate(['index.html\nDashboard', 'chat.html\nAI Assistant', 'intake.html\nPatient Intake']):
        lines = lbl.split('\n')
        sx = M + 8 + i*(sub_w+4)
        d.add(Rect(sx, R[0]+4, sub_w, BH-8, fillColor=colors.HexColor('#2a5080'), strokeColor=None))
        _txt(d, sx+sub_w/2, R[0]+BH-22, lines[0], 7, WHITE, 'middle', True)
        _txt(d, sx+sub_w/2, R[0]+BH-33, lines[1], 6.5, colors.HexColor('#aaccee'), 'middle')

    # ── Arrow 0→1
    _arr(d, dw/2, R[0], dw/2, R[1]+BH, ACCENT, 2, 'HTTP/REST  Port 8000')

    # ── Row 1: FastAPI
    _box(d, M, R[1], BW, BH, fill=FAST, lbl='FASTAPI APPLICATION SERVER', sub='Python 3.14  ·  Uvicorn ASGI  ·  app/main.py', fs=11, fs2=8)
    ep_w = (BW - 24) / 5
    endpoints = ['GET /', 'GET /chat', 'GET /intake', 'POST /api/chat', 'POST /api/intake']
    for i, ep in enumerate(endpoints):
        ex = M + 8 + i*(ep_w+2)
        d.add(Rect(ex, R[1]+4, ep_w, BH-8, fillColor=colors.HexColor('#2a6040'), strokeColor=None))
        _txt(d, ex+ep_w/2, R[1]+BH/2-3, ep, 6.5, WHITE, 'middle')

    # ── Three arrows from FastAPI row
    # Left: direct DB
    _arr(d, M+BW*0.17, R[1], M+BW*0.17, R[2]+BH, DB_C, 1.5, 'SQL direct')
    # Center: AI agent
    _arr(d, dw/2, R[1], dw/2, R[2]+BH, AI_C, 1.5, 'ainvoke()')
    # Right: DB write
    _arr(d, M+BW*0.83, R[1], M+BW*0.83, R[2]+BH, FAST, 1.5, 'INSERT')

    # ── Row 2: Agent + two DB boxes
    # Left DB box
    lw = BW*0.28
    _box(d, M, R[2], lw, BH, fill=DB_C, lbl='SQLite Direct', sub='/api/stats\n/api/patients', fs=9)
    # Center: Agent
    cw = BW*0.38
    _box(d, M+lw+6, R[2], cw, BH, fill=AI_C, lbl='LANGCHAIN REACT AGENT', sub='claude-sonnet-4-6  ·  LangGraph\napp/agent.py', fs=9, fs2=7)
    # Right: Form persist
    rw = BW - lw - cw - 12
    _box(d, M+lw+cw+12, R[2], rw, BH, fill=FAST, lbl='Form Persist', sub='/api/intake\nSQLite INSERT', fs=9)

    # ── Arrow center→below (Agent → MCP)
    cx = M + lw + 6 + cw/2
    _arr(d, cx, R[2], cx, R[3]+BH, MCP_C, 1.5, 'MCP session()')

    # Connect DB boxes down
    _arr(d, M+lw/2, R[2], M+lw/2, R[3]+BH, DB_C, 1.2)
    _arr(d, M+lw+cw+12+rw/2, R[2], M+lw+cw+12+rw/2, R[3]+BH, DB_C, 1.2)

    # ── Row 3: MCP Client | Anthropic API | (empty)
    mw = BW*0.44
    _box(d, M, R[3], mw, BH, fill=MCP_C, lbl='MCP CLIENT', sub='MultiServerMCPClient\nlangchain-mcp-adapters 0.2.2', fs=10, fs2=7)
    aw = BW*0.38
    ax = M + mw + 6
    _box(d, ax, R[3], aw, BH, fill=colors.HexColor('#1e1e3a'), lbl='ANTHROPIC API', sub='claude-sonnet-4-6\nHTTPS  ·  anthropic SDK 0.96', fs=10, fs2=7)
    # Arrow to Anthropic
    _arr(d, M+mw, R[3]+BH/2, ax, R[3]+BH/2, colors.HexColor('#5555cc'), 1.5, 'API call')
    _darr(d, ax+aw, R[3]+BH/2, M+mw, R[3]+BH/2+8, colors.HexColor('#5555cc'), 'response')

    # ── Arrow MCP Client→Server
    _arr(d, M+mw/2, R[3], M+mw/2, R[4]+BH, MCP_C, 1.5, 'stdio subprocess')

    # ── Row 4: MCP Server + SQLite
    sw = BW*0.44
    _box(d, M, R[4], sw, BH, fill=MCP_C, lbl='MCP SERVER  (FastMCP)', sub='mcp_server/server.py  ·  9 Tools\nstdio transport  ·  mcp 1.27.0', fs=10, fs2=7)
    # Tools list
    tools = ['list_tables','describe_table','execute_query','get_patient_by_mrn','get_todays_patients','get_triage_statistics','get_critical_patients','search_patients','insert_patient_intake']
    tstr = '  ·  '.join(tools[:4]) + '\n' + '  ·  '.join(tools[4:])
    # Small note below MCP box
    for li, tl in enumerate(tstr.split('\n')):
        _txt(d, M+2, R[4]-10-li*10, tl, 6, MUTED)

    dbw = BW - sw - 6
    _box(d, M+sw+6, R[4], dbw, BH, fill=DB_C, lbl='SQLite DATABASE', sub='ed_database.db  ·  7 tables\nPatients · Triage · Vitals · Meds · Allergies', fs=10, fs2=7)
    # Arrow MCP→DB
    _arr(d, M+sw, R[4]+BH/2, M+sw+6, R[4]+BH/2, DB_C, 2, 'sqlite3')

    return d


# ══════════════════════════════════════════════════════════════════════════════
#  DIAGRAM 3 — AI CHAT REQUEST SEQUENCE
# ══════════════════════════════════════════════════════════════════════════════

def make_chat_sequence(dw):
    DH = 500
    d = Drawing(dw, DH)
    d.add(Rect(0, 0, dw, DH, fillColor=PAPER, strokeColor=None))

    actors = ['Browser', 'FastAPI', 'LangChain\nAgent', 'MCP\nClient', 'MCP\nServer', 'SQLite', 'Anthropic\nAPI']
    cols = len(actors)
    margin = 28
    col_w = (dw - 2*margin) / (cols - 1)
    xs = [margin + i*col_w for i in range(cols)]
    box_h = 32
    top = DH - 20
    colors_map = [FRONT, FAST, AI_C, MCP_C, MCP_C, DB_C, colors.HexColor('#1e1e3a')]

    # Actor boxes + lifelines
    for i, (actor, xp, col) in enumerate(zip(actors, xs, colors_map)):
        lines = actor.split('\n')
        bx = xp - 32
        d.add(Rect(bx, top - box_h, 64, box_h, fillColor=col, strokeColor=INK, strokeWidth=0.7))
        for li, ln in enumerate(lines):
            _txt(d, xp, top-box_h+box_h/2-len(lines)*5+li*10+3, ln, 7, WHITE, 'middle', True)
        # Lifeline
        d.add(Line(xp, top-box_h, xp, 28, strokeColor=MUTED, strokeWidth=0.5,
                   strokeDashArray=[4, 3]))

    # Steps
    steps = [
        # (from_idx, to_idx, y, label, return_lbl, ret_y)
        (0, 1, top-60,  'POST /api/chat  {message}',          '200 {response, tool_calls}', top-80),
        (1, 2, top-110, 'ainvoke({messages})',                 None, None),
        (2, 3, top-155, 'agent_session()',                     None, None),
        (3, 4, top-195, 'stdio: initialize',                   None, None),
        (4, 3, top-225, 'ListToolsResponse (9 tools)',         None, None),
        (2, 6, top-265, 'Claude API: think + choose tool',     'tool_name + args', top-285),
        (3, 4, top-320, 'stdio: CallToolRequest',              None, None),
        (4, 5, top-350, 'sqlite3.execute(SQL)',                'rows[]', top-370),
        (4, 3, top-395, 'CallToolResponse (JSON)',             None, None),
        (2, 6, top-430, 'Claude API: final answer',            'AIMessage.content', top-450),
        (1, 0, top-480, 'JSON: response + tool_calls[]',       None, None),
    ]

    ret_color = colors.HexColor('#3d8b6e')

    for step_data in steps:
        fi, ti, y, lbl, rlbl, ry = step_data
        x1, x2 = xs[fi], xs[ti]
        _arr(d, x1, y, x2, y, ACCENT if fi < ti else ret_color, 1.2, None)
        # Label above arrow
        mx = (x1+x2)/2
        _txt(d, mx, y+3, lbl, 6.5, ACCENT if fi < ti else ret_color, 'middle')
        if rlbl and ry:
            _arr(d, x2, ry, x1, ry, ret_color, 1, None, dashed=True)
            _txt(d, (x1+x2)/2, ry+3, rlbl, 6, ret_color, 'middle')

    # Activation boxes on lifelines (thick segments)
    acts = [(2, top-100, top-480), (3, top-145, top-410), (4, top-185, top-400)]
    for idx, y1, y2 in acts:
        d.add(Rect(xs[idx]-5, y2, 10, y1-y2, fillColor=colors.HexColor('#dddddd'),
                   strokeColor=MUTED, strokeWidth=0.5))

    # Legend
    _txt(d, margin, 14, 'Forward call', 7, ACCENT, bold=True)
    d.add(Line(margin+68, 17, margin+92, 17, strokeColor=ACCENT, strokeWidth=1.5))
    d.add(Polygon([margin+92, 17, margin+86, 14, margin+86, 20],
                  fillColor=ACCENT, strokeColor=ACCENT, strokeWidth=0))
    _txt(d, margin+100, 14, 'Return / response', 7, ret_color, bold=True)
    d.add(Line(margin+192, 17, margin+216, 17, strokeColor=ret_color, strokeWidth=1,
               strokeDashArray=[4, 2]))

    return d


# ══════════════════════════════════════════════════════════════════════════════
#  DIAGRAM 4 — PATIENT INTAKE FLOW
# ══════════════════════════════════════════════════════════════════════════════

def make_intake_flow(dw):
    DH = 400
    d = Drawing(dw, DH)
    d.add(Rect(0, 0, dw, DH, fillColor=PAPER, strokeColor=None))

    bh, bw_s, gap = 36, 100, 14
    # Flow nodes (x-center, y-bottom, label, sublabel, fill)
    nodes = [
        (dw/2, DH-50,  'NURSE',         'intake.html',        FRONT),
        (dw/2, DH-130, 'BROWSER',       'FormData → JSON',    FRONT),
        (dw/2, DH-210, 'POST /api/intake', 'FastAPI endpoint',FAST),
        (dw/2, DH-290, 'INPUT VALIDATION', 'Pydantic model',  colors.HexColor('#3a3a3a')),
        (dw/4, DH-370, 'INSERT patient', 'if new MRN',        DB_C),
        (3*dw/4, DH-370, 'INSERT triage', 'new record',       DB_C),
    ]

    # Decision diamond at validation level
    dy = DH - 290
    diam_x = dw/2
    diam_h = 30
    diam_w = 130
    pts = [diam_x, dy+diam_h/2+diam_h/2,   # top
           diam_x+diam_w/2, dy+diam_h/2,     # right
           diam_x, dy,                         # bottom
           diam_x-diam_w/2, dy+diam_h/2]      # left
    d.add(Polygon(pts, fillColor=colors.HexColor('#3a3a3a'), strokeColor=INK, strokeWidth=1))
    _txt(d, diam_x, dy+diam_h/2-3, 'Validate & Route', 7.5, WHITE, 'middle', True)

    for i, (nx, ny, lbl, sub, fill) in enumerate(nodes):
        if i == 3:   # skip diamond — drawn above
            continue
        _box(d, nx-bw_s/2, ny-bh, bw_s, bh, fill=fill, lbl=lbl, sub=sub, fs=8, fs2=6.5)

    # Arrows
    _arr(d, dw/2, nodes[0][1]-bh, dw/2, nodes[1][1], ACCENT, 1.5, 'fill & submit')
    _arr(d, dw/2, nodes[1][1]-bh, dw/2, nodes[2][1], ACCENT, 1.5, 'fetch POST')
    _arr(d, dw/2, nodes[2][1]-bh, dw/2, dy+diam_h, ACCENT, 1.5)
    # Diamond → two DB nodes
    _arr(d, diam_x - diam_w/2, dy+diam_h/2, dw/4 + bw_s/2, nodes[4][1], DB_C, 1.2, 'patient_id')
    _arr(d, diam_x + diam_w/2, dy+diam_h/2, 3*dw/4 - bw_s/2, nodes[5][1], DB_C, 1.2, 'triage_id')

    # Response arrow back up
    resp_x = dw/2 + 14
    _darr(d, resp_x, DH-370, resp_x, nodes[2][1], colors.HexColor('#3d8b6e'), '{success, patient_id, triage_id}')
    _darr(d, resp_x, nodes[2][1]-bh, resp_x, nodes[1][1], colors.HexColor('#3d8b6e'), 'redirect → /')

    # Right panel: what gets stored
    px = dw*0.66
    py_top = DH - 60
    d.add(Rect(px, py_top-180, dw-px-8, 180, fillColor=BG, strokeColor=RULE, strokeWidth=0.7))
    _txt(d, px+8, py_top-14, 'Stored Fields', 8, INK, bold=True)
    fields = ['mrn (generated)', 'first_name, last_name', 'dob, age, biological_sex',
              'phone, address, language', 'chief_complaint', 'esi_level  (1-5)',
              'arrival_mode, date, time', 'disposition, triage_nurse']
    for i, f in enumerate(fields):
        _txt(d, px+14, py_top-28-i*18, '▪  ' + f, 7, INK)

    return d


# ══════════════════════════════════════════════════════════════════════════════
#  DIAGRAM 5 — MCP INTEGRATION DETAIL
# ══════════════════════════════════════════════════════════════════════════════

def make_mcp_detail(dw):
    DH = 480
    d = Drawing(dw, DH)
    d.add(Rect(0, 0, dw, DH, fillColor=PAPER, strokeColor=None))

    # Left: LangChain Agent
    _box(d, 10, DH-150, 130, 130, fill=AI_C,
         lbl='LANGCHAIN\nREACT AGENT', sub='create_react_agent()\nClaude Sonnet 4.6\napp/agent.py', fs=9, fs2=7)
    _txt(d, 75, DH-155, 'LangGraph runtime', 6.5, AI_C, 'middle')
    # Thought bubbles inside
    for i, s in enumerate(['1. Receive user query', '2. Choose tool', '3. Call tool', '4. Observe result', '5. Final answer']):
        _txt(d, 16, DH-180-i*16, s, 6.5, colors.HexColor('#ccaaee'))

    # Middle: MCP Client
    _box(d, 165, DH-120, 130, 100, fill=MCP_C,
         lbl='MCP CLIENT', sub='MultiServerMCPClient\nlangchain_mcp_adapters\n0.2.2', fs=9, fs2=7)

    # Protocol labels
    _arr(d, 140, DH-100, 165, DH-100, ACCENT, 2, 'ainvoke(tools)')
    _darr(d, 165, DH-115, 140, DH-115, colors.HexColor('#3d8b6e'), 'ToolMessage')

    # Right: MCP Server
    _box(d, 320, DH-150, 150, 130, fill=MCP_C,
         lbl='MCP SERVER', sub='FastMCP  mcp 1.27.0\nmcp_server/server.py', fs=9, fs2=7)

    # stdio protocol arrows
    _arr(d, 295, DH-95, 320, DH-95, MCP_C, 2, 'initialize')
    _arr(d, 295, DH-110, 320, DH-110, MCP_C, 1.5, 'ListToolsRequest')
    _darr(d, 320, DH-125, 295, DH-125, MCP_C, 'ListToolsResponse')
    _arr(d, 295, DH-140, 320, DH-140, MCP_C, 1.5, 'CallToolRequest')
    _darr(d, 320, DH-155, 295, DH-155, MCP_C, 'CallToolResponse')

    # stdio badge
    d.add(Rect(290, DH-80, 35, 12, fillColor=ACCENT, strokeColor=None))
    _txt(d, 307, DH-72, 'stdio', 7, WHITE, 'middle', True)
    _txt(d, 307, DH-62, 'subprocess', 6, MUTED, 'middle')

    # Bottom: DB
    _box(d, 320, DH-310, 150, 80, fill=DB_C,
         lbl='SQLITE DB', sub='ed_database.db\n7 tables  ·  sqlite3', fs=9, fs2=7)
    _arr(d, 395, DH-150, 395, DH-230, DB_C, 2, 'sqlite3.execute()')
    _darr(d, 395, DH-230, 395, DH-295, DB_C, 'rows[]')

    # 9 Tools panel on right
    tx = 490
    d.add(Rect(tx, DH-360, dw-tx-8, 340, fillColor=BG, strokeColor=RULE, strokeWidth=0.5))
    _txt(d, tx+8, DH-18, 'MCP Tools  (9)', 8.5, INK, bold=True)
    _txt(d, tx+8, DH-30, 'Registered via @mcp.tool()', 6.5, MUTED)
    tools = [
        ('list_tables',            'List all DB tables'),
        ('describe_table',         'Schema + row count'),
        ('execute_query',          'SELECT-only SQL'),
        ('get_patient_by_mrn',     'Full patient record'),
        ('get_todays_patients',    'Census by date'),
        ('get_triage_statistics',  'ESI distribution'),
        ('get_critical_patients',  'ESI 1-2 with vitals'),
        ('search_patients',        'Name / MRN search'),
        ('insert_patient_intake',  'New patient + triage'),
    ]
    for i, (name, desc) in enumerate(tools):
        gy = DH - 52 - i*32
        d.add(Rect(tx+6, gy-2, dw-tx-20, 26, fillColor=colors.HexColor('#ede9de'),
                   strokeColor=RULE, strokeWidth=0.5))
        _txt(d, tx+12, gy+12, name, 7.5, MCP_C, bold=True)
        _txt(d, tx+12, gy+3, desc, 6.5, MUTED)

    # Transport protocol note at bottom
    by = 26
    _txt(d, 10, by, 'Transport:  stdio  (subprocess per request)  —  MCP 1.27.0  —  JSON-RPC 2.0 framing', 7, MUTED)

    return d


# ══════════════════════════════════════════════════════════════════════════════
#  DIAGRAM 6 — DATABASE ER DIAGRAM
# ══════════════════════════════════════════════════════════════════════════════

def make_er_diagram(dw):
    DH = 560
    d = Drawing(dw, DH)
    d.add(Rect(0, 0, dw, DH, fillColor=PAPER, strokeColor=None))

    # Table definitions: (label, x, y, width, height, rows, key_cols)
    tables = {
        'patients': {
            'x': 8, 'y': DH-230, 'w': 150, 'h': 210,
            'cols': ['id  PK', 'mrn  UNIQUE', 'first_name', 'last_name', 'dob', 'age', 'biological_sex',
                     'phone', 'address', 'language', 'ssn_last4', 'created_at'],
            'rows': 10,
        },
        'triage_records': {
            'x': 185, 'y': DH-250, 'w': 158, 'h': 230,
            'cols': ['id  PK', 'patient_id  FK', 'mrn', 'arrival_date', 'arrival_time', 'arrival_mode',
                     'chief_complaint', 'esi_level', 'disposition', 'triage_nurse', 'triage_note',
                     'isolation_type', 'fall_risk', 'code_status'],
            'rows': 12,
        },
        'vital_signs': {
            'x': 370, 'y': DH-245, 'w': 148, 'h': 220,
            'cols': ['id  PK', 'triage_id  FK', 'patient_id  FK', 'reading_number', 'reading_time',
                     'blood_pressure', 'heart_rate', 'respiratory_rate', 'temperature',
                     'spo2', 'o2_source', 'glucose', 'gcs'],
            'rows': 12,
        },
        'allergies': {
            'x': 8, 'y': DH-410, 'w': 150, 'h': 100,
            'cols': ['id  PK', 'patient_id  FK', 'allergen', 'reaction_type', 'severity', 'notes'],
            'rows': 8,
        },
        'medications': {
            'x': 185, 'y': DH-420, 'w': 158, 'h': 115,
            'cols': ['id  PK', 'patient_id  FK', 'medication_name', 'dose', 'frequency', 'route', 'last_taken'],
            'rows': 19,
        },
        'medical_history': {
            'x': 370, 'y': DH-410, 'w': 148, 'h': 100,
            'cols': ['id  PK', 'patient_id  FK', 'condition_name', 'category', 'year_diagnosed'],
            'rows': 19,
        },
        'emergency_contacts': {
            'x': 540, 'y': DH-320, 'w': 130, 'h': 100,
            'cols': ['id  PK', 'patient_id  FK', 'name', 'relationship', 'phone'],
            'rows': 10,
        },
    }

    row_h = 14
    hdr_h = 22

    for tname, info in tables.items():
        tx, ty, tw, th = info['x'], info['y'], info['w'], info['h']
        cols = info['cols']
        # Header
        d.add(Rect(tx, ty+th-hdr_h, tw, hdr_h, fillColor=DB_C, strokeColor=INK, strokeWidth=1))
        _txt(d, tx+tw/2, ty+th-hdr_h+8, tname, 8, WHITE, 'middle', True)
        d.add(Rect(tw-30, ty+th-hdr_h+3, 28, 10, fillColor=colors.HexColor('#2a6080'), strokeColor=None))
        _txt(d, tw-16+tx, ty+th-hdr_h+7, f'{info["rows"]} rows', 5.5, WHITE, 'middle')
        # Body
        d.add(Rect(tx, ty, tw, th-hdr_h, fillColor=colors.white, strokeColor=INK, strokeWidth=1))
        for i, col in enumerate(cols):
            cy = ty + th - hdr_h - (i+1)*row_h
            if cy < ty:
                break
            if i % 2 == 0:
                d.add(Rect(tx+1, cy, tw-2, row_h, fillColor=BG, strokeColor=None))
            pk = col.endswith('PK')
            fk = col.endswith('FK')
            c = colors.HexColor('#c8341f') if pk else (colors.HexColor('#2060a0') if fk else INK)
            _txt(d, tx+6, cy+4, col, 6.5, c, bold=pk or fk)

    # Relationship lines
    rels = [
        # (from_table, from_side, to_table, to_side)
        ('patients', 'right_center', 'triage_records', 'left_center'),
        ('patients', 'right_center', 'allergies', 'left_center'),
        ('patients', 'right_center', 'medications', 'left_center'),
        ('patients', 'right_center', 'medical_history', 'right_top'),
        ('patients', 'right_center', 'emergency_contacts', 'right_top'),
        ('triage_records', 'right_center', 'vital_signs', 'left_center'),
    ]

    def get_anchor(tname, side):
        info = tables[tname]
        tx, ty, tw, th = info['x'], info['y'], info['w'], info['h']
        if side == 'right_center':
            return tx+tw, ty+th/2
        elif side == 'left_center':
            return tx, ty+th/2
        elif side == 'right_top':
            return tx+tw, ty+th-hdr_h/2
        return tx+tw/2, ty

    for ft, fs, tt, ts in rels:
        x1, y1 = get_anchor(ft, fs)
        x2, y2 = get_anchor(tt, ts)
        d.add(Line(x1, y1, x2, y2, strokeColor=MUTED, strokeWidth=0.8,
                   strokeDashArray=[3, 2]))
        # Crow's-foot (many side)
        dx = 6 if x2 > x1 else -6
        d.add(Line(x2, y2, x2-dx, y2+4, strokeColor=DB_C, strokeWidth=1))
        d.add(Line(x2, y2, x2-dx, y2-4, strokeColor=DB_C, strokeWidth=1))
        d.add(Circle(x1+dx/2, y1, 3, fillColor=WHITE, strokeColor=DB_C, strokeWidth=1))

    # Legend
    lex = 8
    ley = 28
    d.add(Rect(lex-2, ley-14, 8, 8, fillColor=colors.HexColor('#c8341f'), strokeColor=None))
    _txt(d, lex+10, ley-10, 'PK = Primary Key', 6.5, INK)
    d.add(Rect(lex+100-2, ley-14, 8, 8, fillColor=colors.HexColor('#2060a0'), strokeColor=None))
    _txt(d, lex+112, ley-10, 'FK = Foreign Key', 6.5, INK)
    d.add(Line(lex+210, ley-10, lex+230, ley-10, strokeColor=MUTED, strokeWidth=0.8, strokeDashArray=[3,2]))
    _txt(d, lex+234, ley-10, '1-to-many relationship', 6.5, INK)

    return d


# ══════════════════════════════════════════════════════════════════════════════
#  DIAGRAM 7 — COMPONENT DEPENDENCY MAP
# ══════════════════════════════════════════════════════════════════════════════

def make_component_map(dw):
    DH = 400
    d = Drawing(dw, DH)
    d.add(Rect(0, 0, dw, DH, fillColor=PAPER, strokeColor=None))

    # File nodes: (x, y, w, h, filename, layer_color, deps_idx_list)
    # Positions in a grid layout
    nodes = [
        # (cx, cy, label, sub, fill)
        (dw/2,    DH-35,  'start.bat / start.sh',    'Entry point',             INK),
        (dw/2,    DH-100, 'app/main.py',              'FastAPI  ·  lifespan  ·  routes', FAST),
        (dw*0.2,  DH-175, 'app/database.py',          'SQLite init  ·  sample data', DB_C),
        (dw*0.5,  DH-175, 'app/agent.py',             'agent_session()  ·  LangChain', AI_C),
        (dw*0.8,  DH-175, 'app/models.py',            'Pydantic models', colors.HexColor('#3a3a3a')),
        (dw*0.35, DH-265, 'mcp_server/server.py',     'FastMCP  ·  9 tools', MCP_C),
        (dw*0.65, DH-265, 'data/ed_database.db',      'SQLite  ·  7 tables', DB_C),
        (dw*0.15, DH-350, 'frontend/index.html',      'Dashboard', FRONT),
        (dw*0.5,  DH-350, 'frontend/chat.html',       'AI Chat', FRONT),
        (dw*0.85, DH-350, 'frontend/intake.html',     'Intake Form', FRONT),
    ]

    bw, bh = 110, 40

    # Draw edges first
    edges = [
        (0, 1), (1, 2), (1, 3), (1, 4), (3, 5), (5, 6), (2, 6),
        (1, 7), (1, 8), (1, 9),
    ]
    for fi, ti in edges:
        x1, y1 = nodes[fi][0], nodes[fi][1] - bh/2
        x2, y2 = nodes[ti][0], nodes[ti][1] + bh/2
        _arr(d, x1, y1, x2, y2, MUTED, 1, None)

    for cx, cy, lbl, sub, fill in nodes:
        _box(d, cx-bw/2, cy-bh/2, bw, bh, fill=fill, lbl=lbl, sub=sub, fs=7.5, fs2=6.5)

    # Layer legend
    for i, (fill, label) in enumerate([
        (FRONT, 'Frontend'), (FAST, 'FastAPI'),
        (AI_C,  'AI/Agent'), (MCP_C, 'MCP'),
        (DB_C,  'Data'), (INK, 'Shell'),
    ]):
        lx = 12 + i*90
        d.add(Rect(lx, 10, 10, 10, fillColor=fill, strokeColor=None))
        _txt(d, lx+14, 13, label, 7, INK)

    return d


# ══════════════════════════════════════════════════════════════════════════════
#  DIAGRAM 8 — DEPLOYMENT ARCHITECTURE
# ══════════════════════════════════════════════════════════════════════════════

def make_deploy(dw):
    DH = 300
    d = Drawing(dw, DH)
    d.add(Rect(0, 0, dw, DH, fillColor=PAPER, strokeColor=None))

    # Windows host box
    d.add(Rect(8, 8, dw-16, DH-16, fillColor=BG, strokeColor=RULE, strokeWidth=1))
    _txt(d, dw/2, DH-20, 'Windows 11 Host  (or Linux / macOS)', 9, MUTED, 'middle', True)

    # Python env
    d.add(Rect(18, 160, dw-36, 100, fillColor=colors.white, strokeColor=RULE, strokeWidth=0.8))
    _txt(d, dw/2, 256, 'Python 3.14.4 Virtual Environment', 8.5, INK, 'middle', True)

    procs = [
        (dw*0.25, 175, 'Uvicorn ASGI', 'Port 8000\napp.main:app', FAST),
        (dw*0.75, 175, 'MCP Subprocess', 'Per-request\nmcp_server/server.py', MCP_C),
    ]
    for px, py, lbl, sub, fill in procs:
        _box(d, px-75, py, 150, 65, fill=fill, lbl=lbl, sub=sub, fs=9, fs2=7.5)
    _arr(d, dw*0.25+75, 207, dw*0.75-75, 207, ACCENT, 1.5, 'stdio spawn')
    _darr(d, dw*0.75-75, 220, dw*0.25+75, 220, colors.HexColor('#3d8b6e'), 'tool results')

    # File system
    d.add(Rect(18, 50, dw-36, 100, fillColor=colors.white, strokeColor=RULE, strokeWidth=0.8))
    _txt(d, dw/2, 146, 'File System', 8.5, INK, 'middle', True)
    fs_items = [
        (dw*0.15, 60, '.env', 'API key', MUTED),
        (dw*0.33, 60, 'app/', 'Python modules', FAST),
        (dw*0.52, 60, 'mcp_server/', 'MCP server', MCP_C),
        (dw*0.70, 60, 'frontend/', 'HTML pages', FRONT),
        (dw*0.87, 60, 'data/', 'ed_database.db', DB_C),
    ]
    for fx, fy, lbl, sub, fill in fs_items:
        _box(d, fx-40, fy, 78, 75, fill=fill, lbl=lbl, sub=sub, fs=8, fs2=6.5)

    # External cloud
    d.add(Rect(dw-110, DH-100, 100, 80, fillColor=colors.HexColor('#1e1e3a'),
               strokeColor=INK, strokeWidth=1))
    _txt(d, dw-60, DH-32, 'Anthropic', 8.5, WHITE, 'middle', True)
    _txt(d, dw-60, DH-44, 'Cloud API', 7, colors.HexColor('#aaaacc'), 'middle')
    _txt(d, dw-60, DH-56, 'claude-sonnet-4-6', 6.5, colors.HexColor('#aaaacc'), 'middle')
    _arr(d, dw*0.25+75, 230, dw-110, DH-60, colors.HexColor('#5555cc'), 1, 'HTTPS')
    _darr(d, dw-110, DH-70, dw*0.25+75, 235, colors.HexColor('#5555cc'), 'AI resp')

    # Startup command note
    _txt(d, 20, 25, 'Start command:  python -m uvicorn app.main:app --host 0.0.0.0 --port 8000', 7, INK)
    _txt(d, 20, 14, 'Env required:  ANTHROPIC_API_KEY=sk-ant-...', 7, ACCENT)

    return d


# ══════════════════════════════════════════════════════════════════════════════
#  API REFERENCE TABLE
# ══════════════════════════════════════════════════════════════════════════════

def make_api_table():
    data = [
        ['Method', 'Path', 'Handler', 'Description'],
        ['GET',  '/',                'main.py', 'Serve ED Dashboard (index.html)'],
        ['GET',  '/chat',            'main.py', 'Serve AI Chat interface (chat.html)'],
        ['GET',  '/intake',          'main.py', 'Serve Patient Intake form (intake.html)'],
        ['GET',  '/api/stats',       'main.py', 'Census stats: total patients, ESI distribution, critical count'],
        ['GET',  '/api/patients',    'main.py', 'Today\'s census: patients + vitals (2025-04-28 sample date)'],
        ['POST', '/api/chat',        'agent.py', 'AI chat: starts MCP session, calls LangChain agent, returns JSON'],
        ['POST', '/api/intake',      'main.py', 'Save intake: INSERT patient + triage_record; returns IDs'],
        ['GET',  '/docs',            'FastAPI', 'Auto-generated Swagger UI API documentation'],
        ['GET',  '/openapi.json',    'FastAPI', 'OpenAPI schema definition'],
    ]
    style = TableStyle([
        ('BACKGROUND', (0,0), (-1,0), INK),
        ('TEXTCOLOR',  (0,0), (-1,0), colors.white),
        ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE',   (0,0), (-1,-1), 8.5),
        ('FONTNAME',   (0,1), (0,-1), 'Courier-Bold'),
        ('BACKGROUND', (0,1), (0,-1), BG),
        ('TEXTCOLOR',  (0,1), (-1,-1), INK),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, BG]),
        ('GRID',       (0,0), (-1,-1), 0.5, RULE),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING',(0,0), (-1,-1), 6),
        ('TOPPADDING',  (0,0), (-1,-1), 5),
        ('BOTTOMPADDING',(0,0),(-1,-1), 5),
        ('VALIGN',     (0,0), (-1,-1), 'MIDDLE'),
    ])
    # Colour POST green, GET blue
    for r in range(1, len(data)):
        if data[r][0] == 'POST':
            style.add('TEXTCOLOR', (0,r), (0,r), colors.HexColor('#1a6a1a'))
        else:
            style.add('TEXTCOLOR', (0,r), (0,r), colors.HexColor('#1a1a8a'))
    return Table(data, colWidths=[1.1*cm, 4.2*cm, 2.8*cm, 8*cm], style=style)


# ══════════════════════════════════════════════════════════════════════════════
#  TECH STACK TABLE
# ══════════════════════════════════════════════════════════════════════════════

def make_tech_table():
    data = [
        ['Layer', 'Technology', 'Version', 'Purpose'],
        ['Runtime',   'Python',             '3.14.4',    'Application runtime'],
        ['Web',       'FastAPI',            '0.136.1',   'ASGI web framework + auto OpenAPI'],
        ['Web',       'Uvicorn',            '0.45.0',    'ASGI server (production-ready)'],
        ['AI',        'LangChain',          '1.2.15',    'LLM orchestration framework'],
        ['AI',        'LangChain-Anthropic','1.4.2',     'Claude Sonnet 4.6 integration'],
        ['AI',        'LangGraph',          '1.1.10',    'ReAct agent runtime (graph executor)'],
        ['AI',        'LangGraph-Prebuilt', '1.0.12',    'create_react_agent() helper'],
        ['MCP',       'mcp',               '1.27.0',    'Model Context Protocol Python SDK'],
        ['MCP',       'FastMCP',           '(built-in)', 'High-level MCP server builder'],
        ['MCP',       'langchain-mcp-adapters','0.2.2', 'MCP tools → LangChain tool interface'],
        ['AI Model',  'claude-sonnet-4-6', '—',         'Anthropic Claude: reasoning + tool use'],
        ['Data',      'SQLite',            '(built-in)', 'Embedded relational database'],
        ['HTTP',      'httpx',             '0.28.1',    'Async HTTP client'],
        ['Config',    'python-dotenv',     '1.2.2',     'Environment variable loading (.env)'],
        ['Validation','Pydantic',          '2.13.3',    'Request/response schema validation'],
        ['Files',     'aiofiles',          '25.1.0',    'Async static file serving'],
        ['Fonts',     'Google Fonts',      '—',         'Fraunces / JetBrains Mono / Inter Tight'],
        ['Docs',      'ReportLab',         '4.4.10',    'PDF generation (this document)'],
    ]
    layer_colors = {
        'Runtime': FAST, 'Web': FAST, 'AI': AI_C, 'MCP': MCP_C,
        'AI Model': AI_C, 'Data': DB_C, 'HTTP': FAST, 'Config': INK,
        'Validation': INK, 'Files': FAST, 'Fonts': FRONT, 'Docs': MUTED,
    }
    style = TableStyle([
        ('BACKGROUND',  (0,0), (-1,0), INK),
        ('TEXTCOLOR',   (0,0), (-1,0), colors.white),
        ('FONTNAME',    (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE',    (0,0), (-1,-1), 8.5),
        ('GRID',        (0,0), (-1,-1), 0.5, RULE),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING',(0,0), (-1,-1), 6),
        ('TOPPADDING',  (0,0), (-1,-1), 4),
        ('BOTTOMPADDING',(0,0),(-1,-1), 4),
        ('VALIGN',      (0,0), (-1,-1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, BG]),
    ])
    for r in range(1, len(data)):
        layer = data[r][0]
        c = layer_colors.get(layer, INK)
        style.add('TEXTCOLOR',  (0,r), (0,r), c)
        style.add('FONTNAME',   (0,r), (0,r), 'Helvetica-Bold')
        style.add('FONTNAME',   (1,r), (1,r), 'Courier-Bold')
        style.add('TEXTCOLOR',  (2,r), (2,r), MUTED)
    return Table(data, colWidths=[2*cm, 4.2*cm, 2.6*cm, 7.4*cm], style=style)


# ══════════════════════════════════════════════════════════════════════════════
#  MCP TOOLS TABLE
# ══════════════════════════════════════════════════════════════════════════════

def make_tools_table():
    data = [
        ['Tool Name', 'Input Parameters', 'Returns', 'Description'],
        ['list_tables',           '—',                           'JSON list', 'All table names in the ED database'],
        ['describe_table',        'table_name: str',             'JSON obj',  'Column schema + current row count'],
        ['execute_query',         'sql: str  (SELECT only)',     'JSON rows', 'Arbitrary read-only SQL query'],
        ['get_patient_by_mrn',    'mrn: str',                    'JSON obj',  'Full record: demographics, allergies, meds, history, visits'],
        ['get_todays_patients',   'date: str  (YYYY-MM-DD)',     'JSON list', 'All patients for a date, sorted by ESI then time'],
        ['get_triage_statistics', 'date: str  (optional)',       'JSON obj',  'ESI distribution, arrival modes, total census'],
        ['get_critical_patients', '—',                           'JSON list', 'ESI 1-2 patients with vitals and allergy flags'],
        ['search_patients',       'query: str',                  'JSON list', 'Name / MRN fuzzy search with visit history'],
        ['insert_patient_intake', '15 fields (mrn, name, dob…)', 'JSON obj',  'Insert new patient and triage record into DB'],
    ]
    style = TableStyle([
        ('BACKGROUND',   (0,0), (-1,0), MCP_C),
        ('TEXTCOLOR',    (0,0), (-1,0), colors.white),
        ('FONTNAME',     (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE',     (0,0), (-1,-1), 8),
        ('FONTNAME',     (0,1), (0,-1), 'Courier-Bold'),
        ('TEXTCOLOR',    (0,1), (0,-1), colors.HexColor('#7c3a00')),
        ('FONTNAME',     (1,1), (2,-1), 'Courier'),
        ('TEXTCOLOR',    (1,1), (2,-1), colors.HexColor('#204060')),
        ('GRID',         (0,0), (-1,-1), 0.5, RULE),
        ('LEFTPADDING',  (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING',   (0,0), (-1,-1), 4),
        ('BOTTOMPADDING',(0,0), (-1,-1), 4),
        ('VALIGN',       (0,0), (-1,-1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, BG]),
    ])
    return Table(data, colWidths=[3.6*cm, 3.8*cm, 1.8*cm, 7*cm], style=style)


# ══════════════════════════════════════════════════════════════════════════════
#  DB SCHEMA TABLE
# ══════════════════════════════════════════════════════════════════════════════

def make_schema_table():
    data = [
        ['Table', 'Rows', 'Key Columns', 'Relationships'],
        ['patients',          '10', 'id PK, mrn UNIQUE, first_name, last_name, dob, age, biological_sex, phone, address, language', 'Root — referenced by all other tables'],
        ['triage_records',    '12', 'id PK, patient_id FK, mrn, arrival_date/time, arrival_mode, chief_complaint, esi_level, disposition, triage_nurse', 'patient_id → patients.id'],
        ['vital_signs',       '12', 'id PK, triage_id FK, patient_id FK, reading_number, blood_pressure, heart_rate, respiratory_rate, temperature, spo2, gcs', 'triage_id → triage_records.id'],
        ['allergies',          '8', 'id PK, patient_id FK, allergen, reaction_type, severity, notes', 'patient_id → patients.id'],
        ['medications',       '19', 'id PK, patient_id FK, medication_name, dose, frequency, route, last_taken', 'patient_id → patients.id'],
        ['medical_history',   '19', 'id PK, patient_id FK, condition_name, category (PMH/PSH), year_diagnosed', 'patient_id → patients.id'],
        ['emergency_contacts','10', 'id PK, patient_id FK, name, relationship, phone', 'patient_id → patients.id'],
    ]
    style = TableStyle([
        ('BACKGROUND',  (0,0), (-1,0), DB_C),
        ('TEXTCOLOR',   (0,0), (-1,0), colors.white),
        ('FONTNAME',    (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE',    (0,0), (-1,-1), 8),
        ('FONTNAME',    (0,1), (0,-1), 'Courier-Bold'),
        ('TEXTCOLOR',   (0,1), (0,-1), DB_C),
        ('FONTNAME',    (1,1), (1,-1), 'Helvetica-Bold'),
        ('TEXTCOLOR',   (1,1), (1,-1), ACCENT),
        ('FONTSIZE',    (1,0), (1,-1), 9),
        ('GRID',        (0,0), (-1,-1), 0.5, RULE),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING',(0,0), (-1,-1), 5),
        ('TOPPADDING',  (0,0), (-1,-1), 4),
        ('BOTTOMPADDING',(0,0),(-1,-1), 4),
        ('VALIGN',      (0,0), (-1,-1), 'TOP'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, BG]),
        ('WORDWRAP', (2,1), (2,-1), True),
    ])
    return Table(data, colWidths=[3.4*cm, 1*cm, 7.6*cm, 4.2*cm], style=style, repeatRows=1)


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN DOCUMENT BUILDER
# ══════════════════════════════════════════════════════════════════════════════

def build_pdf(out_path: str):
    doc = SimpleDocTemplate(
        out_path, pagesize=A4,
        leftMargin=1.8*cm, rightMargin=1.8*cm,
        topMargin=2*cm, bottomMargin=1.8*cm,
        title='ED AI Agent — Technical Architecture',
        author='Adviava Regional Medical Center',
        subject='Technical Architecture & Integration Reference',
    )
    DW = doc.width   # usable page width

    def H(text, style=S_H2):   return Paragraph(text, style)
    def P(text):                return Paragraph(text, S_BODY)
    def C(text):                return Paragraph(text, S_CAP)
    def sp(h=8):                return Spacer(1, h)
    def hr():                   return HRFlowable(width='100%', color=RULE, thickness=0.7, spaceAfter=8)

    story = []

    # ── COVER ────────────────────────────────────────────────────────────────
    story.append(make_cover(DW))
    story.append(PageBreak())

    # ── TABLE OF CONTENTS ─────────────────────────────────────────────────────
    story.append(H('Table of Contents', S_H1))
    story.append(hr())
    toc = [
        ('1.', 'System Architecture Overview',          '3'),
        ('2.', 'AI Chat Request — Sequence Diagram',    '4'),
        ('3.', 'Patient Intake — Data Flow',            '5'),
        ('4.', 'MCP Integration — Tool Chain Detail',   '6'),
        ('5.', 'Component Dependency Map',              '7'),
        ('6.', 'Database Entity-Relationship Diagram',  '8'),
        ('7.', 'Deployment Architecture',               '9'),
        ('8.', 'REST API Reference',                    '10'),
        ('9.', 'MCP Tool Reference',                    '11'),
        ('10.','Database Schema Reference',             '12'),
        ('11.','Technology Stack',                      '13'),
    ]
    toc_data = [[Paragraph(n, S_TOCN), Paragraph(t, S_TOC), Paragraph(p, S_TOC)] for n, t, p in toc]
    toc_table = Table(toc_data, colWidths=[1*cm, 12*cm, 2*cm])
    toc_table.setStyle(TableStyle([
        ('LINEBELOW', (0,0), (-1,-1), 0.3, RULE),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (2,0), (2,-1), 'RIGHT'),
    ]))
    story.append(toc_table)
    story.append(sp(16))

    story.append(H('About This Document', S_H3))
    story.append(P(
        'This document describes the complete technical architecture of the ED AI Agent platform '
        'built for Adviava Regional Medical Center\'s Emergency Department. The system integrates a '
        'LangChain ReAct agent powered by Claude Sonnet 4.6 with a MySQL-compatible MCP (Model '
        'Context Protocol) server that provides the AI direct access to patient records, triage '
        'data, vital signs, medications, and allergy records stored in a relational database.'
    ))
    story.append(P(
        'The platform is accessible via three web interfaces: a real-time census dashboard, a '
        'conversational AI assistant for clinical queries, and a structured patient intake form '
        'that writes directly to the database. All AI tool calls are mediated by the MCP protocol '
        'using a stdio subprocess transport, giving full observability and auditability of every '
        'database operation the agent performs.'
    ))
    story.append(PageBreak())

    # ── §1  SYSTEM ARCHITECTURE OVERVIEW ──────────────────────────────────────
    story.append(H('1   System Architecture Overview', S_H1))
    story.append(hr())
    story.append(P(
        'The five-layer stack shows how a browser request flows through FastAPI, the LangChain '
        'agent, the MCP client/server pair, and ultimately the SQLite database. Direct SQL paths '
        '(for dashboard and patient list endpoints) bypass the AI agent to reduce latency.'
    ))
    story.append(sp(6))
    story.append(make_arch_overview(DW))
    story.append(C('Figure 1 — High-Level System Architecture  ·  Five-layer stack with request routing'))
    story.append(PageBreak())

    # ── §2  CHAT SEQUENCE ─────────────────────────────────────────────────────
    story.append(H('2   AI Chat Request — Sequence Diagram', S_H1))
    story.append(hr())
    story.append(P(
        'When a user submits a chat message, FastAPI calls the LangChain ReAct agent which '
        'reasons about which MCP tool to invoke, calls it via the stdio subprocess, receives '
        'structured data back, optionally calls the Anthropic API for reasoning, and returns a '
        'final formatted clinical response. The MCP subprocess is created fresh per request '
        'inside an <i>agent_session()</i> async context manager.'
    ))
    story.append(sp(6))
    story.append(make_chat_sequence(DW))
    story.append(C('Figure 2 — Chat Request Sequence  ·  7 actors  ·  Solid arrows = forward, dashed = return'))
    story.append(PageBreak())

    # ── §3  INTAKE FLOW ───────────────────────────────────────────────────────
    story.append(H('3   Patient Intake — Data Flow Diagram', S_H1))
    story.append(hr())
    story.append(P(
        'The intake form collects patient demographics, chief complaint, vitals, and triage '
        'level. On submit it sends a JSON POST to <i>/api/intake</i>. FastAPI validates with '
        'Pydantic, checks if the MRN already exists (upsert logic), inserts the patient and '
        'triage records, and redirects the browser to the dashboard.'
    ))
    story.append(sp(6))
    story.append(make_intake_flow(DW))
    story.append(C('Figure 3 — Patient Intake Flow  ·  Form submission → validation → dual DB insert'))
    story.append(PageBreak())

    # ── §4  MCP INTEGRATION ───────────────────────────────────────────────────
    story.append(H('4   MCP Integration — Tool Chain Detail', S_H1))
    story.append(hr())
    story.append(P(
        'The Model Context Protocol (MCP) server runs as a Python subprocess communicating via '
        'JSON-RPC 2.0 over stdio. The LangChain <i>MultiServerMCPClient</i> opens a session, '
        'fetches the 9 tool descriptors, and wraps them as standard LangChain <i>BaseTool</i> '
        'objects. When the ReAct agent decides to call a tool, the call is forwarded through '
        'the MCP protocol to the FastMCP server which executes the SQL and returns JSON.'
    ))
    story.append(sp(6))
    story.append(make_mcp_detail(DW))
    story.append(C('Figure 4 — MCP Integration  ·  FastMCP stdio  ·  9 tools  ·  JSON-RPC 2.0'))
    story.append(PageBreak())

    # ── §5  COMPONENT MAP ─────────────────────────────────────────────────────
    story.append(H('5   Component Dependency Map', S_H1))
    story.append(hr())
    story.append(P(
        'This diagram shows how the Python module files and static assets depend on each other. '
        'The entry point (<i>start.bat</i>) launches Uvicorn which imports <i>app/main.py</i>. '
        'Main imports database (for init), agent (for MCP), and models (for validation). '
        'The agent module spawns <i>mcp_server/server.py</i> as a subprocess when a chat '
        'request arrives. All three frontend HTML pages are served as static files.'
    ))
    story.append(sp(6))
    story.append(make_component_map(DW))
    story.append(C('Figure 5 — Component Dependency Map  ·  File-level dependencies'))
    story.append(PageBreak())

    # ── §6  ER DIAGRAM ────────────────────────────────────────────────────────
    story.append(H('6   Database Entity-Relationship Diagram', S_H1))
    story.append(hr())
    story.append(P(
        'Seven tables form the data model. <b>patients</b> is the root entity; all other '
        'tables reference it via <i>patient_id</i>. <b>triage_records</b> captures each ED '
        'visit, and <b>vital_signs</b> stores multiple readings per visit. '
        '<font color="#c8341f">Red</font> = Primary Key, '
        '<font color="#2060a0">Blue</font> = Foreign Key.'
    ))
    story.append(sp(6))
    story.append(make_er_diagram(DW))
    story.append(C('Figure 6 — Entity-Relationship Diagram  ·  7 tables  ·  Crow’s-foot notation'))
    story.append(PageBreak())

    # ── §7  DEPLOYMENT ────────────────────────────────────────────────────────
    story.append(H('7   Deployment Architecture', S_H1))
    story.append(hr())
    story.append(P(
        'The application runs entirely on a single host machine (Windows / Linux / macOS). '
        'Uvicorn serves the FastAPI app on port 8000. The MCP server spawns as a child '
        'process on each AI chat request and terminates when the response is complete. '
        'The only external dependency at runtime is the Anthropic Cloud API.'
    ))
    story.append(sp(6))
    story.append(make_deploy(DW))
    story.append(C('Figure 7 — Deployment Architecture  ·  Single host  ·  Anthropic Cloud for AI'))
    story.append(sp(12))

    story.append(H('Startup Sequence', S_H3))
    steps_data = [
        ['Step', 'Action', 'File'],
        ['1', 'Run start.bat (Windows) or ./start.sh (Linux/Mac)', 'start.bat'],
        ['2', 'pip install -r requirements.txt (if needed)', 'requirements.txt'],
        ['3', 'Uvicorn starts FastAPI — lifespan() runs', 'app/main.py'],
        ['4', 'init_database() creates SQLite + sample data', 'app/database.py'],
        ['5', 'FastAPI serves / /chat /intake /api/* on port 8000', 'app/main.py'],
        ['6', 'Per chat request: agent_session() spawns MCP subprocess', 'app/agent.py'],
        ['7', 'MCP subprocess runs, exposes 9 tools, handles calls, exits', 'mcp_server/server.py'],
    ]
    st = TableStyle([
        ('BACKGROUND', (0,0), (-1,0), INK),
        ('TEXTCOLOR', (0,0), (-1,0), WHITE),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8.5),
        ('GRID', (0,0), (-1,-1), 0.5, RULE),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [WHITE, BG]),
        ('FONTNAME', (0,1), (0,-1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0,1), (0,-1), ACCENT),
        ('FONTNAME', (2,1), (2,-1), 'Courier'),
        ('TEXTCOLOR', (2,1), (2,-1), MCP_C),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ])
    story.append(Table(steps_data, colWidths=[1*cm, 11*cm, 4.2*cm], style=st))
    story.append(PageBreak())

    # ── §8  API REFERENCE ─────────────────────────────────────────────────────
    story.append(H('8   REST API Reference', S_H1))
    story.append(hr())
    story.append(P('All endpoints are served by <i>app/main.py</i> on <b>http://localhost:8000</b>. '
                   'Swagger UI available at <b>/docs</b>. All API bodies are JSON.'))
    story.append(sp(6))
    story.append(make_api_table())
    story.append(C('Table 1 — REST API Endpoints'))
    story.append(sp(14))

    story.append(H('Request / Response Examples', S_H3))
    examples = [
        ('POST /api/chat', '{"message": "List all ESI 1 patients with vitals"}',
         '{"response": "## ESI 1 — CRITICAL\\n...", "tool_calls": ["get_critical_patients"]}'),
        ('POST /api/intake', '{"mrn":"MRN-2025-012","first_name":"Jane","last_name":"Doe","dob":"1985-03-22","age":40,"biological_sex":"Female","phone":"(617)555-1234","address":"...","language":"English","chief_complaint":"Chest pain 10/10","esi_level":2,"arrival_mode":"Walk-in / Ambulatory","arrival_date":"2025-04-29","arrival_time":"09:00","triage_nurse":"RN Smith","disposition":"Main ED — Bay assignment"}',
         '{"success": true, "patient_id": 12, "triage_id": 14, "error": null}'),
        ('GET /api/stats', '—',
         '{"total_patients":11,"today_census":10,"critical_patients":5,"esi_distribution":[...]}'),
    ]
    for ep, req, resp in examples:
        story.append(Paragraph(f'<b>{ep}</b>', S_H3))
        if req != '—':
            story.append(Paragraph('Request body:', S_BODY))
            story.append(Paragraph(req, S_MONO))
        story.append(Paragraph('Response:', S_BODY))
        story.append(Paragraph(resp, S_MONO))
        story.append(sp(6))
    story.append(PageBreak())

    # ── §9  MCP TOOL REFERENCE ────────────────────────────────────────────────
    story.append(H('9   MCP Tool Reference', S_H1))
    story.append(hr())
    story.append(P('Each tool is defined with the <i>@mcp.tool()</i> decorator in '
                   '<i>mcp_server/server.py</i>. The LangChain agent discovers them via '
                   '<i>load_mcp_tools(session)</i> at session initialization. '
                   'All tools operate read-only except <i>insert_patient_intake</i>.'))
    story.append(sp(6))
    story.append(make_tools_table())
    story.append(C('Table 2 — MCP Tools  (mcp_server/server.py)  ·  FastMCP 1.27.0  ·  stdio transport'))
    story.append(PageBreak())

    # ── §10  DB SCHEMA ────────────────────────────────────────────────────────
    story.append(H('10   Database Schema Reference', S_H1))
    story.append(hr())
    story.append(P('SQLite database at <b>data/ed_database.db</b> — initialized automatically on '
                   'first startup by <i>app/database.py:init_database()</i>. '
                   'All tables use INTEGER PRIMARY KEY AUTOINCREMENT. '
                   'Schema is MySQL-compatible (all SQL queries used by the MCP server run '
                   'identically on MySQL by changing the connection string).'))
    story.append(sp(6))
    story.append(make_schema_table())
    story.append(C('Table 3 — Database Schema  ·  data/ed_database.db  ·  SQLite (MySQL-compatible SQL)'))
    story.append(PageBreak())

    # ── §11  TECH STACK ───────────────────────────────────────────────────────
    story.append(H('11   Technology Stack', S_H1))
    story.append(hr())
    story.append(P('All Python packages are listed in <b>requirements.txt</b> and installable '
                   'via <i>pip install -r requirements.txt</i>. No Docker or external services '
                   'are required to run the application locally.'))
    story.append(sp(6))
    story.append(make_tech_table())
    story.append(C('Table 4 — Complete Technology Stack with Versions'))
    story.append(sp(16))

    # Footer note
    story.append(HRFlowable(width='100%', color=ACCENT, thickness=1.5, spaceAfter=8))
    story.append(Paragraph(
        f'<b>ED AI Agent Platform</b>  ·  Adviava Regional Medical Center  ·  '
        f'Version 1.0  ·  Generated {datetime.now().strftime("%B %d, %Y at %H:%M")}',
        _ps(fontName='Helvetica', fontSize=8, textColor=MUTED, alignment=TA_CENTER)
    ))
    story.append(Paragraph(
        'Architecture: FastAPI 0.136 + LangChain 1.2 + LangGraph 1.1 + FastMCP 1.27 + Claude Sonnet 4.6',
        _ps(fontName='Courier', fontSize=7.5, textColor=MUTED, alignment=TA_CENTER)
    ))

    doc.build(story, onFirstPage=_on_cover, onLaterPages=_on_page)
    print(f'PDF saved: {out_path}')


if __name__ == '__main__':
    out = Path('ED_AI_Agent_Architecture.pdf')
    build_pdf(str(out))
