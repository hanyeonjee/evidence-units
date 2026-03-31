"""Generate Evidence Units GitHub banner (assets/banner.png)."""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
from matplotlib.lines import Line2D
import matplotlib.patheffects as pe

# ── canvas ────────────────────────────────────────────────────────────────────
W, H = 16, 4.6
fig, ax = plt.subplots(figsize=(W, H), dpi=120)
ax.set_xlim(0, W)
ax.set_ylim(0, H)
ax.axis("off")

BG      = "#0d1117"
C_HDR   = "#60A5FA"   # section_header  — blue
C_TBL   = "#FBBF24"   # table           — amber
C_CAP   = "#34D399"   # caption         — emerald
C_UNIT  = "#A78BFA"   # unit_label      — violet
C_PARA  = "#94A3B8"   # paragraph       — slate
C_EU    = "#38BDF8"   # EU border       — sky blue
C_ONT   = "#818CF8"   # ontology accent — indigo
C_TEXT  = "#F8FAFC"
C_DIM   = "#64748B"

fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)

# ── helpers ───────────────────────────────────────────────────────────────────
def box(ax, x, y, w, h, color, alpha=0.85, lw=0, radius=0.08):
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad=0,rounding_size={radius}",
        facecolor=color, edgecolor="none", alpha=alpha, lw=lw, zorder=3
    ))

def label(ax, x, y, txt, size=7.5, color=C_DIM, ha="left", va="center", bold=False):
    weight = "bold" if bold else "normal"
    ax.text(x, y, txt, fontsize=size, color=color, ha=ha, va=va,
            fontweight=weight, zorder=5, fontfamily="monospace")

def section_title(ax, x, y, txt, size=8.5):
    ax.text(x, y, txt, fontsize=size, color=C_DIM, ha="center", va="center",
            fontweight="normal", zorder=5, fontstyle="italic")

# ══════════════════════════════════════════════════════════════════════════════
# LEFT PANEL — "Parser Output"
# ══════════════════════════════════════════════════════════════════════════════
PX, PY, PW, PH = 0.8, 0.65, 3.3, 3.5   # panel bounding box

# panel bg
ax.add_patch(FancyBboxPatch((PX, PY), PW, PH,
    boxstyle="round,pad=0,rounding_size=0.12",
    facecolor="#161b22", edgecolor=C_DIM, alpha=1.0, lw=0.6, zorder=2))

section_title(ax, PX + PW/2, PY + PH + 0.2, "Parser Output")

# document elements (scattered, misaligned feel)
ex = PX + 0.22

#  section header
box(ax, ex, PY + 2.90, 2.70, 0.30, C_HDR, alpha=0.80)
label(ax, ex + 0.10, PY + 3.05, "section_header", size=7.2, color=BG, bold=True)

#  table (parser A: 1 bbox)
box(ax, ex, PY + 1.55, 2.70, 1.10, C_TBL, alpha=0.70)
label(ax, ex + 0.10, PY + 2.12, "table  (Parser A: 1 bbox)", size=7.2, color=BG, bold=True)

# table split (parser B hint — three thin lines inside)
for i, (yoff, h) in enumerate([(1.55, 0.30), (1.85, 0.45), (2.30, 0.35)]):
    ax.add_patch(FancyBboxPatch(
        (ex + 1.55, PY + yoff + 0.05), 0.95, h - 0.08,
        boxstyle="round,pad=0,rounding_size=0.05",
        facecolor=C_TBL, edgecolor="#0d1117", alpha=0.45, lw=0.5, zorder=4))
label(ax, ex + 1.65, PY + 2.12, "Parser B:\n3 rows", size=6, color=BG)

#  caption
box(ax, ex, PY + 1.10, 2.70, 0.30, C_CAP, alpha=0.80)
label(ax, ex + 0.10, PY + 1.25, "caption", size=7.2, color=BG, bold=True)

#  unit_label
box(ax, ex, PY + 0.68, 1.30, 0.28, C_UNIT, alpha=0.80)
label(ax, ex + 0.10, PY + 0.82, "unit_label", size=7.2, color=BG, bold=True)

#  paragraph (lighter, trailing)
box(ax, ex, PY + 0.18, 2.70, 0.35, C_PARA, alpha=0.55)
label(ax, ex + 0.10, PY + 0.36, "paragraph ···", size=7.2, color=BG, bold=True)

# ══════════════════════════════════════════════════════════════════════════════
# CENTER — Ontology normalization
# ══════════════════════════════════════════════════════════════════════════════
CX = 4.8
cy_mid = PY + PH / 2

# vertical ontology spine
ax.plot([CX + 0.75, CX + 0.75], [cy_mid - 1.1, cy_mid + 1.1],
        color=C_ONT, lw=1.2, alpha=0.6, zorder=3)

# canonical role dots
roles = [
    (C_HDR,  "section_header"),
    (C_TBL,  "table"),
    (C_CAP,  "caption"),
    (C_UNIT, "unit_label"),
    (C_PARA, "paragraph"),
]
for i, (col, name) in enumerate(roles):
    dy = cy_mid + 0.9 - i * 0.45
    ax.plot(CX + 0.75, dy, "o", color=col, ms=5, zorder=5)
    ax.text(CX + 0.95, dy, name, fontsize=6.8, color=col,
            va="center", fontfamily="monospace", zorder=5)

# ontology label
ax.text(CX + 0.75, PY + PH + 0.2, "DSO Ontology", fontsize=8.5,
        color=C_DIM, ha="center", va="center", fontstyle="italic", zorder=5)

# arrow left → right
ax.annotate("", xy=(7.15, cy_mid), xytext=(CX - 0.05, cy_mid),
            arrowprops=dict(arrowstyle="-|>", color=C_ONT,
                            lw=1.8, mutation_scale=16), zorder=6)
ax.text((CX - 0.05 + 7.15) / 2, cy_mid - 0.38,
        "normalize\n& group", fontsize=7.5, color=C_ONT,
        ha="center", va="center", fontstyle="italic", zorder=5)

# ══════════════════════════════════════════════════════════════════════════════
# RIGHT PANEL — Evidence Unit
# ══════════════════════════════════════════════════════════════════════════════
RX, RY, RW, RH = 7.3, 0.65, 3.5, 3.5

ax.add_patch(FancyBboxPatch((RX, RY), RW, RH,
    boxstyle="round,pad=0,rounding_size=0.12",
    facecolor="#161b22", edgecolor=C_DIM, alpha=1.0, lw=0.6, zorder=2))

section_title(ax, RX + RW/2, RY + RH + 0.2, "Evidence Unit")

rx = RX + 0.22
gap = 0.10

# EU outer dashed border
eu_pad = 0.12
eu_border = mpatches.FancyBboxPatch(
    (rx - eu_pad, RY + 0.10),
    2.85 + eu_pad * 2, 3.20,
    boxstyle="round,pad=0,rounding_size=0.14",
    facecolor="none", edgecolor=C_EU, lw=1.6,
    linestyle=(0, (4, 3)), alpha=0.9, zorder=4
)
ax.add_patch(eu_border)

# stacked members
members = [
    (C_HDR,  "section_header"),
    (C_TBL,  "table"),
    (C_CAP,  "caption"),
    (C_UNIT, "unit_label"),
    (C_PARA, "paragraph"),
]
heights = [0.30, 1.10, 0.30, 0.28, 0.35]
y_cur = RY + 0.22
for (col, name), h in zip(members, heights):
    box(ax, rx, y_cur, 2.85, h, col,
        alpha=0.80 if name != "paragraph" else 0.55)
    label(ax, rx + 0.10, y_cur + h / 2, name,
          size=7.2, color=BG, bold=True)
    y_cur += h + gap

# EU label badge
badge_x, badge_y = rx + 2.85 - 0.05, RY + 0.12
ax.text(badge_x, badge_y, "EU", fontsize=8, color=C_EU, ha="right", va="bottom",
        fontweight="bold", fontstyle="italic", zorder=6,
        path_effects=[pe.withStroke(linewidth=2, foreground="#161b22")])

# ══════════════════════════════════════════════════════════════════════════════
# TITLE (right side of canvas)
# ══════════════════════════════════════════════════════════════════════════════
TX = 11.6
ax.text(TX, 3.60, "Evidence Units", fontsize=26, color=C_TEXT,
        ha="left", va="center", fontweight="bold", zorder=5,
        path_effects=[pe.withStroke(linewidth=3, foreground=BG)])

ax.text(TX, 3.00,
        "Ontology-Grounded Document\nOrganization for\nParser-Independent Retrieval",
        fontsize=11.5, color="#94A3B8", ha="left", va="center",
        linespacing=1.6, zorder=5)

# thin separator line
ax.plot([TX - 0.1, TX - 0.1], [1.1, 4.1],
        color=C_EU, lw=1.5, alpha=0.5, zorder=3)

# bottom tag line
ax.text(TX, 1.70, "KT (Korea Telecom) · GenApp Tech",
        fontsize=8.5, color=C_DIM, ha="left", va="center", zorder=5)
ax.text(TX, 1.28, "arXiv:XXXX.XXXXX · github.com/hanyeonjee/evidence-units",
        fontsize=8, color=C_DIM, ha="left", va="center", zorder=5,
        fontfamily="monospace")

# ── save ──────────────────────────────────────────────────────────────────────
out = "assets/banner.png"
plt.tight_layout(pad=0)
plt.savefig(out, dpi=120, bbox_inches="tight", facecolor=BG)
print(f"Saved → {out}")
plt.close()
