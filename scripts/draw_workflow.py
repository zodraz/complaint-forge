"""Generates complaint-forge workflow diagram as a PNG using Pillow."""
import math
from PIL import Image, ImageDraw, ImageFont

W, H = 1500, 1950
BG = "#F8F9FA"
FONT_PATH = None  # will fall back to default

# Colors
C_LLM        = "#4A90D9"   # blue  — LLM agents
C_DET        = "#5BA85B"   # green — deterministic nodes
C_ESC        = "#E07B39"   # orange — escalation nodes
C_HUM        = "#C0392B"   # red   — human review
C_IO         = "#6C757D"   # gray  — input/output/end
C_BORDER     = "#2C3E50"
C_TEXT_LIGHT = "#FFFFFF"
C_TEXT_DARK  = "#2C3E50"
C_ARROW      = "#2C3E50"
C_ARROW_ESC  = "#C0392B"

def load_font(size):
    try:
        return ImageFont.truetype("arial.ttf", size)
    except Exception:
        return ImageFont.load_default()

def draw_rounded_rect(draw, x1, y1, x2, y2, r, fill, outline, width=2):
    draw.rounded_rectangle([x1, y1, x2, y2], radius=r, fill=fill, outline=outline, width=width)

def text_center(draw, cx, cy, lines, font, color):
    line_h = font.size + 4
    total_h = len(lines) * line_h
    y = cy - total_h / 2 + 2
    for line in lines:
        bbox = font.getbbox(line)
        tw = bbox[2] - bbox[0]
        draw.text((cx - tw / 2, y), line, font=font, fill=color)
        y += line_h

def arrow(draw, x1, y1, x2, y2, color=C_ARROW, width=2, label=None, label_font=None, label_color="#555555"):
    draw.line([(x1, y1), (x2, y2)], fill=color, width=width)
    # arrowhead
    angle = math.atan2(y2 - y1, x2 - x1)
    size = 10
    for sign in (1, -1):
        ax = x2 - size * math.cos(angle - sign * math.pi / 6)
        ay = y2 - size * math.sin(angle - sign * math.pi / 6)
        draw.line([(x2, y2), (ax, ay)], fill=color, width=width)
    if label and label_font:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        bbox = label_font.getbbox(label)
        tw = bbox[2] - bbox[0]
        draw.rectangle([mx - tw/2 - 3, my - 9, mx + tw/2 + 3, my + 9], fill="#F8F9FA", outline=None)
        draw.text((mx - tw/2, my - 8), label, font=label_font, fill=label_color)

def polyline_arrow(draw, points, color=C_ARROW, width=2):
    for i in range(len(points) - 1):
        draw.line([points[i], points[i+1]], fill=color, width=width)
    x1, y1 = points[-2]
    x2, y2 = points[-1]
    angle = math.atan2(y2 - y1, x2 - x1)
    size = 10
    for sign in (1, -1):
        ax = x2 - size * math.cos(angle - sign * math.pi / 6)
        ay = y2 - size * math.sin(angle - sign * math.pi / 6)
        draw.line([(x2, y2), (ax, ay)], fill=color, width=width)

# Node: (cx, cy, w, h, lines, fill, text_color)
nodes = {
    "input":            (500,  70,  340,  50, ["Zendesk Webhook / POST /complaint"],        C_IO,   C_TEXT_LIGHT),
    "triage":           (500, 175,  280,  70, ["TRIAGE", "[LLM Agent]"],                    C_LLM,  C_TEXT_LIGHT),
    "ignored":          (130, 280,  200,  55, ["IGNORED"],                                  C_IO,   C_TEXT_LIGHT),
    "end_ignored":      (130, 375,   80,  40, ["END"],                                      C_IO,   C_TEXT_LIGHT),
    "customer_context": (500, 340,  280,  70, ["CUSTOMER CONTEXT", "[Salesforce lookup]"],  C_DET,  C_TEXT_LIGHT),
    "analyzer":         (500, 460,  280,  70, ["ANALYZER", "[LLM Agent]"],                  C_LLM,  C_TEXT_LIGHT),
    "resolver":         (500, 580,  280,  70, ["RESOLVER", "[LLM Agent]"],                  C_LLM,  C_TEXT_LIGHT),
    "policy":           (500, 710,  280,  90, ["POLICY", "[Deterministic Rules]"],           C_DET,  C_TEXT_LIGHT),
    "responder":        (500, 860,  280,  70, ["RESPONDER", "[LLM Agent]"],                  C_LLM,  C_TEXT_LIGHT),
    "guardrails":       (500, 990,  280,  90, ["GUARDRAILS", "[LLM Evaluators]"],            C_DET,  C_TEXT_LIGHT),
    "action":           (500,1135,  280,  70, ["ACTION AGENT", "[Salesforce actions]"],      C_DET,  C_TEXT_LIGHT),
    "communication":    (500,1260,  280,  70, ["COMMUNICATION", "[Zendesk MCP]"],            C_DET,  C_TEXT_LIGHT),
    "end":              (500,1370,   80,  40, ["END"],                                       C_IO,   C_TEXT_LIGHT),
    "specialist":       (1080, 930, 280,  80, ["SPECIALIST REVIEW", "[A2A · CrewAI]"],       C_ESC,  C_TEXT_LIGHT),
    "human_review":     (1080,1070, 280,  80, ["HUMAN REVIEW", "[LangGraph interrupt()]"],   C_HUM,  C_TEXT_LIGHT),
}

img = Image.new("RGB", (W, H), BG)
draw = ImageDraw.Draw(img)

f_title  = load_font(22)
f_main   = load_font(17)
f_sub    = load_font(13)
f_label  = load_font(13)
f_legend = load_font(14)

# Draw title
title = "ComplaintForge — LangGraph Workflow"
bbox = f_title.getbbox(title)
tw = bbox[2] - bbox[0]
draw.text((W/2 - tw/2, 10), title, font=f_title, fill=C_TEXT_DARK)

# Draw nodes
for key, (cx, cy, w, h, lines, fill, tc) in nodes.items():
    x1, y1 = cx - w/2, cy - h/2
    x2, y2 = cx + w/2, cy + h/2
    draw_rounded_rect(draw, x1, y1, x2, y2, 10, fill, C_BORDER, width=2)
    if len(lines) == 1:
        text_center(draw, cx, cy, lines, f_main, tc)
    else:
        text_center(draw, cx, cy - 8, [lines[0]], f_main, tc)
        text_center(draw, cx, cy + 10, [lines[1]], f_sub, tc)

# ── Main happy-path arrows ──────────────────────────────────────────────────
def bottom(k): cx,cy,w,h,*_ = nodes[k]; return (cx, cy+h/2)
def top(k):    cx,cy,w,h,*_ = nodes[k]; return (cx, cy-h/2)
def left(k):   cx,cy,w,h,*_ = nodes[k]; return (cx-w/2, cy)
def right(k):  cx,cy,w,h,*_ = nodes[k]; return (cx+w/2, cy)

# input → triage
arrow(draw, *bottom("input"), *top("triage"))

# triage → customer_context (labeled)
arrow(draw, *bottom("triage"), *top("customer_context"),
      label="is complaint", label_font=f_label, label_color="#1A6A20")

# triage → ignored (branch left)
tx, ty = bottom("triage"); tx2,ty2 = right("ignored")
polyline_arrow(draw, [(tx,ty),(tx,270),(tx2,270)], color=C_IO)
lbl = "not complaint"
bbox = f_label.getbbox(lbl)
tw2 = bbox[2]-bbox[0]
mx = (tx+tx2)/2-20; my = 260
draw.rectangle([mx-3,my-9,mx+tw2+3,my+9], fill=BG)
draw.text((mx,my-8), lbl, font=f_label, fill="#8B4513")

# ignored → end_ignored
arrow(draw, *bottom("ignored"), *top("end_ignored"), color=C_IO)

# customer_context → analyzer → resolver → policy
for a, b in [("customer_context","analyzer"),("analyzer","resolver"),("resolver","policy")]:
    arrow(draw, *bottom(a), *top(b))

# policy → responder (approved)
px,py = bottom("policy")
arrow(draw, px, py, *top("responder"),
      label="approved", label_font=f_label, label_color="#1A6A20")

# responder → guardrails
arrow(draw, *bottom("responder"), *top("guardrails"))

# guardrails → action (passed)
gx,gy = bottom("guardrails")
arrow(draw, gx, gy, *top("action"),
      label="passed", label_font=f_label, label_color="#1A6A20")

# action → communication → end
arrow(draw, *bottom("action"), *top("communication"))
arrow(draw, *bottom("communication"), *top("end"))

# ── Escalation path arrows ──────────────────────────────────────────────────
# policy → specialist_review (escalate)
px2, py2 = right("policy")
sx, sy = left("specialist")
mid_x = (px2 + sx) / 2
polyline_arrow(draw,
    [(px2, py2), (mid_x, py2), (mid_x, 930), (sx, 930)],
    color=C_ARROW_ESC, width=2)
draw.rectangle([mid_x-52, py2-10, mid_x+52, py2+10], fill=BG)
draw.text((mid_x-50, py2-9), "escalate", font=f_label, fill=C_ARROW_ESC)

# guardrails → specialist_review (escalate)
grx, gry = right("guardrails")
sx2, sy2 = left("specialist")
mid_x2 = (grx + sx2) / 2 + 20
polyline_arrow(draw,
    [(grx, gry), (mid_x2+20, gry), (mid_x2+20, 930), (sx2, 930)],
    color=C_ARROW_ESC, width=2)
draw.rectangle([mid_x2-32, gry-10, mid_x2+72, gry+10], fill=BG)
draw.text((mid_x2-30, gry-9), "escalate", font=f_label, fill=C_ARROW_ESC)

# specialist_review → human_review
arrow(draw, *bottom("specialist"), *top("human_review"), color=C_ARROW_ESC, width=2)

# human_review → communication (route back left)
hrx, hry = bottom("human_review"); hrx2 = hrx
cx2, cy2 = top("communication")
polyline_arrow(draw,
    [(hrx, hry), (hrx, 1200), (cx2+10, 1200), (cx2+10, cy2)],
    color=C_ARROW_ESC, width=2)

# ── Policy escalation trigger labels (inside policy box) ───────────────────
policy_cx, policy_cy, *_ = nodes["policy"]
triggers = [
    "• confidence < 0.85  • refund > $500",
    "• digital/custom product  • no SF order",
]
y0 = policy_cy + 28
for t in triggers:
    bbox = f_sub.getbbox(t)
    tw3 = bbox[2]-bbox[0]
    draw.text((policy_cx - tw3/2, y0), t, font=f_sub, fill="#DDEEDD")
    y0 += 15

# ── Guardrails trigger labels ──────────────────────────────────────────────
g_cx, g_cy, *_ = nodes["guardrails"]
g_triggers = ["• empathy score < 6", "• resolution score < 6"]
y0 = g_cy + 28
for t in g_triggers:
    bbox = f_sub.getbbox(t)
    tw4 = bbox[2]-bbox[0]
    draw.text((g_cx - tw4/2, y0), t, font=f_sub, fill="#DDEEDD")
    y0 += 15

# ── Legend ─────────────────────────────────────────────────────────────────
lx, ly = 30, H - 200
legend_items = [
    (C_LLM,  "LLM Agent"),
    (C_DET,  "Deterministic Node"),
    (C_ESC,  "Escalation (A2A/CrewAI)"),
    (C_HUM,  "Human Review (interrupt)"),
    (C_IO,   "Input / Output / End"),
]
draw.text((lx, ly - 24), "Legend", font=f_legend, fill=C_TEXT_DARK)
for fill, label in legend_items:
    draw.rounded_rectangle([lx, ly, lx+20, ly+18], radius=4, fill=fill, outline=C_BORDER, width=1)
    draw.text((lx+28, ly+1), label, font=f_legend, fill=C_TEXT_DARK)
    ly += 30

# ── Specialist box annotation ──────────────────────────────────────────────
sx3, sy3, sw, sh, *_ = nodes["specialist"]
note = "Advisory recommendation for human approver"
bbox = f_sub.getbbox(note)
nt = bbox[2]-bbox[0]
draw.text((sx3-nt/2, sy3+22), note, font=f_sub, fill="#FFE0C0")

out_path = "workflow.png"
img.save(out_path, "PNG", dpi=(150, 150))
print(f"Saved: {out_path}")
