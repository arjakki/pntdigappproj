"""
Generate Adviava ED AI Agent — Prompt Template Reference PDF
"""
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate, Frame, HRFlowable, NextPageTemplate, PageBreak,
    PageTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether,
)
from reportlab.platypus.flowables import Flowable
from reportlab.lib.colors import HexColor

# ── Brand palette ──────────────────────────────────────────────────────────────
NAVY      = HexColor("#0D2B4E")
TEAL      = HexColor("#007C91")
TEAL_LITE = HexColor("#E0F4F7")
MID_GREY  = HexColor("#4A5568")
LIGHT_BG  = HexColor("#F7FAFC")
CODE_BG   = HexColor("#1E2D3D")
CODE_FG   = HexColor("#A8D8EA")
RED       = HexColor("#C8341F")
GOLD      = HexColor("#D4A017")
GREEN     = HexColor("#276749")
WHITE     = colors.white

W, H = A4
MARGIN     = 18 * mm
CONTENT_W  = W - 2 * MARGIN


# ── Styles ─────────────────────────────────────────────────────────────────────
def make_styles():
    def S(name, **kw):
        return ParagraphStyle(name, **kw)

    return {
        "cover_title": S("cover_title",
            fontName="Helvetica-Bold", fontSize=26, textColor=WHITE,
            leading=34, alignment=TA_LEFT, spaceAfter=8),
        "cover_sub": S("cover_sub",
            fontName="Helvetica", fontSize=13, textColor=HexColor("#B0C8D8"),
            leading=18, alignment=TA_LEFT, spaceAfter=6),
        "cover_org": S("cover_org",
            fontName="Helvetica-Bold", fontSize=11, textColor=GOLD,
            leading=15, alignment=TA_LEFT),
        "cover_date": S("cover_date",
            fontName="Helvetica", fontSize=9.5, textColor=HexColor("#90A8B8"),
            alignment=TA_LEFT),
        "h1": S("h1",
            fontName="Helvetica-Bold", fontSize=15, textColor=NAVY,
            spaceBefore=16, spaceAfter=5, leading=20),
        "h2": S("h2",
            fontName="Helvetica-Bold", fontSize=11, textColor=TEAL,
            spaceBefore=12, spaceAfter=4, leading=15),
        "h3": S("h3",
            fontName="Helvetica-Bold", fontSize=9.5, textColor=NAVY,
            spaceBefore=8, spaceAfter=3, leading=13),
        "body": S("body",
            fontName="Helvetica", fontSize=9.5, textColor=MID_GREY,
            leading=15, alignment=TA_JUSTIFY, spaceAfter=4),
        "bullet": S("bullet",
            fontName="Helvetica", fontSize=9.5, textColor=MID_GREY,
            leading=15, leftIndent=14, bulletIndent=4, spaceAfter=2),
        "bold_bullet": S("bold_bullet",
            fontName="Helvetica-Bold", fontSize=9.5, textColor=NAVY,
            leading=15, leftIndent=14, bulletIndent=4, spaceAfter=2),
        "code": S("code",
            fontName="Courier", fontSize=8, textColor=CODE_FG,
            leading=13, leftIndent=10, spaceAfter=2, backColor=CODE_BG),
        "code_label": S("code_label",
            fontName="Helvetica-Bold", fontSize=7.5, textColor=WHITE,
            leading=11, alignment=TA_LEFT),
        "th": S("th",
            fontName="Helvetica-Bold", fontSize=8.5, textColor=WHITE,
            alignment=TA_CENTER, leading=12),
        "td": S("td",
            fontName="Helvetica", fontSize=8.5, textColor=MID_GREY,
            alignment=TA_LEFT, leading=13),
        "td_bold": S("td_bold",
            fontName="Helvetica-Bold", fontSize=8.5, textColor=NAVY,
            alignment=TA_LEFT, leading=13),
        "td_code": S("td_code",
            fontName="Courier", fontSize=8, textColor=TEAL,
            alignment=TA_LEFT, leading=13),
        "callout": S("callout",
            fontName="Helvetica-Bold", fontSize=10, textColor=NAVY,
            leading=15, alignment=TA_CENTER),
        "italic": S("italic",
            fontName="Helvetica-Oblique", fontSize=8.5, textColor=MID_GREY,
            leading=13, alignment=TA_CENTER),
        "footer": S("footer",
            fontName="Helvetica", fontSize=7.5, textColor=HexColor("#8090A0"),
            alignment=TA_CENTER),
        "rule_label": S("rule_label",
            fontName="Helvetica-Bold", fontSize=9, textColor=WHITE,
            leading=12, alignment=TA_LEFT),
        "rule_body": S("rule_body",
            fontName="Helvetica", fontSize=9, textColor=MID_GREY,
            leading=14, alignment=TA_JUSTIFY),
    }


# ── Page backgrounds ───────────────────────────────────────────────────────────
def cover_background(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(NAVY)
    canvas.rect(0, 0, W, H, fill=1, stroke=0)
    canvas.setFillColor(TEAL)
    canvas.rect(0, 0, W, 18 * mm, fill=1, stroke=0)
    canvas.setFillColor(HexColor("#0A2240"))
    canvas.rect(W - 55 * mm, 0, 55 * mm, H, fill=1, stroke=0)
    canvas.setFillColor(GOLD)
    canvas.rect(0, H - 4 * mm, W, 4 * mm, fill=1, stroke=0)
    canvas.setStrokeColor(HexColor("#1A3D60"))
    canvas.setLineWidth(0.5)
    for i in range(0, int(H) + 200, 40):
        canvas.line(W - 55 * mm, i, W, i - 55 * mm)
    canvas.restoreState()


def inner_background(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(NAVY)
    canvas.rect(0, H - 14 * mm, W, 14 * mm, fill=1, stroke=0)
    canvas.setFont("Helvetica-Bold", 8)
    canvas.setFillColor(HexColor("#90A8C8"))
    canvas.drawString(MARGIN, H - 9 * mm, "ADVIAVA REGIONAL MEDICAL CENTER")
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(HexColor("#607080"))
    canvas.drawRightString(W - MARGIN, H - 9 * mm, "ED AI Agent — Prompt Template Reference")
    canvas.setFillColor(TEAL)
    canvas.rect(0, 0, 3 * mm, H - 14 * mm, fill=1, stroke=0)
    canvas.setStrokeColor(HexColor("#CBD5E0"))
    canvas.setLineWidth(0.5)
    canvas.line(MARGIN, 12 * mm, W - MARGIN, 12 * mm)
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(HexColor("#8090A0"))
    canvas.drawString(MARGIN, 7 * mm, "Adviava Regional Medical Center  |  Confidential — For Internal Use Only")
    canvas.drawRightString(W - MARGIN, 7 * mm, f"Page {doc.page}")
    canvas.restoreState()


# ── Helpers ────────────────────────────────────────────────────────────────────
def sp(n=6):   return Spacer(1, n)
def hr():      return HRFlowable(width="100%", thickness=0.5, color=HexColor("#CBD5E0"),
                                  spaceAfter=4, spaceBefore=4)
def P(t, s):   return Paragraph(t, s)
def bullet(t, S, bold=False):
    return Paragraph(f"• {t}", S["bold_bullet" if bold else "bullet"])


def styled_table(headers, rows, S, col_widths=None, first_col_code=False):
    data = [[Paragraph(h, S["th"]) for h in headers]]
    for row in rows:
        styled = []
        for j, cell in enumerate(row):
            if j == 0 and first_col_code:
                styled.append(Paragraph(str(cell), S["td_code"]))
            elif j == 0:
                styled.append(Paragraph(str(cell), S["td_bold"]))
            else:
                styled.append(Paragraph(str(cell), S["td"]))
        data.append(styled)

    if col_widths is None:
        col_widths = [CONTENT_W / len(headers)] * len(headers)

    ts = TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  TEAL),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_BG]),
        ("GRID",          (0, 0), (-1, -1), 0.4, HexColor("#CBD5E0")),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 7),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 7),
        ("LINEBELOW",     (0, 0), (-1, 0),  1.2, TEAL),
    ])
    return Table(data, colWidths=col_widths, style=ts, hAlign="LEFT")


class CodeBlock(Flowable):
    """Dark-background monospace block for prompt text."""
    def __init__(self, lines, width=None, padding=10):
        super().__init__()
        self.lines = lines
        self.width = width or CONTENT_W
        self.padding = padding
        self.line_h = 13
        self.height = len(lines) * self.line_h + 2 * padding

    def draw(self):
        self.canv.setFillColor(CODE_BG)
        self.canv.roundRect(0, 0, self.width, self.height, 4, fill=1, stroke=0)
        self.canv.setFont("Courier", 7.5)
        self.canv.setFillColor(CODE_FG)
        y = self.height - self.padding - self.line_h + 3
        for line in self.lines:
            # colour keywords
            if line.startswith("##"):
                self.canv.setFillColor(GOLD)
            elif line.startswith("- `") or line.startswith("| "):
                self.canv.setFillColor(HexColor("#90D0E0"))
            elif line.startswith("**") or line.startswith("You are"):
                self.canv.setFillColor(WHITE)
            else:
                self.canv.setFillColor(CODE_FG)
            self.canv.drawString(self.padding, y, line)
            y -= self.line_h


class SectionBadge(Flowable):
    """Coloured section header pill."""
    def __init__(self, text, colour=TEAL, width=None, height=22):
        super().__init__()
        self.text = text
        self.colour = colour
        self.width = width or CONTENT_W
        self.height = height

    def draw(self):
        self.canv.setFillColor(self.colour)
        self.canv.roundRect(0, 0, self.width, self.height, 4, fill=1, stroke=0)
        self.canv.setFont("Helvetica-Bold", 9.5)
        self.canv.setFillColor(WHITE)
        self.canv.drawString(10, 7, self.text)


class RuleCard(Flowable):
    """Bordered card for a single safety or format rule."""
    def __init__(self, number, label, body, accent=TEAL, width=None):
        super().__init__()
        self.number = str(number)
        self.label  = label
        self.body   = body
        self.accent = accent
        self.width  = width or CONTENT_W
        self.height = 52

    def draw(self):
        from reportlab.lib.utils import simpleSplit
        self.canv.setFillColor(LIGHT_BG)
        self.canv.roundRect(0, 0, self.width, self.height, 4, fill=1, stroke=0)
        # accent left bar
        self.canv.setFillColor(self.accent)
        self.canv.roundRect(0, 0, 5, self.height, 3, fill=1, stroke=0)
        # number circle
        cx = 20
        self.canv.setFillColor(self.accent)
        self.canv.circle(cx, self.height - 16, 8, fill=1, stroke=0)
        self.canv.setFont("Helvetica-Bold", 8)
        self.canv.setFillColor(WHITE)
        self.canv.drawCentredString(cx, self.height - 19, self.number)
        # label
        self.canv.setFont("Helvetica-Bold", 9)
        self.canv.setFillColor(self.accent)
        self.canv.drawString(34, self.height - 19, self.label)
        # body text
        self.canv.setFont("Helvetica", 8.5)
        self.canv.setFillColor(MID_GREY)
        lines = simpleSplit(self.body, "Helvetica", 8.5, self.width - 42)
        y = self.height - 33
        for line in lines[:3]:
            self.canv.drawString(34, y, line)
            y -= 12


# ── Cover ──────────────────────────────────────────────────────────────────────
def make_cover(S):
    story = []
    story.append(Spacer(1, 60 * mm))
    story.append(P("Prompt Template Reference", S["cover_sub"]))
    story.append(sp(4))
    story.append(P("ED AI Agent", S["cover_title"]))
    story.append(P("Clinical Decision Support System", S["cover_title"]))
    story.append(sp(10))
    story.append(P("Adviava Regional Medical Center", S["cover_org"]))
    story.append(P("Emergency Department", S["cover_org"]))
    story.append(sp(18))

    class CoverStats(Flowable):
        def __init__(self, items, w, h=50):
            super().__init__()
            self.items = items
            self.width = w
            self.height = h

        def draw(self):
            n = len(self.items)
            cw = self.width / n
            self.canv.setFillColor(HexColor("#0A2240"))
            self.canv.roundRect(0, 0, self.width, self.height, 5, fill=1, stroke=0)
            for i, (val, lbl) in enumerate(self.items):
                x = i * cw
                if i > 0:
                    self.canv.setStrokeColor(HexColor("#1A3D60"))
                    self.canv.setLineWidth(0.5)
                    self.canv.line(x, 8, x, self.height - 8)
                self.canv.setFont("Helvetica-Bold", 14)
                self.canv.setFillColor(GOLD)
                self.canv.drawCentredString(x + cw / 2, 24, val)
                self.canv.setFont("Helvetica", 7)
                self.canv.setFillColor(HexColor("#90A8B8"))
                self.canv.drawCentredString(x + cw / 2, 11, lbl)

    story.append(CoverStats([
        ("2", "Prompt Templates"),
        ("9", "MCP Tools Covered"),
        ("5", "ESI Triage Levels"),
        ("5", "Safety Rules"),
    ], CONTENT_W))
    story.append(sp(22))
    story.append(P("April 2026  |  For Internal Use", S["cover_date"]))
    story.append(PageBreak())
    return story


# ── Introduction ───────────────────────────────────────────────────────────────
def make_intro(S):
    story = []
    story.append(P("Introduction", S["h1"]))
    story.append(hr())
    story.append(sp(4))
    story.append(P(
        "This document is the definitive reference for the two prompt templates that govern AI "
        "behaviour in the Adviava ED AI Agent system:",
        S["body"]))
    story.append(sp(4))

    templates = [
        ("CLAUDE.md",
         "Project context prompt loaded by Claude Code (the developer AI). Describes the "
         "codebase architecture, key files, database schema, MCP tools, dev commands, and "
         "coding conventions so that any AI-assisted development session starts with full "
         "project awareness.",
         TEAL),
        ("SYSTEM_PROMPT  (app/agent.py)",
         "Runtime prompt injected into every chat request. Defines the agent's clinical role, "
         "tool routing strategy, ESI and vital-sign reference tables, response formatting rules, "
         "and hard safety guardrails that prevent the AI from making autonomous clinical decisions.",
         NAVY),
    ]

    for name, desc, colour in templates:
        class TemplateCard(Flowable):
            def __init__(self, n, d, c, w=CONTENT_W):
                super().__init__()
                self.n = n; self.d = d; self.c = c
                self.width = w; self.height = 56

            def draw(self):
                from reportlab.lib.utils import simpleSplit
                self.canv.setFillColor(LIGHT_BG)
                self.canv.roundRect(0, 0, self.width, self.height, 5, fill=1, stroke=0)
                self.canv.setFillColor(self.c)
                self.canv.roundRect(0, 0, 6, self.height, 3, fill=1, stroke=0)
                self.canv.setFont("Courier-Bold", 9)
                self.canv.setFillColor(self.c)
                self.canv.drawString(16, self.height - 17, self.n)
                self.canv.setFont("Helvetica", 8.5)
                self.canv.setFillColor(MID_GREY)
                lines = simpleSplit(self.d, "Helvetica", 8.5, self.width - 24)
                y = self.height - 31
                for line in lines[:4]:
                    self.canv.drawString(16, y, line)
                    y -= 12

        story.append(TemplateCard(name, desc, colour))
        story.append(sp(8))

    story.append(sp(4))
    story.append(P(
        "Together these two templates ensure consistent, safe, and clinically appropriate behaviour "
        "whether the AI is helping a developer modify the codebase or helping a nurse query patient records.",
        S["body"]))
    story.append(sp(8))
    story.append(PageBreak())
    return story


# ── Section 1 — CLAUDE.md ─────────────────────────────────────────────────────
def make_section1(S):
    story = []
    story.append(P("1.  CLAUDE.md — Developer Context Prompt", S["h1"]))
    story.append(hr())

    story.append(sp(6))
    story.append(P("1.1  Purpose", S["h2"]))
    story.append(P(
        "<b>CLAUDE.md</b> is a Markdown file placed at the project root. Claude Code automatically "
        "loads it at the start of every development session, giving the AI complete awareness of "
        "the project without the developer having to re-explain architecture each time.",
        S["body"]))
    story.append(sp(4))
    for item in [
        "Eliminates repetitive onboarding questions at the start of every session",
        "Ensures the AI never suggests changes that violate architectural constraints (e.g., importing the MCP server directly)",
        "Provides a single authoritative reference that stays in version control alongside the code",
        "Accelerates onboarding for human developers as well as AI assistants",
    ]:
        story.append(bullet(item, S))

    story.append(sp(8))
    story.append(P("1.2  Sections Covered", S["h2"]))

    sections = [
        ("Project Overview", "One-paragraph description of purpose, user base, and deployment environment"),
        ("Architecture Diagram", "ASCII flow diagram: Frontend → FastAPI → LangGraph → MCP → SQLite"),
        ("Tech Stack Table", "Framework, AI model, protocol, database, frontend, and PDF generation libraries"),
        ("Key Files Table", "Every critical file with a one-line description of its role"),
        ("Database Schema", "Tables, sample data date, and abnormal vital threshold definitions"),
        ("MCP Tools Reference", "All 9 tools with descriptions — gives the AI full tool awareness"),
        ("Development Commands", "Install, run, and DB reset commands for immediate use"),
        ("Frontend Pages", "Route → file → purpose mapping for all 4 pages"),
        ("Agent System Prompt", "Pointer and preservation notes for the runtime prompt"),
        ("Conventions", "No build step, stateless agent, no MCP direct imports, model pinning"),
    ]
    story.append(styled_table(
        ["Section", "Content"],
        sections, S,
        col_widths=[CONTENT_W * 0.32, CONTENT_W * 0.68],
    ))

    story.append(sp(10))
    story.append(P("1.3  Key Conventions Encoded", S["h2"]))
    story.append(P(
        "The following constraints are explicitly captured in CLAUDE.md to prevent the most "
        "common AI-assisted development mistakes in this codebase:",
        S["body"]))
    story.append(sp(6))

    conventions = [
        (RED,   "No direct MCP import",
         "The MCP server runs as a subprocess. Importing mcp_server from app code breaks the transport architecture."),
        (NAVY,  "Stateless agent only",
         "No session memory may be added without explicit product approval — the per-request subprocess design is intentional."),
        (TEAL,  "No committing the database",
         "data/ed_database.db is auto-generated on startup and must not be committed to version control."),
        (GREEN, "Model pinning",
         "The Claude model is explicitly pinned in app/agent.py. Change it deliberately, not incidentally."),
        (GOLD,  "No build step",
         "Frontend HTML/CSS/JS is edited directly — there is no bundler, transpiler, or compilation step."),
    ]
    for colour, label, body in conventions:
        story.append(RuleCard("→", label, body, accent=colour))
        story.append(sp(5))

    story.append(sp(8))
    story.append(PageBreak())
    return story


# ── Section 2 — SYSTEM_PROMPT ─────────────────────────────────────────────────
def make_section2(S):
    story = []
    story.append(P("2.  SYSTEM_PROMPT — Agent Runtime Prompt", S["h1"]))
    story.append(hr())

    story.append(sp(6))
    story.append(P("2.1  Purpose and Placement", S["h2"]))
    story.append(P(
        "The <b>SYSTEM_PROMPT</b> is injected as the system message into every LangGraph ReAct "
        "agent invocation. It lives in <b>app/agent.py</b> and is passed directly to "
        "<font face='Courier'>create_react_agent(llm, tools, prompt=SYSTEM_PROMPT)</font>. "
        "Every chat request — regardless of what the user asks — receives this full prompt, "
        "ensuring consistent role framing, tool selection, output formatting, and safety behaviour.",
        S["body"]))

    story.append(sp(8))
    story.append(P("2.2  Prompt Structure", S["h2"]))
    story.append(P(
        "The prompt is divided into four named sections, each serving a distinct purpose:",
        S["body"]))
    story.append(sp(6))

    prompt_sections = [
        ("Role Statement",      "First paragraph — no heading",
         "Establishes identity (clinical decision support AI), audience (physicians, nurses, triage staff), core value proposition (surface information fast), and the hard boundary (no autonomous clinical decisions)."),
        ("## Available Capabilities", "Tool routing guide",
         "Maps each of the 9 MCP tools to the query type it handles. Reduces unnecessary tool calls by telling the agent which tool to reach for first in each scenario."),
        ("## Clinical Reference", "ESI and vitals tables",
         "Two reference tables baked into the prompt: ESI triage levels 1–5 with severity and required action, and abnormal vital sign thresholds for HR, SBP, SpO₂, Temp, and RR."),
        ("## Response Format Rules", "Output formatting spec",
         "Defines how responses must be structured: single patient → labelled sections; multi-patient → markdown table; allergy warnings → ⚠ prefix; critical patients → 🔴 prefix; abnormal vitals → inline ↑↓ annotation."),
        ("## Safety Rules",     "Hard guardrails",
         "Five non-negotiable rules: no medication recommendations, mandatory protocol reminder when clinical data influences care, clear not-found messaging, no unprompted record writes, and refusal of write SQL via execute_query."),
    ]
    story.append(styled_table(
        ["Prompt Section", "Role", "Description"],
        prompt_sections, S,
        col_widths=[CONTENT_W * 0.28, CONTENT_W * 0.20, CONTENT_W * 0.52],
    ))

    story.append(sp(10))
    story.append(P("2.3  Tool Routing Logic", S["h2"]))
    story.append(P(
        "The prompt instructs the agent to select tools based on what the user provides, "
        "minimising unnecessary tool calls and reducing latency:",
        S["body"]))
    story.append(sp(6))

    tools = [
        ("get_patient_by_mrn",      "MRN is known",                   "Fastest — direct primary-key lookup"),
        ("search_patients",         "Name or partial name given",      "Full-text search across name fields"),
        ("get_patient_full_record", "Complete clinical picture needed","All vitals, allergies, meds, history in one call"),
        ("get_critical_patients",   "ESI 1–2 list requested",         "Pre-filtered query — most efficient for shift overviews"),
        ("get_today_census",        "Shift overview or all patients",  "Date-parameterised; sample date 2025-04-28"),
        ("execute_query",           "Custom query not covered above",  "SELECT only — agent refuses write SQL"),
        ("insert_intake",           "Explicit patient registration",   "Used only on explicit staff instruction"),
        ("list_tables / describe_table", "Schema exploration needed", "Rarely needed; used for ad-hoc database investigation"),
    ]
    story.append(styled_table(
        ["Tool", "Use When", "Notes"],
        tools, S,
        col_widths=[CONTENT_W * 0.30, CONTENT_W * 0.30, CONTENT_W * 0.40],
        first_col_code=True,
    ))

    story.append(sp(10))
    story.append(P("2.4  Clinical Reference Tables", S["h2"]))
    story.append(P(
        "Two lookup tables are embedded directly in the prompt so the agent applies consistent "
        "clinical thresholds without needing to query external knowledge:",
        S["body"]))

    story.append(sp(6))
    story.append(P("ESI Triage Levels", S["h3"]))
    esi_rows = [
        ("1", "Immediate — life threat",    "Flag as 🔴 CRITICAL — immediate physician notification"),
        ("2", "Emergent — high risk",       "Flag as 🔴 CRITICAL — urgent escalation"),
        ("3", "Urgent",                     "Note acuity in response — no critical flag"),
        ("4", "Less urgent",                "Standard display"),
        ("5", "Non-urgent",                 "Standard display"),
    ]
    story.append(styled_table(
        ["ESI", "Severity", "Agent Action"],
        esi_rows, S,
        col_widths=[CONTENT_W * 0.10, CONTENT_W * 0.32, CONTENT_W * 0.58],
    ))

    story.append(sp(8))
    story.append(P("Abnormal Vital Sign Thresholds", S["h3"]))
    vitals_rows = [
        ("Heart Rate",       "< 60 bpm",    "> 100 bpm",   "Bradycardia / Tachycardia"),
        ("Systolic BP",      "< 90 mmHg",   "> 180 mmHg",  "Hypotension / Hypertensive crisis"),
        ("SpO₂",             "< 95%",       "—",           "Hypoxia"),
        ("Temperature",      "< 36.0°C",    "> 38.3°C",    "Hypothermia / Fever"),
        ("Respiratory Rate", "< 12 /min",   "> 20 /min",   "Bradypnea / Tachypnea"),
    ]
    story.append(styled_table(
        ["Vital Sign", "Abnormal Low", "Abnormal High", "Clinical Concern"],
        vitals_rows, S,
        col_widths=[CONTENT_W * 0.26, CONTENT_W * 0.18, CONTENT_W * 0.18, CONTENT_W * 0.38],
    ))

    story.append(sp(10))
    story.append(PageBreak())
    return story


# ── Section 3 — Response Format ───────────────────────────────────────────────
def make_section3(S):
    story = []
    story.append(P("3.  Response Format Specification", S["h1"]))
    story.append(hr())

    story.append(sp(6))
    story.append(P("3.1  Single Patient Summary Format", S["h2"]))
    story.append(P(
        "When a query returns a single patient, the agent must structure its response with "
        "labelled sections. This ensures nursing and physician staff can scan for the field "
        "they need rather than reading prose from top to bottom.",
        S["body"]))
    story.append(sp(5))
    story.append(CodeBlock([
        "**Demographics**   MRN: A10001 | Name: John Smith | DOB: 1965-03-14 | Age: 61 | M",
        "**Chief Complaint** Chest pain radiating to left arm, onset 2 hours ago",
        "**ESI**            🔴 CRITICAL — ESI 2 (Emergent)",
        "**Arrival**        2025-04-28 08:12 via EMS",
        "",
        "**Vitals**",
        "  HR: 118 bpm ↑  |  SBP: 88 mmHg ↓  |  SpO₂: 93% ↓  |  Temp: 37.1°C  |  RR: 22 /min ↑",
        "",
        "⚠ ALLERGY: Penicillin (rash, hives) — verify before any antibiotic order",
        "",
        "**Medications**    Metoprolol 25mg PO BID | Aspirin 81mg PO daily",
        "**History**        HTN, CAD, Prior MI (2019)",
        "",
        "Please verify with the treating clinician and follow institutional protocols.",
    ]))

    story.append(sp(10))
    story.append(P("3.2  Multi-Patient Census / List Format", S["h2"]))
    story.append(P(
        "When returning multiple patients (census, critical list, search results), the agent "
        "uses a markdown table. Critical patients are prefixed and appear first.",
        S["body"]))
    story.append(sp(5))
    story.append(CodeBlock([
        "| MRN     | Name            | ESI | Chief Complaint          | Flags              |",
        "|---------|-----------------|-----|--------------------------|--------------------|",
        "| A10001  | John Smith      | 🔴 2 | Chest pain               | SpO₂ 93% ↓, HR ↑  |",
        "| A10003  | Maria Garcia    | 🔴 1 | Altered mental status    | BP 78/42 ↓         |",
        "| A10007  | Robert Chen     |  3  | Abdominal pain           | Temp 38.6°C ↑      |",
        "| A10002  | Jane Doe        |  4  | Laceration — right hand  | —                  |",
    ]))

    story.append(sp(10))
    story.append(P("3.3  Visual Flag System", S["h2"]))

    flags = [
        ("🔴 CRITICAL",   "ESI 1 or ESI 2",              "Prepend to patient name or ESI field"),
        ("⚠ ALLERGY",    "Any known patient allergy",    "Shown in every response about that patient"),
        ("↑ (arrow up)",  "Vital above threshold",        "Appended inline to the vital value"),
        ("↓ (arrow down)","Vital below threshold",        "Appended inline to the vital value"),
        ("Protocol note", "Any clinical data that could influence care",
         "Always append the standard protocol reminder at the end of the response"),
    ]
    story.append(styled_table(
        ["Flag", "Trigger Condition", "Placement"],
        flags, S,
        col_widths=[CONTENT_W * 0.22, CONTENT_W * 0.38, CONTENT_W * 0.40],
    ))

    story.append(sp(10))
    story.append(PageBreak())
    return story


# ── Section 4 — Safety Rules ──────────────────────────────────────────────────
def make_section4(S):
    story = []
    story.append(P("4.  Safety Rules", S["h1"]))
    story.append(hr())
    story.append(sp(6))
    story.append(P(
        "Five non-negotiable safety rules are hard-coded into the SYSTEM_PROMPT. They are "
        "architectural constraints — not suggestions — and must be preserved in any future "
        "revision of the prompt.",
        S["body"]))
    story.append(sp(8))

    rules = [
        (RED,   "No Clinical Recommendations",
         "The agent must never recommend a specific medication, dose, or treatment plan. "
         "It presents data only. Clinical decisions belong exclusively to licensed clinicians."),
        (NAVY,  "Mandatory Protocol Reminder",
         "Whenever a response contains clinical data that could influence a care decision, "
         "the agent must end with: \"Please verify with the treating clinician and follow "
         "institutional protocols.\""),
        (TEAL,  "Clear Not-Found Messaging",
         "If a patient is not found, the agent states this explicitly and suggests "
         "verifying the MRN or spelling. It must never guess or return a partial match "
         "without flagging the uncertainty."),
        (GREEN, "No Unprompted Record Writes",
         "The insert_intake tool is used only when a staff member explicitly requests "
         "patient registration. The agent must never initiate a database write autonomously."),
        (GOLD,  "Read-Only SQL Enforcement",
         "If a user asks the agent to run a destructive or write SQL query via execute_query, "
         "the agent refuses and explains that the tool accepts SELECT statements only."),
    ]

    for i, (colour, label, body) in enumerate(rules, 1):
        story.append(RuleCard(i, label, body, accent=colour))
        story.append(sp(6))

    story.append(sp(6))
    story.append(P(
        "These rules reflect a fundamental design principle: the ED AI Agent is a "
        "<b>data surface tool</b>, not a clinical decision engine. All clinical authority "
        "remains with licensed staff. The agent accelerates information access; it does not "
        "replace clinical judgement.",
        S["body"]))

    story.append(sp(8))
    story.append(PageBreak())
    return story


# ── Section 5 — Maintenance ───────────────────────────────────────────────────
def make_section5(S):
    story = []
    story.append(P("5.  Maintenance and Update Guidelines", S["h1"]))
    story.append(hr())
    story.append(sp(6))

    story.append(P("5.1  When to Update CLAUDE.md", S["h2"]))
    for item in [
        "A new page or route is added to the frontend",
        "A new MCP tool is registered in <font face='Courier'>mcp_server/server.py</font>",
        "The database schema changes (new table or column)",
        "The Claude model is upgraded in <font face='Courier'>app/agent.py</font>",
        "A new architectural constraint is established (e.g., adding Redis for session state)",
        "The deployment environment changes (new cloud provider, new port)",
    ]:
        story.append(bullet(item, S))

    story.append(sp(8))
    story.append(P("5.2  When to Update SYSTEM_PROMPT", S["h2"]))
    for item in [
        "A new MCP tool is added — add it to the tool routing section",
        "Clinical thresholds change (e.g., institutional policy adjusts SpO₂ threshold)",
        "A new output format is required (e.g., voice-optimised prose for a voice interface)",
        "A new safety rule is mandated by legal, compliance, or clinical governance",
        "The agent model is upgraded — verify all formatting instructions still apply",
        "Staff feedback indicates the agent is misrouting tool calls or producing inconsistent output",
    ]:
        story.append(bullet(item, S))

    story.append(sp(8))
    story.append(P("5.3  What Must Never Change", S["h2"]))
    story.append(P(
        "The following elements of the SYSTEM_PROMPT are load-bearing and must not be removed "
        "or weakened without clinical governance sign-off:",
        S["body"]))
    story.append(sp(4))

    immutable = [
        ("The opening role statement",     "Defines the AI's scope and authority boundary"),
        ("All five Safety Rules",          "Protect patients and staff from AI overreach"),
        ("The protocol reminder trigger",  "Required by clinical risk management policy"),
        ("ESI 1–2 critical flag rule",     "Ensures no high-acuity patient is visually de-prioritised"),
        ("Allergy warning rule",           "Medication error prevention — non-negotiable"),
    ]
    story.append(styled_table(
        ["Element", "Reason"],
        immutable, S,
        col_widths=[CONTENT_W * 0.40, CONTENT_W * 0.60],
    ))

    story.append(sp(10))
    story.append(P("5.4  Version Control", S["h2"]))
    story.append(P(
        "Both prompt files are version-controlled in the project repository. Changes to either "
        "prompt should be committed with a descriptive message explaining the clinical or "
        "operational reason for the change — not just what changed, but <b>why</b>. "
        "Prompt changes are code changes and carry the same review requirements.",
        S["body"]))

    story.append(sp(10))
    story.append(hr())
    story.append(sp(8))
    story.append(P(
        "Document prepared for: <b>Adviava Regional Medical Center</b> — ED Operations and Digital Health",
        S["italic"]))
    story.append(P(
        "Technology: FastAPI · LangChain · LangGraph · Claude Sonnet 4.6 · Model Context Protocol (MCP)",
        S["italic"]))
    story.append(P(
        "Adviava Regional Medical Center  |  Confidential — For Internal Use Only  |  April 2026",
        S["footer"]))
    return story


# ── Assembly ───────────────────────────────────────────────────────────────────
def build_pdf(output_path: str):
    S = make_styles()

    cover_frame = Frame(
        MARGIN, 14 * mm, CONTENT_W, H - 28 * mm,
        leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
    )
    inner_frame = Frame(
        MARGIN + 4 * mm, 16 * mm, CONTENT_W - 4 * mm, H - 32 * mm,
        leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
    )

    doc = BaseDocTemplate(
        output_path, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=16 * mm, bottomMargin=16 * mm,
    )
    doc.addPageTemplates([
        PageTemplate(id="cover", frames=[cover_frame], onPage=cover_background),
        PageTemplate(id="inner", frames=[inner_frame], onPage=inner_background),
    ])

    story = []
    story += make_cover(S)
    story.insert(1, NextPageTemplate("inner"))
    story += make_intro(S)
    story += make_section1(S)
    story += make_section2(S)
    story += make_section3(S)
    story += make_section4(S)
    story += make_section5(S)

    doc.build(story)
    print(f"PDF saved: {output_path}")


if __name__ == "__main__":
    out = Path("Adviava_ED_AI_Agent_Prompt_Template.pdf")
    build_pdf(str(out))
