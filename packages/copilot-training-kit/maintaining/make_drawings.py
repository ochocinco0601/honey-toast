"""The kit's drawings: VS Code's parts, each with its source, and each drawing composed of them.

Run from the kit's folder: python maintaining/make_drawings.py. It writes every drawing into its
training's images folder; then build. The rules are in maintaining/README.md, "Pictures". This file
is the kit's own: a new version of the training-kit skill replaces drawings.py, never this file.

Every part below was checked against VS Code 1.140.0, read from the
source at that tag (src/... paths; "chat/" is src/vs/workbench/contrib/chat/browser/) on 2026-10-07.
"""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from drawings import *  # noqa: E402,F401,F403

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# The chat view's title row: CHAT, then New Chat (+, a split button: chat/actions/chatNewActions.ts 119-127),
# Open Customizations (gear: chat/actions/chatActions.ts 1543-1555) and More. No history action.
def chat_header(x0, x1, y=30):
    # CHAT at the left; New Chat (+, a split button), Open Customizations (gear) and More at the right
    p = x1 - 78
    return ('<text class="dg-s" x="%d" y="%d">CHAT</text>' % (x0 + 16, y + 4) +
            '<path class="dg-ic" d="M%d %dv14M%d %dh14"/>' % (p, y - 7, p - 7, y) +
            '<path class="dg-ic" d="M%d %dl3 3 3-3"/>' % (p + 11, y - 1) +
            gear(p + 36, y) +
            '<path class="dg-ic" d="M%d %dh.5M%d %dh.5M%d %dh.5"/>' % (p + 56, y, p + 62, y, p + 68, y))

def gear(cx, cy, r=6):
    return ('<circle class="dg-ic" cx="%d" cy="%d" r="%d" style="stroke-dasharray:2.4 1.6;stroke-width:2.4"/>'
            '<circle class="dg-ic" cx="%d" cy="%d" r="2.2"/>') % (cx, cy, r, cx, cy)

# The control under the chat box that shows Agent: the agent's icon and its name, no chevron
# (chat/widget/input/modePickerActionItem.ts 296-319). A narrow chat shows the icon only.
def agent_pill(x, y, w=64, h=22):
    # the agent's icon, then "Agent"; no chevron
    return ('<rect class="dg-p" x="%d" y="%d" width="%d" height="%d" rx="5"/>'
            '<path class="dg-ic" d="M%d %.1fl4.5 4.5-4.5 4.5-4.5-4.5z"/>'
            '<text class="dg-t" x="%d" y="%d" style="font-size:12px">Agent</text>') % (
            x, y, w, h, x + 12, y + h / 2 - 4.5, x + 23, y + h / 2 + 4)

# Add Context comes first in the chat box's bottom row (chat/actions/chatContextActions.ts 478-500).
def add_context(cx, cy):
    return '<rect class="dg-ic" x="%d" y="%d" width="11" height="11" rx="2"/><path class="dg-ic" d="M%d %dv5M%.1f %dh5"/>' % (
        cx - 5, cy - 5, cx + 0.5, cy - 2, cx - 2, cy + 0.5)

# The window: menu bar, activity bar, Explorer with the practice folder, an editor with line numbers,
# the chat on the right with the learner's request tinted (layout as VS Code's default; parts as above).
window = """
<rect class="dg-w" x="5" y="5" width="690" height="430" rx="8"/>
<rect class="dg-c" x="6" y="6" width="688" height="28" rx="7"/>
<text class="dg-t" x="20" y="25" style="font-size:12px">File   Edit   Selection   View   Go   …</text>
<rect class="dg-p" x="270" y="11" width="160" height="17" rx="4"/><rect class="dg-b" x="280" y="17" width="60" height="5" rx="2"/>
<path class="dg-ic" d="M630 20h9M652 15h9v9h-9zM674 15l9 9M683 15l-9 9"/>
<rect class="dg-c" x="6" y="34" width="34" height="380"/>
<path class="dg-ic" d="M17 48h8l4 4v12H17z"/>
<circle class="dg-ic" cx="22" cy="83" r="5"/><path class="dg-ic" d="M26 87l5 5"/>
<circle class="dg-ic" cx="19" cy="108" r="2.5"/><circle class="dg-ic" cx="27" cy="116" r="2.5"/><path class="dg-ic" d="M19 111v10M19 118c0-4 8-2 8-4"/>
<path class="dg-ic" d="M18 136l10 6-10 6z"/>
<path class="dg-ic" d="M16 162h6v6h-6zM25 162h6v6h-6zM16 171h6v6h-6zM27 170l4 4-4 4-4-4z"/>
<line class="dg-l" x1="190" y1="34" x2="190" y2="414"/>
<text class="dg-s" x="50" y="54">EXPLORER</text>
<text class="dg-tb" x="50" y="78" style="font-size:12px">⌄ COPILOT-PRACTICE</text>
<text class="dg-t" x="62" y="100">› notes</text>
<rect class="dg-tn" x="41" y="108" width="149" height="20"/>
<rect class="dg-b2" x="62" y="112" width="9" height="11" rx="2"/><text class="dg-t" x="77" y="122">actions.md</text>
<rect class="dg-c" x="191" y="34" width="263" height="26"/>
<rect class="dg-w" x="191" y="34" width="100" height="26" style="stroke:none"/>
<line x1="191" y1="59" x2="291" y2="59" style="stroke:var(--accent,#0065b3);stroke-width:2"/>
<text class="dg-t" x="201" y="52">actions.md</text><path class="dg-ic" d="M274 44l6 6M280 44l-6 6"/>
<g class="dg-n" style="font-size:11px"><text x="200" y="84">1</text><text x="200" y="102">2</text><text x="200" y="120">3</text><text x="200" y="138">4</text><text x="200" y="156">5</text><text x="200" y="174">6</text></g>
<rect class="dg-b2" x="220" y="77" width="120" height="8" rx="2"/>
<rect class="dg-b" x="220" y="113" width="190" height="7" rx="2"/>
<rect class="dg-b" x="220" y="131" width="160" height="7" rx="2"/>
<rect class="dg-b" x="220" y="149" width="205" height="7" rx="2"/>
<rect class="dg-b" x="220" y="167" width="140" height="7" rx="2"/>
<line class="dg-l" x1="455" y1="34" x2="455" y2="414"/>
""" + chat_header(455, 694, 50) + """
<rect class="dg-b" x="467" y="66" width="104" height="6" rx="2"/>
<rect class="dg-tn" x="520" y="82" width="164" height="42" rx="7"/>
<rect class="dg-b2" x="532" y="93" width="138" height="7" rx="2"/><rect class="dg-b2" x="532" y="107" width="96" height="7" rx="2"/>
<rect class="dg-b" x="467" y="140" width="150" height="7" rx="2"/>
<rect class="dg-b" x="467" y="157" width="205" height="7" rx="2"/>
<rect class="dg-b" x="467" y="174" width="180" height="7" rx="2"/>
<rect class="dg-b" x="467" y="191" width="110" height="7" rx="2"/>
<rect class="dg-w" x="463" y="318" width="223" height="66" rx="7"/>
<rect class="dg-b" x="475" y="331" width="110" height="7" rx="2"/>
""" + add_context(478, 365) + agent_pill(491, 354) + """
<rect class="dg-p" x="561" y="354" width="48" height="22" rx="5"/><rect class="dg-b" x="569" y="362" width="30" height="5" rx="2"/>
""" + gear(623, 365, 5) + """
<path d="M664 371l13-6-13-6v4.5l7 1.5-7 1.5z" style="fill:var(--ink3,#6b6b6b)"/>
<rect class="dg-b" x="467" y="392" width="36" height="10" rx="3"/><rect class="dg-b" x="509" y="392" width="36" height="10" rx="3"/><rect class="dg-b" x="551" y="392" width="36" height="10" rx="3"/>
<rect class="dg-c" x="6" y="414" width="688" height="20"/>
<rect class="dg-b2" x="18" y="421" width="50" height="6" rx="3"/><rect class="dg-b2" x="590" y="421" width="90" height="6" rx="3"/>
""" + badge(165, 50, 1) + badge(430, 80, 2) + badge(522, 50, 3) + badge(597, 50, 4) + badge(523, 343, 5)

# A permission request: terminal icon, the command, Allow (with a chevron) and Skip
# (chat/.../chatTerminalToolConfirmationSubPart.ts 208-212; the message itself is only a hover).
perm = ("""
<rect class="dg-w" x="5" y="5" width="450" height="320" rx="8"/>
""" + chat_header(5, 455) + """
<rect class="dg-tn" x="200" y="50" width="240" height="42" rx="7"/>
<rect class="dg-b2" x="212" y="61" width="200" height="7" rx="2"/><rect class="dg-b2" x="212" y="75" width="130" height="7" rx="2"/>
<rect class="dg-w" x="20" y="106" width="420" height="150" rx="7"/>
<path class="dg-ic" d="M38 128l5 5-5 5M48 140h9"/>
<rect class="dg-b2" x="66" y="129" width="180" height="9" rx="2"/>
<rect class="dg-c" x="38" y="156" width="384" height="28" rx="4"/><rect class="dg-b2" x="50" y="166" width="210" height="7" rx="2"/>
<rect class="dg-btn" x="38" y="204" width="88" height="28" rx="5"/><text class="dg-btnt" x="52" y="223">Allow</text>
<line class="dg-btnl" x1="100" y1="208" x2="100" y2="228"/><path class="dg-btnl" d="M107 215l5 5 5-5" style="stroke-width:1.6"/>
<rect class="dg-p" x="134" y="204" width="58" height="28" rx="5"/><text class="dg-t" x="148" y="223">Skip</text>
<rect class="dg-w" x="17" y="272" width="426" height="44" rx="7"/>
""" + agent_pill(41, 284, 64, 22) + add_context(28, 295) + """
<rect class="dg-m" x="30" y="118" width="400" height="74" rx="5"/>
<rect class="dg-m" x="30" y="198" width="168" height="40" rx="5"/>
<path class="dg-ml" d="M430 155h36"/><text class="dg-lab" x="472" y="151">What Copilot will do:</text><text class="dg-lab" x="472" y="169">the command it runs</text>
<path class="dg-ml" d="M198 218h268"/><text class="dg-lab" x="472" y="223">Allow runs it; Skip doesn't</text>
""")

# The trust dialog: the question, the parent-folder box, Yes, I trust the authors on the left on Windows,
# each button with a second line (contrib/workspace/browser/workspace.contribution.ts 424, 471-476).
trust = """
<rect class="dg-c" x="5" y="5" width="470" height="250" rx="8" style="stroke:var(--rule2,#cdcdcd);stroke-width:1.5"/>
<rect class="dg-w" x="30" y="30" width="420" height="190" rx="8"/>
<path class="dg-ic" d="M60 50l12 5v9c0 8-5 13-12 16-7-3-12-8-12-16v-9z"/>
<rect class="dg-b2" x="88" y="54" width="250" height="10" rx="2"/>
<rect class="dg-b" x="88" y="80" width="320" height="7" rx="2"/>
<rect class="dg-b" x="88" y="95" width="290" height="7" rx="2"/>
<rect class="dg-b" x="88" y="110" width="210" height="7" rx="2"/>
<rect class="dg-p" x="88" y="124" width="11" height="11" rx="2"/><rect class="dg-b" x="106" y="127" width="230" height="6" rx="2"/>
<rect class="dg-btn" x="128" y="150" width="172" height="48" rx="5"/><text class="dg-btnt" x="142" y="170">Yes, I trust the authors</text>
<rect x="142" y="180" width="140" height="6" rx="2" style="fill:var(--accent-ink,#fff);fill-opacity:.55"/>
<rect class="dg-p" x="308" y="150" width="130" height="48" rx="5"/><rect class="dg-b2" x="320" y="163" width="100" height="8" rx="2"/><rect class="dg-b" x="320" y="180" width="90" height="6" rx="2"/>
<rect class="dg-m" x="122" y="144" width="184" height="60" rx="6"/>
<path class="dg-ml" d="M214 204v36h271"/><text class="dg-lab" x="492" y="245">Yes, I trust the authors</text>
"""

# Restore Checkpoint: centred on a solid line above the request it undoes, Fork icon after it, never on the
# chat's first request (chat/widget/media/chat.css 4360-4385; chatEditing/chatEditingActions.ts 507-530;
# actions/chatForkActions.ts 34-55).
restore = ("""
<rect class="dg-w" x="5" y="5" width="450" height="250" rx="8"/>
""" + chat_header(5, 455) + """
<rect class="dg-tn" x="250" y="50" width="190" height="30" rx="7"/><rect class="dg-b2" x="262" y="62" width="150" height="7" rx="2"/>
<rect class="dg-b" x="20" y="94" width="200" height="7" rx="2"/>
<rect class="dg-b" x="20" y="110" width="250" height="7" rx="2"/>
<line x1="60" y1="142" x2="164" y2="142" style="stroke:var(--rule2,#cdcdcd);stroke-width:1.2"/>
<line x1="334" y1="142" x2="410" y2="142" style="stroke:var(--rule2,#cdcdcd);stroke-width:1.2"/>
<rect class="dg-p" x="170" y="131" width="130" height="22" rx="5"/><text class="dg-t" x="180" y="146" style="font-size:12px">Restore Checkpoint</text>
<text class="dg-n" x="305" y="146">·</text><circle class="dg-ic" cx="317" cy="137" r="2"/><circle class="dg-ic" cx="325" cy="137" r="2"/><circle class="dg-ic" cx="321" cy="148" r="2"/><path class="dg-ic" d="M317 139v2l4 4M325 139v2l-4 4"/>
<rect class="dg-tn" x="200" y="162" width="240" height="42" rx="7"/>
<rect class="dg-b2" x="212" y="173" width="196" height="7" rx="2"/><rect class="dg-b2" x="212" y="187" width="120" height="7" rx="2"/>
<rect class="dg-b" x="20" y="218" width="180" height="7" rx="2"/>
<rect class="dg-b" x="20" y="234" width="130" height="7" rx="2"/>
<rect class="dg-m" x="164" y="125" width="170" height="34" rx="5"/>
<path class="dg-ml" d="M334 128L366 102h100"/><text class="dg-lab" x="472" y="96">Hover over your last</text><text class="dg-lab" x="472" y="114">request: Restore Checkpoint</text><text class="dg-lab" x="472" y="132">appears above it</text>
""")

# The list of agents, opened from the Agent control: each row an icon then a name, the selected one
# highlighted, custom agents below a divider (platform/actionWidget/browser/actionWidgetDropdown.ts 214;
# actionList.ts _focusCheckedOrFirst).
agents = ("""
<rect class="dg-w" x="5" y="5" width="420" height="370" rx="8"/>
""" + chat_header(5, 425) + """
<rect class="dg-b" x="21" y="56" width="180" height="7" rx="2"/><rect class="dg-b" x="21" y="73" width="240" height="7" rx="2"/>
<rect class="dg-w" x="21" y="100" width="230" height="168" rx="6"/>
<rect class="dg-tn" x="22" y="110" width="228" height="28" rx="0"/>
<path class="dg-ic" d="M38 119 l5 5 -5 5 -5 -5z"/><text class="dg-t" x="51" y="129">Agent</text>
<rect class="dg-b2" x="34" y="148" width="9" height="9" rx="2"/><rect class="dg-b" x="51" y="149" width="70" height="7" rx="2"/>
<rect class="dg-b2" x="34" y="172" width="9" height="9" rx="2"/><rect class="dg-b" x="51" y="173" width="56" height="7" rx="2"/>
<line class="dg-l" x1="29" y1="194" x2="243" y2="194"/>
<text class="dg-t" x="51" y="220">Procedure reviewer</text>
<line class="dg-l" x1="29" y1="232" x2="243" y2="232"/><rect class="dg-b" x="51" y="245" width="90" height="7" rx="2"/>
<rect class="dg-w" x="17" y="280" width="396" height="62" rx="7"/>
<rect class="dg-b" x="31" y="292" width="140" height="7" rx="2"/>
""" + add_context(34, 320) + agent_pill(48, 309, 66, 24) + """
<rect class="dg-p" x="120" y="309" width="54" height="24" rx="5"/><rect class="dg-b" x="129" y="318" width="34" height="5" rx="2"/>
<rect class="dg-m" x="27" y="203" width="214" height="26" rx="4"/>
<rect class="dg-m" x="44" y="305" width="74" height="32" rx="5"/>
<path class="dg-ml" d="M241 216h200"/><text class="dg-lab" x="447" y="221">The custom agent you created</text>
<path class="dg-ml" d="M81 337v23h360"/><text class="dg-lab" x="447" y="365">The control that shows Agent</text>
""")

# --- Parts for the trainings' further drawings; each cites its source, as the parts above do. ---

# The activity bar's icons (Explorer, Search, Source Control, Run, Extensions), as in the window above.
def activity_bar(x, y, h):
    return (strip(x, y, 34, h) +
            '<g transform="translate(%d %d)">' % (x - 6, y - 34) +
            '<path class="dg-ic" d="M17 48h8l4 4v12H17z"/>'
            '<circle class="dg-ic" cx="22" cy="83" r="5"/><path class="dg-ic" d="M26 87l5 5"/>'
            '<circle class="dg-ic" cx="19" cy="108" r="2.5"/><circle class="dg-ic" cx="27" cy="116" r="2.5"/>'
            '<path class="dg-ic" d="M19 111v10M19 118c0-4 8-2 8-4"/>'
            '<path class="dg-ic" d="M18 136l10 6-10 6z"/>'
            '<path class="dg-ic" d="M16 162h6v6h-6zM25 162h6v6h-6zM16 171h6v6h-6zM27 170l4 4-4 4-4-4z"/></g>')


def file_icon(x, y):
    return '<rect class="dg-b2" x="%d" y="%d" width="9" height="11" rx="2"/>' % (x, y)


# The Explorer: EXPLORER, the folder's name in capitals, then folders and files indented under it.
# A chain of folders that each hold only one folder shows as one row, names joined by "\" on Windows,
# because explorer.compactFolders is on by default (contrib/files/browser/files.contribution.ts
# 577-581; the separator, 44-48).
def explorer(x, y, w, h, root, rows, selected=None):
    """rows: (level, name, kind) with kind 'open', 'shut' or 'file'. Returns (svg, row y positions)."""
    out = heading(x + 10, y + 20, "EXPLORER") + text(x + 10, y + 44, "⌄ " + root, bold=True, size=12)
    ys = []
    for i, (level, name, kind) in enumerate(rows):
        ry = y + 66 + 22 * i
        ys.append(ry)
        ix = x + 22 + 12 * level
        if selected == i:
            out += tint(x + 1, ry - 15, w - 2, 21, 0)
        if kind == "file":
            out += file_icon(ix, ry - 10) + text(ix + 15, ry, name)
        else:
            out += text(ix, ry, ("⌄ " if kind == "open" else "› ") + name)
    return out, ys


# The chat box: a line for the request, then Add Context, the agent control, the model picker, the
# tools (gear) and Send, as in the window drawing (parts above; chat/actions/chatContextActions.ts 478-500,
# chat/actions/chatToolActions.ts 130).
def agent_control(x, y, name="Agent", w=None):
    # Built-in agents show their icon; a custom agent has none, so only its name
    # (contrib/chat/common/chatModes.ts 492-494; chat/widget/input/modePickerActionItem.ts 299-314).
    if name == "Agent":
        w = w or (36 + 7 * len(name))
        return ('<rect class="dg-p" x="%d" y="%d" width="%d" height="22" rx="5"/>'
                '<path class="dg-ic" d="M%d %.1fl4.5 4.5-4.5 4.5-4.5-4.5z"/>' % (x, y, w, x + 12, y + 6.5) +
                text(x + 23, y + 15, name, size=12)), w
    w = w or (20 + 7 * len(name))
    return pill(x, y, w) + text(x + 10, y + 15, name, size=12), w


def chat_box(x, y, w, name="Agent", typed=None):
    pill, pw = agent_control(x + 28, y + 36, name)
    out = frame(x, y, w, 66, 7)
    out += text(x + 12, y + 20, typed) if typed else bar(x + 12, y + 13, 110)
    out += add_context(x + 15, y + 47) + pill
    mx = x + 34 + pw
    out += pill_(mx, y + 36, 48) + bar(mx + 8, y + 44, 30, 5)
    out += gear(mx + 62, y + 47, 5)
    out += '<path d="M%d %dl13-6-13-6v4.5l7 1.5-7 1.5z" style="fill:var(--ink3,#6b6b6b)"/>' % (x + w - 22, y + 53)
    return out


def pill_(x, y, w, h=22):
    return pill(x, y, w, h)


# A chat panel: frame, header, an earlier exchange as bars with the learner's request tinted.
def chat_panel(x, y, w, h, request=True):
    out = frame(x, y, w, h) + chat_header(x, x + w, y + 25)
    if request:
        out += tint(x + w - 200, y + 45, 186, 30) + bar(x + w - 188, y + 57, 140, strong=True)
    return out


# An editor: the tab with the file's name, line numbers, the lines as bars.
def editor(x, y, w, h, name):
    out = frame(x, y, w, h, 6) + strip(x + 1, y + 1, w - 2, 26, 5)
    out += '<rect class="dg-w" x="%d" y="%d" width="%d" height="26" style="stroke:none"/>' % (x + 1, y + 1, 24 + 8 * len(name))
    out += '<line x1="%d" y1="%d" x2="%d" y2="%d" style="stroke:var(--accent,#0065b3);stroke-width:2"/>' % (
        x + 1, y + 26, x + 25 + 8 * len(name), y + 26)
    out += text(x + 12, y + 18, name)
    return out


# --- The trainings' further drawings ---

# Open Preview: right-click a Markdown file in the Explorer; Open Preview is in the menu's first group,
# with the other ways to open it (extensions/markdown-language-features/package.json 630-635). Other items are bars.
_ex, _ys = explorer(41, 34, 200, 230, "COPILOT-PRACTICE", [(0, "notes", "shut"), (0, "actions.md", "file")], selected=1)
open_preview = (frame(5, 5, 690, 270) + activity_bar(6, 34, 240) + rule(241, 34, 241, 274) + _ex +
    frame(170, 96, 230, 168, 6) + text(184, 118, "Open Preview") + bar(184, 130, 110) + bar(184, 144, 130) + bar(184, 158, 96) +
    rule(176, 172, 394, 172) + bar(184, 184, 140) + bar(184, 200, 96) + rule(176, 214, 394, 214) +
    bar(184, 228, 120) + bar(184, 246, 150) +
    outline(176, 102, 218, 26) + leader([(394, 115), (466, 115)]) +
    label(472, 110, ["Right-click actions.md, then", "select Open Preview"]))

# New Chat (+) in the chat's title row (chat_header's source).
new_chat = (chat_panel(5, 5, 450, 250) + bar(21, 92, 220) + bar(21, 108, 260) + bar(21, 124, 190) +
    chat_box(17, 176, 426) +
    outline(364, 16, 34, 28) + leader([(381, 16), (381, 10), (480, 10)]) + label(486, 15, "New Chat (+)"))

# The skill's file in the Explorer: three folders on one row (contrib/files/browser/files.contribution.ts
# 577-581).
def compact_file(root, chain, leaf, other, lab):
    ex, ys = explorer(41, 34, 300, 170, root, [(0, chain, "open"), (1, leaf, "file"), (0, other, "shut")], selected=1)
    return (frame(5, 5, 690, 210) + activity_bar(6, 34, 180) + rule(341, 34, 341, 214) + ex +
            outline(47, ys[0] - 17, 288, 47) + leader([(335, ys[0] + 6), (420, ys[0] + 6)]) + label(426, ys[0] + 1, lab))

skill_file = compact_file("SKILLS-PRACTICE", ".github\\skills\\meeting-summary", "SKILL.md", "notes",
                          ["Expand .github until SKILL.md", "shows, then select it"])
agent_file = compact_file("AGENTS-PRACTICE", ".github\\agents", "procedure-reviewer.agent.md", "procedures",
                          ["Expand .github until the agent's", "file shows, then select it"])

# Going back to Agent from a custom agent: the list as in list-of-agents, the custom agent's row
# highlighted because it is the selected one (platform/actionWidget/browser/actionWidgetDropdown.ts 214).
back_to_agent = (chat_panel(5, 5, 420, 370, request=False) +
    '<rect class="dg-b" x="21" y="56" width="180" height="7" rx="2"/><rect class="dg-b" x="21" y="73" width="240" height="7" rx="2"/>'
    '<rect class="dg-w" x="21" y="100" width="230" height="168" rx="6"/>'
    '<path class="dg-ic" d="M38 119 l5 5 -5 5 -5 -5z"/><text class="dg-t" x="51" y="129">Agent</text>'
    '<rect class="dg-b2" x="34" y="148" width="9" height="9" rx="2"/><rect class="dg-b" x="51" y="149" width="70" height="7" rx="2"/>'
    '<rect class="dg-b2" x="34" y="172" width="9" height="9" rx="2"/><rect class="dg-b" x="51" y="173" width="56" height="7" rx="2"/>'
    '<line class="dg-l" x1="29" y1="194" x2="243" y2="194"/>' +
    tint(22, 202, 228, 28, 0) + '<path class="dg-ic" d="M34 216l3 3 6-7"/>' + text(51, 221, "Procedure reviewer") +
    '<line class="dg-l" x1="29" y1="232" x2="243" y2="232"/><rect class="dg-b" x="51" y="245" width="90" height="7" rx="2"/>' +
    chat_box(17, 280, 396, "Procedure reviewer") +
    outline(27, 110, 214, 26, 4) + outline(40, 311, 158, 30) +
    leader([(241, 123), (441, 123)]) + label(447, 128, "Agent") +
    leader([(121, 342), (121, 360), (441, 360)]) + label(447, 356, ["The control that shows", "Procedure reviewer"]))

# A handoff after the reply: "Proceed from {agent}", then one button per handoff, between the reply
# and the chat box (chat/widget/chatContentParts/chatSuggestNextWidget.ts 85-86, 130-136;
# chat/widget/chatWidget.ts 1166-1171). The reply is bars.
handoff = (chat_panel(5, 5, 450, 330) +
    bar(21, 92, 300) + bar(21, 108, 260) + bar(21, 124, 330) + bar(21, 140, 200) + bar(21, 156, 240) +
    text(21, 196, "Proceed from Procedure reviewer", muted=True, size=12) +
    pill(21, 206, 170, 28) + text(35, 225, "Fix the unclear steps", size=12) +
    chat_box(17, 252, 426, "Procedure reviewer") +
    outline(15, 182, 220, 58) + leader([(235, 211), (480, 211)]) +
    label(486, 206, ["After the reviewer's reply:", "Fix the unclear steps"]))

# The line of small text above a server in .mcp.json: Start while stopped, Running once started
# (contrib/mcp/browser/mcpLanguageFeatures.ts 331-345, 365).
start_line = (frame(5, 5, 690, 250) + activity_bar(6, 34, 220) + rule(41, 34, 41, 254) +
    editor(48, 40, 400, 205, ".mcp.json") +
    '<g class="dg-n" style="font-size:11px">' + "".join('<text x="58" y="%d">%d</text>' % (yy, n) for n, yy in ((1, 92), (2, 114), (3, 151), (4, 173), (5, 195), (6, 217))) + '</g>' +
    bar(80, 85, 12) + bar(96, 107, 110) +
    '<path class="dg-ic" d="M114 121l7 4-7 4z" style="stroke-width:1.2"/>' + text(126, 129, "Start", muted=True, size=11) + text(168, 129, "|  More...", muted=True, size=11) +
    text(112, 151, '"github": {', size=12) + bar(128, 166, 220) + bar(128, 188, 150) + bar(112, 210, 14) +
    outline(106, 115, 56, 20, 4) + leader([(134, 135), (134, 140), (480, 140)]) +
    label(486, 135, ["Select Start. It then", "says Running"]))

# The tool lines in a reply: a folded line whose wording varies, opened, then "Ran List commits"
# among the tools the reply used (contrib/mcp/common/mcpLanguageModelToolContribution.ts 250;
# github/github-mcp-server pkg/github/repositories.go 239-243).
tool_lines = (chat_panel(5, 5, 450, 300) +
    '<path class="dg-ic" d="M21 100l3 3 6-7"/>' + bar(37, 96, 170, strong=True) +
    '<line class="dg-l" x1="27" y1="112" x2="27" y2="176"/>' +
    '<rect class="dg-b2" x="39" y="119" width="10" height="10" rx="2"/>' + bar(58, 121, 120) +
    '<rect class="dg-b2" x="39" y="141" width="10" height="10" rx="2"/>' + text(58, 152, "Ran List commits", size=12) +
    '<rect class="dg-b2" x="39" y="163" width="10" height="10" rx="2"/>' + bar(58, 165, 100) +
    bar(21, 198, 330) + bar(21, 214, 280) +
    chat_box(17, 228, 426) +
    outline(33, 136, 150, 24, 4) + leader([(183, 148), (480, 148)]) +
    label(486, 128, ["Select the folded line to see", "each tool: Ran List commits"]))

# Ideas (Explain drawings), in the style of request-matches-a-skill.svg, from the shared Explain parts.
where_skill_works = (
    caption(0, 16, "Saved in a folder") +
    card(0, 28, 104, 58, ["one", "folder"], "hit", bold=True) +
    card(114, 28, 104, 58, ["another", "folder"], "dim") + card(228, 28, 104, 58, ["another", "folder"], "dim") +
    caption(0, 112, "Works while that folder is open.") + caption(0, 130, "Anyone who opens the folder has it.") +
    caption(368, 16, "Saved in your personal skills folder") +
    card(368, 28, 104, 58, ["one", "folder"], "hit", bold=True) +
    card(482, 28, 104, 58, ["another", "folder"], "hit", bold=True) + card(596, 28, 104, 58, ["another", "folder"], "hit", bold=True) +
    caption(368, 112, "Works in every folder you open.") + caption(368, 130, "For you only."))

instructions_or_skill = (
    caption(0, 16, "Custom instructions") +
    card(0, 28, 150, 40, "A request", "req") + card(0, 78, 150, 40, "A request", "req") +
    card(0, 128, 150, 40, "A request", "req") +
    arrow([(150, 48), (170, 48), (170, 98), (196, 98)]) + arrow([(150, 98), (196, 98)]) +
    arrow([(150, 148), (170, 148), (170, 98), (196, 98)]) +
    card(196, 70, 140, 56, ["Custom", "instructions"], "hit", bold=True) +
    caption(0, 196, "Read with every request in the folder") +
    caption(368, 16, "A skill") +
    card(368, 28, 150, 40, ["Summarize the", "meeting notes"], "req") + card(368, 78, 150, 40, "A request", "req") +
    card(368, 128, 150, 40, "A request", "req") +
    arrow([(518, 48), (538, 48), (538, 98), (564, 98)]) +
    faint([(518, 98), (532, 98)]) + faint([(518, 148), (532, 148)]) +
    card(564, 70, 136, 56, ["meeting-", "summary skill"], "hit", bold=True) +
    caption(368, 196, "Read only when a request matches it"))

connection_tools = (
    card(0, 98, 110, 48, "Copilot", "req", bold=True) +
    arrow([(110, 122), (130, 122), (130, 64), (164, 64)]) + arrow([(110, 122), (130, 122), (130, 188), (164, 188)]) +
    caption(164, 16, "Its own tools") +
    card(164, 26, 170, 32, "Read a file") + card(164, 64, 170, 32, "Change a file") + card(164, 102, 170, 32, "Run a command") +
    caption(164, 166, "Added by the connection") +
    card(164, 176, 170, 32, "List commits", "hit") + card(164, 214, 170, 32, ["Other look-ups"], "card") +
    arrow([(334, 192), (420, 192)]) +
    card(420, 168, 120, 48, "GitHub", "card", bold=True) +
    caption(420, 238, "Its tools only look things up."))

# Asked not to change a file, Copilot still has the tool; a custom agent given only the reading
# tools does not have it (vscode-docs custom-agents.md, "tools"; the page's own two bullets).
asked_or_taken_away = (
    text(0, 16, "Asked not to change a file", bold=True, size=14) +
    caption(0, 34, "by a request, custom instructions or a skill") +
    card(0, 70, 110, 48, "Copilot", "req", bold=True) +
    arrow([(110, 94), (130, 94), (130, 64), (164, 64)]) + arrow([(110, 94), (130, 94), (130, 124), (164, 124)]) +
    card(164, 46, 150, 36, "Read files") + card(164, 106, 150, 36, "Change files", "hit", bold=True) +
    caption(0, 172, "Still has the tool. It can change the file.") +
    text(368, 16, "A custom agent", bold=True, size=14) +
    caption(368, 34, "given only the tools for reading files") +
    card(368, 70, 110, 48, "Copilot", "req", bold=True) +
    arrow([(478, 94), (498, 94), (498, 64), (532, 64)]) +
    card(532, 46, 150, 36, "Read files") + card(532, 106, 150, 36, "Change files", "dim") +
    caption(368, 172, "Doesn't have the tool. It can't change the file."))

# A request is checked against each skill's description; the one that matches has its
# instructions followed (vscode-docs agent-skills.md, "How Copilot uses skills").
request_matches_a_skill = (
    caption(0, 16, "Your request") +
    card(0, 26, 176, 52, ["“Summarize the", "meeting notes.”"], "req") +
    caption(236, 16, "The description of each skill you have") +
    card(236, 26, 220, 40, "Check a new document", "dim") +
    card(236, 76, 220, 40, "Summarize meeting notes", "hit", bold=True) +
    card(236, 126, 220, 40, "Make the weekly summary", "dim") +
    faint([(176, 52), (206, 52), (206, 46), (236, 46)]) +
    arrow([(176, 52), (206, 52), (206, 96), (236, 96)]) +
    faint([(176, 52), (206, 52), (206, 146), (236, 146)]) +
    arrow([(456, 96), (508, 96)]) +
    caption(516, 16, "Copilot follows") +
    '<rect class="dg-x-hit" x="516" y="26" width="188" height="140" rx="6"/>' +
    text(528, 50, "Its instructions", bold=True, size=14) +
    "".join(caption(528, 74 + 18 * i, t) for i, t in enumerate(
        ["Lead with the decisions.", "Then list the actions, each", "with its owner and due date.",
         "After each item, name the", "note it came from."])))

# Custom instructions, a skill or a custom agent: which requests each goes with (the page's own
# list; vscode-docs custom-instructions.md, agent-skills.md, custom-agents.md).
def _which(x, title, purpose, source, reach, caption_words):
    """reach: for each of three requests, 'hit' (the source goes with it) or 'dim'."""
    out = text(x, 16, title, bold=True, size=14) + caption(x, 34, purpose)
    out += card(x + 30, 48, 160, 40, source, "hit", bold=True)
    for i, kind in enumerate(reach):
        tx = x + 4 + 74 * i
        cx = tx + 32
        if kind == "hit":
            out += arrow([(x + 110, 88), (x + 110, 106), (cx, 106), (cx, 130)])
        else:
            out += faint([(x + 110, 88), (x + 110, 106), (cx, 106), (cx, 128)])
        out += card(tx, 130, 64, 34, "request", "dim" if kind == "dim" else "req")
    return out + caption(x, 188, caption_words)


which_one = (
    _which(0, "Custom instructions", "The same rules for a folder", "Instructions",
           ["hit", "hit", "hit"], "Every request in the folder") +
    _which(242, "A skill", "A task you repeat", "A skill", ["dim", "hit", "dim"],
           "A request that matches it") +
    _which(484, "A custom agent", "One role for a whole chat", "A custom agent", ["hit", "hit", "hit"],
           "Every request while it's selected"))

# One chat box everywhere: these drawings use chat_box.
perm = perm.replace('<rect class="dg-w" x="5" y="5" width="450" height="320" rx="8"/>',
                    '<rect class="dg-w" x="5" y="5" width="450" height="336" rx="8"/>')
perm = perm.replace('<rect class="dg-w" x="17" y="272" width="426" height="44" rx="7"/>\n', "")
perm = perm.replace(agent_pill(41, 284, 64, 22) + add_context(28, 295), chat_box(17, 266, 426))
agents = agents.replace('<rect class="dg-w" x="17" y="280" width="396" height="62" rx="7"/>\n<rect class="dg-b" x="31" y="292" width="140" height="7" rx="2"/>\n', "")
agents = agents.replace(add_context(34, 320) + agent_pill(48, 309, 66, 24) + """
<rect class="dg-p" x="120" y="309" width="54" height="24" rx="5"/><rect class="dg-b" x="129" y="318" width="34" height="5" rx="2"/>""",
                        chat_box(17, 276, 396))
agents = agents.replace('<rect class="dg-m" x="44" y="305" width="74" height="32" rx="5"/>',
                        '<rect class="dg-m" x="39" y="306" width="83" height="34" rx="5"/>')
agents = agents.replace('<path class="dg-ml" d="M81 337v23h360"/>', '<path class="dg-ml" d="M81 340v20h360"/>')
agents = agents.replace("The custom agent you created", "Procedure reviewer")

# list-of-agents gains New Chat (+): the step selects it first.
agents_with_new_chat = agents + outline(334, 21, 34, 28) + leader([(351, 21), (351, 12), (441, 12)]) + label(447, 17, "New Chat (+)")


DRAWINGS = {
 "getting-started/images/vs-code-window.svg": (700, 440, "The VS Code window: the list on the left, a file and the chat", window),
 "getting-started/images/permission-request.svg": (700, 346, "A permission request in the chat", perm),
 "getting-started/images/trust-question.svg": (700, 260, "The question whether you trust the authors of a folder", trust),
 "getting-started/images/restore-checkpoint.svg": (700, 260, "Restore Checkpoint above your last request", restore),
 "agents/images/list-of-agents.svg": (700, 380, "The list of agents, open above the Agent control", agents_with_new_chat),
 "getting-started/images/open-preview.svg": (700, 280, "Open Preview in the menu of a Markdown file", open_preview),
 "getting-started/images/new-chat.svg": (700, 260, "New Chat at the top of the chat", new_chat),
 "skills-in-depth/images/skill-file.svg": (700, 220, "The skill's file in the list on the left", skill_file),
 "skills-in-depth/images/where-a-skill-works.svg": (700, 140, "Where a skill works", where_skill_works),
 "skills-in-depth/images/instructions-or-skill.svg": (700, 204, "Custom instructions and a skill", instructions_or_skill),
 "agents/images/agent-file.svg": (700, 220, "The custom agent's file in the list on the left", agent_file),
 "agents/images/back-to-agent.svg": (700, 380, "Going back to Agent from the Procedure reviewer", back_to_agent),
 "agents/images/handoff.svg": (700, 340, "The handoff button after the reviewer's reply", handoff),
 "connecting/images/connection-tools.svg": (700, 250, "Copilot's own tools and the ones a connection adds", connection_tools),
 "connecting/images/start-line.svg": (700, 260, "Start above the server in .mcp.json", start_line),
 "agents/images/asked-or-taken-away.svg": (704, 184, "Asked not to change a file, or given only the reading tools", asked_or_taken_away),
 "skills-in-depth/images/request-matches-a-skill.svg": (704, 172, "A request is matched to a skill by its description", request_matches_a_skill),
 "agents/images/which-one.svg": (704, 200, "Which requests custom instructions, a skill and a custom agent go with", which_one),
 "connecting/images/tool-lines.svg": (700, 310, "The tools Copilot ran, in its reply", tool_lines),
}
if __name__ == "__main__":
    write(KIT, DRAWINGS)
