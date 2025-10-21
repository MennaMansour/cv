import json
import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.lines as mlines

# -------------------------------
# Palette / styles
BG_PAGE = "#F5F7FA"        # page background
TITLE_COLOR = "#2C3E50"
TEXT_COLOR = "#34495E"
PRIMARY = "#3498DB"        # primary button
SECONDARY = "#95A5A6"      # back button
WARN = "#E67E22"
SUCCESS = "#27AE60"
INFOBOX_BG = "white"
INFOBOX_FG = TITLE_COLOR

# -------------------------------
# Load Data
# -------------------------------
with open("events_log_2.json", "r") as f:
    events_data = json.load(f)

with open("possessions_20_10.json", "r") as f:
    possessions = json.load(f)
with open("stage_log_20_10.json", "r") as f:
    stages_data = json.load(f)

#########################
def safe_loc(loc):
    """Convert a location value to a readable string."""
    if loc is None:
        return "N/A"
    if isinstance(loc, (list, tuple)):
        # If both are numbers → display them
        if all(isinstance(x, (int, float)) for x in loc):
            return f"({loc[0]:.2f}, {loc[1]:.2f})"
        # If values are strings like center, circle
        return " ".join(str(x) for x in loc)
    return str(loc)


def safe_value(val, default="Unknown"):
    """Convert null/empty to a textual default value."""
    return val if val not in [None, ""] else default

# -------------------------------
# change frame into timed
# -------------------------------
FPS = 25  

def frame_to_time(frame):
    """Convert a frame number to time in mm:ss.s format."""
    if frame is None or frame == "" or frame == "N/A":
        return ""
    seconds = frame / FPS
    minutes = int(seconds // 60)
    sec = seconds % 60
    return f"{minutes:02d}:{sec:04.1f}"
# -----------------------------
# Helpers & Pitch Drawing
# -----------------------------
def draw_pitch(ax, length=105, width=68):
    # 🎨 Better-looking pitch
    ax.clear()
    ax.set_xlim(0, width)
    ax.set_ylim(0, length)
    ax.set_aspect('equal')
    ax.set_facecolor("#228B22")  # natural green

    # pitch lines
    ax.plot([0, width], [0, 0], color="white", lw=1.5)
    ax.plot([0, width], [length, length], color="white", lw=1.5)
    ax.plot([0, 0], [0, length], color="white", lw=1.5)
    ax.plot([width, width], [0, length], color="white", lw=1.5)
    ax.plot([0, width], [length/2, length/2], color="white", linestyle="--", lw=1.5)

    # center circle
    ax.add_patch(plt.Circle((width/2, length/2), 9.15, fill=False, color="white", lw=1.5))

    ax.add_patch(patches.Rectangle(((width/2)-20.15, 0), 40.3, 16.5,
                                   fill=False, edgecolor="white", lw=2))
    ax.add_patch(patches.Rectangle(((width/2)-20.15, length-16.5), 40.3, 16.5,
                                   fill=False, edgecolor="white", lw=2))

def scale_coords(x, y, max_x=80, max_y=120):
    return x * (68/max_x), y * (105/max_y)

def normalize_coords(x, y, width=68, length=105):
    try:
        x = float(x)
        y = float(y)
    except Exception:
        return None
    
    # clamp coordinates to pitch bounds
    if x > width:
        x = width
    if y > length:
        y = length
    if x < 0:
        x = 0
    if y < 0:
        y = 0

    return x, y

# -------------------------------
# new helper: handle special (text) locations like ["center","circle"]
def resolve_loc(loc, width=68, length=105):
    """
    Accepts loc which can be:
      - numeric list [x,y]
      - text list like ["center","circle"]
      - string or special values (extendable for other maps)
    Returns (x,y) or None.
    """
    if loc is None:
        return None

    # if already numeric list/tuple
    if isinstance(loc, (list, tuple)) and len(loc) >= 2 and all(isinstance(x, (int, float)) for x in loc[:2]):
        return normalize_coords(loc[0], loc[1], width=width, length=length)

    # if text-like list/tuple such as ["center","circle"]
    if isinstance(loc, (list, tuple)) and len(loc) >= 2 and all(isinstance(x, str) for x in loc[:2]):
        a = loc[0].lower()
        b = loc[1].lower()
        # center circle -> pitch center
        if a == "center" and b == "circle":
            return normalize_coords(width/2, length/2, width=width, length=length)
        # add more generic maps here if needed
        # ex: if a == "bottom" and b == "goal-area": ...
        return None

    # if location is a single string
    if isinstance(loc, str):
        s = loc.lower()
        if s == "bottom-goal-area":
            return (width/2, 5)
        if s == "top-goal-area":
            return (width/2, length-5)
        # add other rules as required
        return None

    return None

# -------------------------------
# Legends
# -------------------------------
def draw_event_legend(ax):
    elems = [
        mlines.Line2D([], [], marker='x', color='#4B0082', linestyle='None', markersize=8, label="Foul"),
        mlines.Line2D([], [], marker='^', color='#00008B', linestyle='None', markersize=8, label="Corner Kick"),
        mlines.Line2D([], [], marker='o', color='#000000', linestyle='None', markersize=8, label="Goal Kick"),
        mlines.Line2D([], [], marker='s', color='#009E73', linestyle='None', markersize=8, label="Throw-in"),
        mlines.Line2D([], [], marker='D', color='#F0E442', linestyle='None', markersize=8, label="Kick-off"),
    ]
    ax.legend(handles=elems, loc="center left", bbox_to_anchor=(1.02, 0.5),
              frameon=True, fontsize=10, title="Event Legend", title_fontsize=11)

def draw_possession_legend(ax):
    elems = [
        mlines.Line2D([], [], marker='o', color='#000000', linestyle='None', markersize=10, label="Start of Possession"),
        mlines.Line2D([], [], marker='o', color='#FFFF00', linestyle='None', markersize=10, label="End of Possession"),
        mlines.Line2D([], [], marker='^', color='blue', linestyle='None', markersize=10, label="Receive"),
        mlines.Line2D([], [], color='#00FFFF', lw=2, label="Controlled Pass"),
        mlines.Line2D([], [], marker='x', color='orange', linestyle='None', markersize=8, label="Pass Intercepted"),
        mlines.Line2D([], [], color='red', lw=2, label="Pass leading to Throw-in"),
        mlines.Line2D([], [], color='red', marker=r'',markersize=0, label='Pass before Interception'),
        mlines.Line2D([], [], color='purple', lw=2, marker="o", markersize=5, label="Dribble Path"),
        mlines.Line2D([], [], color='#E67E22', lw=2, marker=">", markersize=6, label="Shot"),


    ]
    ax.legend(handles=elems, loc="center left", bbox_to_anchor=(1.02, 0.5),
              frameon=True, fontsize=10, title="Possession Legend", title_fontsize=11)
#-----------------------------------------------------------
def show_intercepted_pass_only():
    global selected_pos
    idx = possession_combo.current()
    if idx < 0:
        messagebox.showwarning("No Selection", "Please select a possession first.")
        return
    selected_pos = filtered_possessions[idx]

    draw_pitch(ax)

    actions = selected_pos.get("actions", [])
    found = False

    for i, act in enumerate(actions):
        typ = str(act.get("type", "")).lower()
        if "intercept" in typ or "pass_intercepted" in typ:
            found = True
            loc = act.get("location_m") or act.get("end_location_m")
            norm = resolve_loc(loc)
            if norm:
                x, y = norm
                ax.plot(x, y, "x", color="orange", markersize=12, zorder=5)
                ax.text(x+1, y+1, "Intercepted", fontsize=10, color="black",
                        weight="bold", bbox=dict(facecolor="white", alpha=0.6, edgecolor="none", pad=0.2))

            # ⛔️ the red arrow for the intercepted pass (use start/end from same event if available)
            start_loc = act.get("start_location_m")
            end_loc = act.get("end_location_m")
            s_norm = resolve_loc(start_loc)
            e_norm = resolve_loc(end_loc)
            if s_norm and e_norm:
                dx = e_norm[0] - s_norm[0]
                dy = e_norm[1] - s_norm[1]
                ax.arrow(s_norm[0], s_norm[1], dx, dy,
                         head_width=1.0, head_length=1.5,
                         length_includes_head=True,
                         fc="red", ec="red", linewidth=2, zorder=3)

            # 🎯 get the last pass before the interception
            if i > 0:
                prev_act = actions[i-1]
                prev_typ = str(prev_act.get("type", "")).lower()
                if "controlled_pass" in prev_typ:
                    ps = prev_act.get("start_location_m")
                    pe = prev_act.get("end_location_m")
                    ps_norm = resolve_loc(ps)
                    pe_norm = resolve_loc(pe)
                    if ps_norm and pe_norm:
                        dx = pe_norm[0] - ps_norm[0]
                        dy = pe_norm[1] - ps_norm[1]
                        ax.arrow(ps_norm[0], ps_norm[1], dx, dy,
                                 head_width=1.0, head_length=1.5,
                                 length_includes_head=True,
                                 fc="red", ec="red", linewidth=2, zorder=3)


    # 📦 the black info box above the pitch
    if found:
        start_team = selected_pos.get("team", "Unknown")
        end_team = selected_pos.get("end_team", "Unknown")
        end_reason = selected_pos.get("end_reason", "N/A")
        start_frame = selected_pos.get("start_frame", "N/A")
        end_frame = selected_pos.get("end_frame", "N/A")
        start_time = frame_to_time(start_frame)
        end_time = frame_to_time(end_frame)

        text = (
            f"Start Team: {start_team}\n"
            f"End Team: {end_team}\n"
            f"End Reason: {end_reason}\n"
            f"Time: {start_time} → {end_time}"
        )

        ax.text(70, 90, text,
                ha="left", va="center", fontsize=18, color="white", weight="bold",
                bbox=dict(facecolor="black", alpha=0.6, boxstyle="round,pad=0.3"))

    if not found:
        messagebox.showinfo("No Interception", "⚠️ This possession has no intercepted pass.")

    canvas.draw()

# -------------------------------
# Plot Possession
# -------------------------------
def plot_possession(ax, pos):
    actions = pos.get("actions", []) or []
    valid = []

    start_loc = pos.get("start_location_m")
    end_loc = pos.get("end_location_m")

    start_norm = resolve_loc(start_loc) if start_loc else None
    end_norm = resolve_loc(end_loc) if end_loc else None

    for act in actions:
        loc = act.get("location_m") or act.get("start_location_m") or act.get("end_location_m")
        norm = resolve_loc(loc)
        if norm is not None:
            valid.append((act, norm))

    if not valid and not start_norm:
        return

    seen_labels = []

    # 🎯 START marker
    if start_norm:
        x, y = start_norm
        ax.plot(x, y, "o", color="#000000", markersize=7, zorder=5)
        # move the word START a bit to the right of the circle to keep it clear
        ax.text(x + 1.0, y, "START", fontsize=7, color="white", weight="bold", zorder=6)

    for idx, (act, (x, y)) in enumerate(valid):
        typ = str(act.get("type", "")).lower()
        player_num = act.get("player_number") or act.get("player") or idx

        if typ == "receive":
            ax.plot(x, y, "^", color='blue', markersize=7.5, zorder=5)
            duplicate = any(p == player_num and abs(px - x) < 1 and abs(py - y) < 1 for p, px, py in seen_labels)
            if not duplicate:
                ax.text(x, y + 1.0, str(player_num), fontsize=7, color="white",
                        weight="bold", ha="center", va="bottom", zorder=6)
                seen_labels.append((player_num, x, y))
        elif "controlled_pass" in typ:
            start_loc = act.get("start_location_m")
            end_loc = act.get("end_location_m")
            s_norm = resolve_loc(start_loc)
            e_norm = resolve_loc(end_loc)
            if s_norm and e_norm:
                dx = e_norm[0] - s_norm[0]
                dy = e_norm[1] - s_norm[1]

                # 👇 determine the color here:
                next_act = actions[idx + 1] if idx + 1 < len(actions) else None
                next_typ = str(next_act.get("type", "")).lower() if next_act else ""

                end_reason = pos.get("end_reason", "").lower()

                # ✅ if the possession ended with a Throw-in and it's the last action → last pass is red
                if end_reason == "throw-in" and idx == len(actions) - 2:
                    color = "red"
                elif "intercept" in next_typ or "pass_intercepted" in next_typ:
                    color = "red"
                else:
                    color = "#00FFFF"

                ax.arrow(s_norm[0], s_norm[1], dx, dy,
                        head_width=1.0, head_length=1.5,
                        length_includes_head=True,
                        fc=color, ec=color, alpha=0.9,
                        linewidth=1.5, zorder=3)


        elif "intercept" in typ or "pass_intercepted" in typ:
            ax.plot(x, y, "x", color="orange", markersize=8, zorder=5)
            interceptor = act.get("by_team") or act.get("interceptor_team") or act.get("team") or pos.get("end_team") or "Unknown"
            ax.text(x + 1.0, y + 1.0, str(interceptor), fontsize=8, color="black",
                    weight="bold", zorder=6, ha="left", va="bottom",
                    bbox=dict(facecolor="white", alpha=0.6, edgecolor="none", pad=0.2))
            try:
                info_box.config(state="normal")
                info_box.insert(tk.END, f"Pass intercepted by: {interceptor} at ({x:.2f}, {y:.2f})\n")
                info_box.see(tk.END)
                info_box.config(state="disabled")
            except Exception:
                pass
        elif "dribble" in typ:
            path = act.get("path")
            if path and isinstance(path, list):
                norm_path = [resolve_loc(p) for p in path if p]
                norm_path = [p for p in norm_path if p]
                if len(norm_path) >= 2:
                    xs, ys = zip(*norm_path)

                    dx = xs[-1] - xs[0]
                    dy = ys[-1] - ys[0]


                    if abs(dx) >= 2 or abs(dy) >= 2:
                        ax.plot(xs, ys, color="purple", linewidth=2, marker="o", markersize=3, zorder=4)
                        ax.text(xs[-1]+0.8, ys[-1]+0.8, str(player_num),
                                fontsize=7, color="white", weight="bold",
                                bbox=dict(facecolor="purple", alpha=0.5, edgecolor="none", pad=0.2))
                else:
                    
                    if path and len(path) == 1:
                        ax.plot(x, y, marker=".", color="purple", markersize=8, zorder=5)

        elif "shot" in typ:
            start_loc = act.get("start_location_m")
            end_loc = act.get("end_location_m")
            s_norm = resolve_loc(start_loc)
            e_norm = resolve_loc(end_loc)
            if s_norm and e_norm:
                dx = e_norm[0] - s_norm[0]
                dy = e_norm[1] - s_norm[1]
                ax.arrow(s_norm[0], s_norm[1], dx, dy,
                        head_width=1.5, head_length=2.0,
                        length_includes_head=True,
                        fc="#E67E22", ec="#E67E22", linewidth=2.5, zorder=4)

                # 🟢 SHOT
                outcome = act.get("outcome") or act.get("result") or act.get("outcome_name") or "Shot"
                outcome_text = str(outcome).upper()

                ax.text(e_norm[0]+0.5, e_norm[1]+0.5, outcome_text,
                        fontsize=8, color="white", weight="bold",
                        bbox=dict(facecolor="#E67E22", alpha=0.7, edgecolor="none", pad=0.2))

    # 🎯 END marker
    if end_norm:
        x, y = end_norm
        ax.plot(x, y, "o", color="#FFFF00", markersize=7, zorder=5)
        # move the word END slightly left of the circle to keep it clear
        ax.text(x - 1.0, y, "END", fontsize=7, color="white", weight="bold", ha="right", zorder=6)


        start_team = selected_pos.get("team", "Unknown")
        end_team = selected_pos.get("end_team", "Unknown")
        end_reason = selected_pos.get("end_reason", "N/A")
        start_frame = selected_pos.get("start_frame", "N/A")
        end_frame = selected_pos.get("end_frame", "N/A")
        start_time = frame_to_time(start_frame)
        end_time = frame_to_time(end_frame)

        text = (
            f"Start Team: {start_team}\n"
            f"End Team: {end_team}\n"
            f"Reason: {end_reason}\n"
            f"Time: {start_time} → {end_time}"
        )

      
        ax.text(70,100 , text,
                ha="left", va="top",
                fontsize=13, color="white", weight="bold",
                bbox=dict(facecolor="black", alpha=0.7, boxstyle="round,pad=0.4"),
                transform=ax.transData)


    # 🎨 Draw legend after box
    draw_possession_legend(ax)
    canvas.draw()



# -------------------------------
# Filter Possessions
# -------------------------------
def filter_possessions(team):
    return [pos for pos in possessions if team == "Both" or pos.get("team") == team]
def get_stages_for_possession(possession_id):
    """Return all stages that belong to the given possession_id."""
    related = [s for s in stages_data if s.get("possession_id") == possession_id]
    return related


# -------------------------------
# UI helper stubs (to avoid crashes)
# -------------------------------
def show_event_counts(team):
    draw_pitch(ax)

    counts = {}
    for ev in events_data:
        if team == "Both" or ev["team"] == team:
            counts[ev["event"]] = counts.get(ev["event"], 0) + 1

    info_box.config(state="normal")
    info_box.delete("1.0", tk.END)
    info_box.insert(tk.END, f"=== EVENT COUNTS ({team}) ===\n", "title")
    info_box.insert(tk.END, "-" * 60 + "\n", "separator")
    for ev_type, count in counts.items():
        info_box.insert(tk.END, f"{ev_type:<15}: {count}\n", "subtitle")
    info_box.config(state="disabled")

# -------------------------------
# Selected possession show
# -------------------------------
def show_selected_possession():
    global selected_pos
    idx = possession_combo.current()
    if idx < 0:
        messagebox.showwarning("No Selection", "Please select a possession first.")
        return
    selected_pos = filtered_possessions[idx]

    draw_pitch(ax)
    plot_possession(ax, selected_pos)
    
    canvas.draw()

# -------------------------------
# Draw Selected Events
# -------------------------------
def draw_selected_events(event_type, team):
    draw_pitch(ax)

    if team == "Both":
        teams_text = " | ".join(set(ev.get("team", "") for ev in events_data))
    else:
        teams_text = team

    ax.text(34, 108, teams_text,
            ha="center", va="center",
            fontsize=20, weight="bold",
            color="black",
            bbox=dict(facecolor="white", alpha=0.7, edgecolor="none", boxstyle="round,pad=0.3"))


    draw_event_legend(ax)

    filtered = [
        ev for ev in events_data
        if (team == "Both" or ev.get("team") == team)
        and ev.get("event", "").lower() == event_type.lower()
    ]


    area_map = {
        "bottom-goal-area": (34, 5),
        "top-goal-area": (34, 100),
        "left-corner": (0, 0),
        "right-corner": (68, 0)
    }


    for ev in filtered:
        loc = ev.get("location")
        if isinstance(loc, list) and len(loc) >= 2:
            norm = resolve_loc(loc)
            if norm is None:
                continue
            x, y = norm
        elif isinstance(loc, str) and loc in area_map:
            x, y = area_map[loc]
        else:
            continue

        et = event_type.lower()

        if et == "foul":
            ax.plot(x, y, marker="x", color='#4B0082', markersize=8, mew=2)
        elif et == "corner kick":
            ax.plot(x, y, marker="^", color='#00008B', markersize=10)
        elif et == "goal kick":
            ax.plot(x, y, marker="o", color='#000000', markersize=12,
                    markeredgecolor="white", zorder=5)
        elif et == "throw-in":
            ax.plot(x, y, marker="s", color='#009E73', markersize=7)
        elif et == "kick-off":
            ax.plot(x, y, marker="D", color='F0E442', markersize=10)


        if team == "Both":
            ax.text(x + 1, y, ev.get("team", ""),
                    fontsize=8, color='#000000', weight="bold")

    canvas.draw()

    # ----------- Info Box -----------
    info_box.config(state="normal")
    info_box.delete("1.0", tk.END)
    info_box.insert(tk.END, f"=== {event_type.upper()} ({team}) ===\n", "title")
    info_box.insert(tk.END, f"Total Events: {len(filtered)}\n", "subtitle")
    info_box.insert(tk.END, "-" * 60 + "\n", "separator")

    for i, ev in enumerate(filtered, 1):
        line = f"{i}. Team: {ev.get('team')} | Location: {ev.get('location')} | Time: {ev.get('timestamp')}\n"
        info_box.insert(tk.END, line)

    info_box.config(state="disabled")
   

# -------------------------------
# Details view (non-destructive)
# -------------------------------
details_container = None  # frame details

def close_details():
    global details_container
    if details_container is not None:
        details_container.destroy()
        details_container = None
    # show info_box again
    if info_box and not info_box.winfo_manager():
        info_box.pack(pady=10, fill="both", expand=True)

def show_possession_details():
    global selected_pos, details_container
    if not selected_pos:
        info_box.config(state="normal")
        info_box.delete("1.0", tk.END)
        info_box.insert(tk.END, "⚠️ Please select and show a possession first.\n", "highlight")
        info_box.config(state="disabled")
        return

    pos = selected_pos

    # if details already open, destroy then reopen fresh
    if details_container is not None:
        details_container.destroy()
        details_container = None

    # hide info_box to free the right area
    if info_box.winfo_manager():
        info_box.pack_forget()

    # create details container inside info_frame
    details_container = tk.Frame(info_frame, bg="white", bd=1, relief="solid")
    details_container.pack(pady=6, padx=6, fill="both", expand=True)

    # Counts cards
    actions = pos.get("actions", [])
    counts = {
        "Passes": len([a for a in actions if "controlled_pass" in str(a.get("type", "")).lower()]),
        "Receives": len([a for a in actions if "receive" in str(a.get("type", "")).lower()]),
        "Intercepts": len([a for a in actions if "intercept" in str(a.get("type", "")).lower()]),
        "Dribbles": len([a for a in actions if "dribble" in str(a.get("type", "")).lower()])
    }

    # ===== Dribbles =====
    dribbles = [a for a in actions if "dribble" in str(a.get("type", "")).lower()]
    successful_dribbles = []
    effective_dribbles = []
    team_name = pos.get("team", "").lower()

    for d in dribbles:
        s_norm = resolve_loc(d.get("start_location_m"))
        e_norm = resolve_loc(d.get("end_location_m"))
        if not s_norm or not e_norm:
            continue

        sx, sy = s_norm
        ex, ey = e_norm
        dx = ex - sx
        dy = ey - sy

        if abs(dx) >= 2 or abs(dy) >= 2:
            successful_dribbles.append(d)

        if team_name == "usa":  
            is_toward_goal = dy > 5
        else:  
            is_toward_goal = dy < -5

        if (is_toward_goal or d.get("toward_goal", False)):
            effective_dribbles.append(d)

    counts["S_Dribbles"] = len(successful_dribbles)
    counts["E_Dribbles"] = len(effective_dribbles)

    # ===== Passes =====
    passes = [a for a in actions if "controlled_pass" in str(a.get("type", "")).lower()]
    effective_passes = []
    successful_passes = []

    for i, p in enumerate(passes):
        is_succ = False

        next_index = actions.index(p) + 1
        if next_index < len(actions):
            next_act = actions[next_index]
            if "receive" in str(next_act.get("type", "")).lower():
                is_succ = True

        s_norm = resolve_loc(p.get("start_location_m"))
        e_norm = resolve_loc(p.get("end_location_m"))
        if not s_norm or not e_norm:
            continue

        sx, sy = s_norm
        ex, ey = e_norm
        dx = ex - sx
        dy = ey - sy

        if team_name == "usa":  
            is_toward_goal = dy > 5
        else:  
            is_toward_goal = dy < -5

        if is_succ:
            successful_passes.append(p)
        if is_succ and (is_toward_goal or p.get("toward_goal", False)):
            effective_passes.append(p)

    counts["S_Passes"] = len(successful_passes)
    counts["E_Passes"] = len(effective_passes)


    # --- Cards section with horizontal scroll ---
    cards_canvas_frame = tk.Frame(details_container, bg="white")
    cards_canvas_frame.pack(fill="x", pady=5, padx=6)

    cards_canvas = tk.Canvas(cards_canvas_frame, bg="white", height=100, highlightthickness=0)
    h_scroll = tk.Scrollbar(cards_canvas_frame, orient="horizontal", command=cards_canvas.xview)
    cards_canvas.configure(xscrollcommand=h_scroll.set)

    h_scroll.pack(side="bottom", fill="x")
    cards_canvas.pack(side="top", fill="x", expand=True)

    card_frame = tk.Frame(cards_canvas, bg="white")
    cards_canvas.create_window((0,0), window=card_frame, anchor="nw")

    color_map = {
        "Passes": "#1ABC9C",
        "Receives": "#3498DB",
        "Intercepts": "#E67E22",
        "Dribbles": "#9B59B6",
        "E_Dribbles": "#2ECC71",
        "S_Dribbles": "#2980B9",
        "E_Passes": "#FFB6C1",
        "S_Passes": "#FF7F50"
    }

    for k, v in counts.items():
        bg_color = color_map.get(k, "#7F8C8D")
        card = tk.Label(card_frame, text=f"{k}\n{v}", font=("Arial", 18, "bold"),
                        bg=bg_color, fg="white", padx=14, pady=10,
                        relief="raised", bd=3, width=8, height=1)
        card.pack(side="left", padx=4, pady=4)

    card_frame.update_idletasks()
    cards_canvas.config(scrollregion=cards_canvas.bbox("all"))
    


    # --- Table area with vertical & horizontal scroll ---
    table_frame = tk.Frame(details_container, bg="white")
    table_frame.pack(pady=8, padx=8, fill="both", expand=True)

    columns = ("#", "Type", "From", "To", "Player", "Start Loc", "End Loc", "Time")

    style = ttk.Style()
    style.configure("Custom.Treeview", font=("Arial", 15), rowheight=32)
    style.configure("Custom.Treeview.Heading", font=("Arial", 16, "bold"))

    tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=8, style="Custom.Treeview")

    col_widths = {
        "#": 40, "Type": 150, "From": 90, "To": 90,
        "Player": 80, "Start Loc": 150, "End Loc": 150,
        "Time": 120
    }

    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=col_widths.get(col, 100), anchor="center", stretch=True)

    vsb = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

    tree.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")
    hsb.grid(row=1, column=0, sticky="ew")

    table_frame.grid_rowconfigure(0, weight=1)
    table_frame.grid_columnconfigure(0, weight=1)

    def format_loc(loc):
        if isinstance(loc, (list, tuple)) and len(loc) == 2:
            return f"{loc[0]:.2f}, {loc[1]:.2f}"
        return ""

    for i, act in enumerate(actions, start=1):
        action_type = safe_value(act.get("type"), "N/A")
        from_player = safe_value(act.get("from"))
        to_player = safe_value(act.get("to"))
        player = safe_value(act.get("player"), "N/A")

        shots_info = ", ".join(act.get("shots", []))
        if shots_info:
            action_type = f"{action_type} ({shots_info})"

        if act.get("start_location_m") or act.get("end_location_m"):
            start_loc = safe_loc(act.get("start_location_m"))
            end_loc = safe_loc(act.get("end_location_m"))
        else:
            start_loc = safe_loc(act.get("location_m"))
            end_loc = safe_loc(act.get("location_m"))

        if "frame" in act:
            time = frame_to_time(act.get("frame", ""))
        elif "start_frame" in act and "end_frame" in act:
            start_time = frame_to_time(act.get("start_frame"))
            end_time = frame_to_time(act.get("end_frame"))
            time = f"{start_time} → {end_time}"
        else:
            time = ""

        tree.insert("", "end", values=(
            i, action_type, from_player, to_player,
            player, start_loc, end_loc, time
        ))
    

    btn_close = tk.Button(details_container, text="Close Details", bg=SECONDARY, fg="white",
                          font=("Arial", 14, "bold"),
                          command=close_details)
    btn_close.pack(pady=8, anchor="e", padx=8)
stages_popup = None  

def show_stages_popup():
    global selected_pos, stages_popup


    if not selected_pos:
        messagebox.showwarning("No possession", "Please select a possession first.")
        return

 
    if stages_popup and tk.Toplevel.winfo_exists(stages_popup):
        stages_popup.destroy()

    pid = selected_pos.get("possession_id")
    related_stages = get_stages_for_possession(pid)

    stages_popup = tk.Toplevel(root)
    stages_popup.title(f"Stages for Possession {pid}")
    stages_popup.geometry("500x500")
    stages_popup.configure(bg="#FFFFFF")

    tk.Label(stages_popup, text=f"Possession {pid} - Stages",
             font=("Arial", 16, "bold"), bg="#FFFFFF", fg="#1E3A8A").pack(pady=15)

 
    if not related_stages:
        tk.Label(stages_popup, text="No stages found for this possession.",
                 font=("Arial", 12), bg="#FFFFFF", fg="#6B7280").pack(pady=10)
        return

   
    for s in related_stages:
        card = tk.Frame(stages_popup, bg="#F9FAFB", bd=1, relief="solid")
        card.pack(fill="x", padx=20, pady=6)

        tk.Label(card, text=f"🏁 Stage: {s.get('stage', 'N/A')}",
                 font=("Arial", 13, "bold"), bg="#F9FAFB", fg="#111827").pack(anchor="w", padx=10, pady=(5, 0))
        tk.Label(card, text=f"🎯 Team: {s.get('team', 'N/A')}",
                 font=("Arial", 12), bg="#F9FAFB", fg="#374151").pack(anchor="w", padx=10)
        tk.Label(card, text=f"🧩 End Reason: {s.get('end_reason', 'N/A')}",
                 font=("Arial", 12), bg="#F9FAFB", fg="#6B7280").pack(anchor="w", padx=10, pady=(0, 5))

    tk.Button(stages_popup, text="Close", command=stages_popup.destroy,
              font=("Arial", 12), bg="#1E3A8A", fg="white",
              relief="flat", padx=10, pady=5).pack(pady=15)

# -------------------------------
# Show Result (UI flow)
# -------------------------------
def show_result():
    global selected_team, selected_mode, filtered_possessions, possession_combo, selected_pos
    selected_team = team_combo.get()
    selected_mode = mode_combo.get()
    selected_pos = None

    if not selected_team:
        messagebox.showerror("Error", "Please select Team")
        return

    page2.pack_forget()
    page3.pack(fill="both", expand=True)

    # ensure info_box visible (if previously hidden by details)
    if not info_box.winfo_manager():
        info_box.pack(pady=10, fill="both", expand=True)

    draw_pitch(ax)
    info_box.config(state="normal")
    info_box.delete("1.0", tk.END)
    info_box.config(state="disabled")

    # clear controls
    for widget in event_controls_frame.winfo_children():
        widget.destroy()

    if selected_mode == "Event":
        tk.Label(event_controls_frame, text="Select Event:", font=("Arial", 18, "bold"), bg="white", fg=TITLE_COLOR).pack(side="left", padx=5)
        event_types = sorted({ev.get("event", "") for ev in events_data})
        event_combo = ttk.Combobox(event_controls_frame, values=event_types, font=("Arial", 16))
        event_combo.pack(side="left", padx=5)

        tk.Button(event_controls_frame, text="Show Selected Event", bg=PRIMARY, fg="white",
                  command=lambda: draw_selected_events(event_combo.get(), selected_team)).pack(side="left", padx=5)

        tk.Button(event_controls_frame, text="Show Event Counts", bg=SUCCESS, fg="white",
                  command=lambda: show_event_counts(selected_team)).pack(side="left", padx=5)

    elif selected_mode == "Possession":
        filtered_possessions = filter_possessions(selected_team)
        if filtered_possessions:
            tk.Label(event_controls_frame, text="Select Possession:", font=("Arial", 18, "bold"), bg="white", fg=TITLE_COLOR).pack(side="left", padx=5)
            possession_combo = ttk.Combobox(event_controls_frame,
                                           values=[f"Possession {i+1}" for i in range(len(filtered_possessions))],
                                           font=("Arial", 16))
            possession_combo.pack(side="left", padx=5)
            def on_possession_select(event):
                global selected_pos
                idx = possession_combo.current()
                if idx >= 0:
                    selected_pos = filtered_possessions[idx]

            # اربطي الحدث بالـ Combobox
            possession_combo.bind("<<ComboboxSelected>>", on_possession_select)

            tk.Button(event_controls_frame, text="Show", bg=PRIMARY, fg="white", command=show_selected_possession).pack(side="left", padx=5)
            tk.Button(event_controls_frame, text="Details", bg=WARN, fg="white", command=show_possession_details).pack(side="left", padx=5)
            tk.Button(event_controls_frame, text="Missed Passes", bg="#C0392B", fg="white",
                    command=show_intercepted_pass_only).pack(side="left", padx=5)
            tk.Button(event_controls_frame, text="Show Stages", bg="#2563EB", fg="white", command=show_stages_popup).pack(side="left", padx=5)

            tk.Button(event_controls_frame, text="Analysis 📊", bg="#8E44AD", fg="white",
                    command=show_analysis).pack(side="left", padx=5)


    canvas.draw()

# -------------------------------
# Navigation
# -------------------------------
def back_to_page1():
    # when going back to page1 clear info and details
    close_details()
    info_box.config(state="normal"); info_box.delete("1.0", tk.END); info_box.config(state="disabled")
    draw_pitch(ax); canvas.draw()
    page2.pack_forget(); page1.pack(fill="both", expand=True)

def back_to_page2():
    # close details and return
    close_details()
    info_box.config(state="normal"); info_box.delete("1.0", tk.END); info_box.config(state="disabled")
    draw_pitch(ax); canvas.draw()
    page3.pack_forget(); page2.pack(fill="both", expand=True)
def back_to_page3():
    # close details and return
    close_details()
    info_box.config(state="normal"); info_box.delete("1.0", tk.END); info_box.config(state="disabled")
    draw_pitch(ax); canvas.draw()
    page4.pack_forget(); page3.pack(fill="both", expand=True)

# -------------------------------
# Main Window / UI
# -------------------------------
root = tk.Tk()
root.title("⚽ Football Match Visualization ⚽")
root.geometry("1300x750")

style_font = ("Arial", 14, "bold")

# ----- Page 1 -----
page1 = tk.Frame(root, bg=BG_PAGE)
tk.Label(page1, text="Step 1: Select Mode", font=("Arial", 20, "bold"), bg=BG_PAGE, fg=TITLE_COLOR).pack(pady=20)
mode_combo = ttk.Combobox(page1, values=["Possession", "Event"], font=("Arial", 12))
mode_combo.current(0)
mode_combo.pack(pady=5)
tk.Button(page1, text="Next ➡", font=style_font, bg=PRIMARY, fg="white",
          command=lambda: (page1.pack_forget(), page2.pack(fill="both", expand=True))).pack(pady=20)
page1.pack(fill="both", expand=True)

# ----- Page 2 -----
page2 = tk.Frame(root, bg="#E8F6FF")
tk.Label(page2, text="Step 2: Select Team", font=("Arial", 20, "bold"), bg="#E8F6FF", fg=TITLE_COLOR).pack(pady=20)
team_combo = ttk.Combobox(page2, values=["USA", "France", "Both"], font=("Arial", 12))
team_combo.current(2)
team_combo.pack(pady=10)
btn_frame2 = tk.Frame(page2, bg="#E8F6FF")
btn_frame2.pack(pady=20)
tk.Button(btn_frame2, text="⬅ Back", font=style_font, bg=SECONDARY, fg="white", command=back_to_page1).pack(side="left", padx=10)
tk.Button(btn_frame2, text="Show Result ✅", font=style_font, bg=PRIMARY, fg="white", command=show_result).pack(side="left", padx=10)

# -------------- Page 3 -----------------
page3 = tk.Frame(root, bg="white")
tk.Label(page3, text="📊 Match Result", font=("Arial", 20, "bold"), bg="white", fg=TITLE_COLOR).pack(pady=10)

content_frame = tk.Frame(page3, bg="white")
content_frame.pack(fill="both", expand=True)

canvas_frame = tk.Frame(content_frame, bg="white")
canvas_frame.pack(side="left", padx=10, pady=10, fill="both", expand=False)

info_frame = tk.Frame(content_frame, bg="white")
info_frame.pack(side="right", padx=0, pady=10, fill="y")
info_frame.place(relx=0.50, rely=0.05, relheight=0.9)

# Figure & Canvas
fig, ax = plt.subplots(figsize=(11, 13))
draw_pitch(ax)
plt.subplots_adjust(left=0.0005, right=0.55, top=0.90, bottom=0.1)

canvas = FigureCanvasTkAgg(fig, master=canvas_frame)
canvas.get_tk_widget().pack(fill="both", expand=True)

event_controls_frame = tk.Frame(info_frame, bg="white")
event_controls_frame.pack(pady=5, fill="x")

info_box = tk.Text(info_frame, height=25, width=90, font=("Consolas", 12), wrap="word",
                   bg=INFOBOX_BG, fg=INFOBOX_FG, relief="solid", bd=1)
info_box.tag_config("title", font=("Consolas", 14, "bold"), foreground=PRIMARY)
info_box.tag_config("subtitle", font=("Consolas", 12, "bold"), foreground=TITLE_COLOR)
info_box.tag_config("highlight", font=("Consolas", 12, "bold"), foreground="#E74C3C")
info_box.tag_config("separator", foreground="#7F8C8D")
info_box.pack(pady=10, fill="both", expand=True)

# back button under info area (always visible)
back_btn = tk.Button(info_frame, text="⬅ Back", font=("Arial", 11, "bold"), bg=SECONDARY, fg="white",
                     command=back_to_page2)
back_btn.pack(side="bottom", anchor="w", pady=8, padx=8)
# -------------------------------
# Page 4: Analysis Dashboard
# -------------------------------
page4 = tk.Frame(root, bg="white")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

def show_analysis():
    page3.pack_forget()
    page4.pack(fill="both", expand=True)

    for widget in page4.winfo_children():
        widget.destroy()

    tk.Label(page4, text="📊 Match Analysis Dashboard", font=("Arial", 15, "bold"),
             bg="white", fg=TITLE_COLOR).pack(pady=10)

    # Close Button
    tk.Button(page4, text="Close", font=("Arial", 10, "bold"),
              bg=PRIMARY, fg="white", command=back_to_page3).pack(pady=9, padx=5)

    FPS = 25
    team_stats = {}
    all_durations = {}

    try:

        for pos in possessions:
            team = pos.get("team", "Unknown")
            start_frame = pos.get("start_frame") or 0
            end_frame = pos.get("end_frame") if pos.get("end_frame") is not None else start_frame

            try:
                duration = (end_frame - start_frame) / FPS
            except Exception:
                duration = 0

            actions = pos.get("actions", []) or []

            passes = [a for a in actions if "controlled_pass" in str(a.get("type", "")).lower()]
            effective_passes = []
            successful_passes = []
            missed_passes = []

            team_name = pos.get("team", "").lower()
            for i, p in enumerate(passes):
                is_succ = False
                try:
                    next_index = actions.index(p) + 1
                    if next_index < len(actions):
                        next_act = actions[next_index]
                        if "receive" in str(next_act.get("type", "")).lower():
                            is_succ = True
                except ValueError:
                    continue

                s_norm = resolve_loc(p.get("start_location_m"))
                e_norm = resolve_loc(p.get("end_location_m"))
                if not s_norm or not e_norm:
                    continue

                sx, sy = s_norm
                ex, ey = e_norm
                dx = ex - sx
                dy = ey - sy

    
                if team_name == "usa":
                    is_toward_goal = dy > 5
                else:
                    is_toward_goal = dy < -5

                if is_succ:
                    successful_passes.append(p)
                    if is_toward_goal or p.get("toward_goal", False):
                        effective_passes.append(p)
                else:
                    missed_passes.append(p)

    
            end_norm = resolve_loc(pos.get("end_location_m"))
            half = "Top Half" if end_norm and end_norm[1] > 52.5 else "Bottom Half"

            # team_stats
            if team not in team_stats:
                team_stats[team] = {
                    "time": 0, "poss": 0,
                    "top": 0, "bottom": 0, "durations": [],
                    "effective_passes": 0, "successful_passes": 0, "miss_passes": 0
                }

            team_stats[team]["time"] += duration
            team_stats[team]["poss"] += 1
            team_stats[team]["effective_passes"] += len(effective_passes)
            team_stats[team]["successful_passes"] += len(successful_passes)
            team_stats[team]["miss_passes"] += len(missed_passes)
            team_stats[team]["durations"].append(duration)

            if half == "Top Half":
                team_stats[team]["top"] += 1
            else:
                team_stats[team]["bottom"] += 1

            all_durations.setdefault(team, []).append(duration)

        # ======dribbles_by_team ======
        dribbles_by_team = {}
        for pos in possessions:
            tm = pos.get("team", "Unknown")
            for a in (pos.get("actions", []) or []):
                if "dribble" in str(a.get("type", "")).lower():
                    dribbles_by_team.setdefault(tm, []).append(a)

        for team, drs in dribbles_by_team.items():
            successful_dribbles = []
            effective_dribbles = []

            for d in drs:
                s_norm = resolve_loc(d.get("start_location_m"))
                e_norm = resolve_loc(d.get("end_location_m"))
                if not s_norm or not e_norm:
                    continue

                sx, sy = s_norm
                ex, ey = e_norm
                dx = ex - sx
                dy = ey - sy


                if abs(dx) >= 2 or abs(dy) >= 2:
                    successful_dribbles.append(d)


                if team.lower() == "usa":
                    is_toward_goal = dy > 5
                else:
                    is_toward_goal = dy < -5

                if  (is_toward_goal or d.get("toward_goal", False)):
                    effective_dribbles.append(d)

            if team not in team_stats:
                team_stats[team] = {
                    "time": 0, "poss": 0,
                    "top": 0, "bottom": 0, "durations": [],
                    "effective_passes": 0, "successful_passes": 0, "miss_passes": 0
                }

            team_stats[team]["dribbles_total"] = len(drs)
            team_stats[team]["dribbles_successful"] = len(successful_dribbles)
            team_stats[team]["dribbles_effective"] = len(effective_dribbles)

        # ====== الملخّص ======
        total_possessions = sum(stats["poss"] for stats in team_stats.values())
        total_time = sum(stats["time"] for stats in team_stats.values())
        total_succ = sum(stats["successful_passes"] for stats in team_stats.values())
        total_miss = sum(stats["miss_passes"] for stats in team_stats.values())
        total_effective = sum(stats["effective_passes"] for stats in team_stats.values())
        avg_time = total_time / total_possessions if total_possessions else 0

        data = {
            "summary": {
                "total_possessions": total_possessions,
                "total_time": total_time,
                "avg_time": avg_time,
                "total_succ": total_succ,
                "total_miss": total_miss,
                "total_effective": total_effective
            },
            "teams": team_stats
        }

        with open("analysis_output.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        # ====== KPIs ======
        kpi_frame = tk.Frame(page4, bg="white")
        kpi_frame.pack(fill="x", pady=8, padx=20)

        for text, value, color in [
            ("Total Possessions", total_possessions, "#2980B9"),
            ("Avg Possession Time (s)", f"{avg_time:.1f}", "#16A085"),
            ("Successful Passes", total_succ, "#27AE60"),
            ("Missed Passes", total_miss, "#C0392B"),
            ("Effective Passes", total_effective, "#000000")
        ]:
            card = tk.Frame(kpi_frame, bg=color)
            card.pack(side="left", expand=True, fill="x", padx=5)
            tk.Label(card, text=text, font=("Arial", 12, "bold"),
                     bg=color, fg="white").pack(pady=5)
            tk.Label(card, text=value, font=("Arial", 16, "bold"),
                     bg=color, fg="white").pack(pady=5)

        # ====== Main Layout: Left (Cards+Charts) / Right (Table) ======
        main_frame = tk.Frame(page4, bg="white")
        main_frame.pack(fill="both", expand=True, padx=15, pady=10)

        # --- Left Section ---
        left_section = tk.Frame(main_frame, bg="white")
        left_section.pack(side="left", fill="both", expand=True, padx=10)

        # --- Team Cards ---
        for team, stats in team_stats.items():
            avg_time_team = stats["time"] / stats["poss"] if stats["poss"] else 0
            avg_pos = (stats["poss"] / total_possessions) * 100 if total_possessions else 0
            longest = max(stats["durations"]) if stats["durations"] else 0
            shortest = min(stats["durations"]) if stats["durations"] else 0
            avg_passes = (stats["successful_passes"] / stats["poss"]) if stats["poss"] else 0

            card = tk.Frame(left_section, bg="#ECF0F1", bd=2, relief="groove")
            card.pack(fill="x", pady=6)
        
            tk.Label(card, text=f"{team}", font=("Arial", 18, "bold"),
                     bg="#ECF0F1", fg=PRIMARY).pack(anchor="w", padx=10, pady=5)
            tk.Label(card, text=f"Total Possessions: {stats['poss']}", font=("Arial", 12),
                     bg="#ECF0F1", fg=TEXT_COLOR).pack(anchor="w", padx=15)
            tk.Label(card, text=f"Total Time: {stats['time']:.1f}s", font=("Arial", 12),
                     bg="#ECF0F1", fg=TEXT_COLOR).pack(anchor="w", padx=15)
            tk.Label(card, text=f"Avg Time: {avg_time_team:.1f}s", font=("Arial", 12),
                     bg="#ECF0F1", fg=TEXT_COLOR).pack(anchor="w", padx=15)
            tk.Label(card, text=f"Longest Possession: {longest:.1f}s", font=("Arial", 12),
                     bg="#ECF0F1", fg="#16A085").pack(anchor="w", padx=15)
            tk.Label(card, text=f"Shortest Possession: {shortest:.1f}s", font=("Arial", 12),
                     bg="#ECF0F1", fg="#C0392B").pack(anchor="w", padx=15)
            tk.Label(card, text=f"Avg Passes per Possession: {avg_passes:.1f}", font=("Arial", 12),
                     bg="#ECF0F1", fg="#34495E").pack(anchor="w", padx=15)
            tk.Label(card, text=f"Top Half: {stats['top']} | Bottom Half: {stats['bottom']}", font=("Arial", 12),
                     bg="#ECF0F1", fg="#2C3E50").pack(anchor="w", padx=15, pady=5)
            tk.Label(card, text=f"Possession Share: {avg_pos:.1f}%", font=("Arial", 12),
                     bg="#ECF0F1", fg="#2980B9").pack(anchor="w", padx=15, pady=5)
        # ====== Controlled Passes Cards Section ======
        passes_frame = tk.Frame(main_frame, bg="white")
        passes_frame.pack(side="right", fill="y", padx=15)

        for team, stats in team_stats.items():
            card = tk.Frame(passes_frame, bg="#E8F8F5", bd=2, relief="groove")
            card.pack(fill="x", pady=8)

            tk.Label(card, text=f"🎯 {team} Controlled Passes", font=("Arial", 16, "bold"),
                 bg="#E8F8F5", fg="#117864").pack(anchor="w", padx=10, pady=5)

            tk.Label(card, text=f"Total Successful Passes: {stats['successful_passes']}", font=("Arial", 12),
                 bg="#E8F8F5", fg="#0E6655").pack(anchor="w", padx=15)
            tk.Label(card, text=f"Effective Passes (in opponent half): {stats.get('effective_passes', 0)}", font=("Arial", 12),
                 bg="#E8F8F5", fg="#0E6655").pack(anchor="w", padx=15)
            tk.Label(card, text=f"miss_passes: {stats['miss_passes']}", font=("Arial", 12),
                    bg="#E8F8F5", fg="#0E6655").pack(anchor="w", padx=15)
        # ====== Dribbling Cards Section ======
        dribbling_frame = tk.Frame(main_frame, bg="white")
        dribbling_frame.pack(side="right", fill="y", padx=15)

        for team, stats in team_stats.items():
            card = tk.Frame(dribbling_frame, bg="#F3E5F5", bd=2, relief="groove")
            card.pack(fill="x", pady=8)

            tk.Label(card, text=f"⚡ {team} Dribbling Stats", font=("Arial", 16, "bold"),
                     bg="#F3E5F5", fg="#6C3483").pack(anchor="w", padx=10, pady=5)

            tk.Label(card, text=f"Total Dribbles: {stats.get('dribbles_total', 0)}", font=("Arial", 12),
                     bg="#F3E5F5", fg="#4A235A").pack(anchor="w", padx=15)
            tk.Label(card, text=f"Successful Dribbles (>2m): {stats.get('dribbles_successful', 0)}", font=("Arial", 12),
                     bg="#F3E5F5", fg="#8E44AD").pack(anchor="w", padx=15)
            tk.Label(card, text=f"Effective Dribbles (forward/goal): {stats.get('dribbles_effective', 0)}", font=("Arial", 12),
                     bg="#F3E5F5", fg="#9B59B6").pack(anchor="w", padx=15)

        # --- Charts ---
        charts_frame = tk.Frame(left_section, bg="white")
        charts_frame.pack(fill="both", expand=True, pady=10,padx=70)

        # Pie Chart
        fig1, ax1 = plt.subplots(figsize=(3.5, 3.5))
        labels = list(team_stats.keys())
        sizes = [stats["poss"] for stats in team_stats.values()]
        if sizes and sum(sizes) > 0:
            ax1.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)
        ax1.set_title("Possession Share")
        canvas1 = FigureCanvasTkAgg(fig1, master=charts_frame)
        canvas1.get_tk_widget().pack(side="left", padx=15)

        # Bar Chart
        fig2, ax2 = plt.subplots(figsize=(3.5, 3.5))
        teams = list(team_stats.keys())
        succ_vals = [team_stats[t]["successful_passes"] for t in teams]
        miss_vals = [team_stats[t]["miss_passes"] for t in teams]
        ax2.bar(teams, succ_vals, label="Successful")
        ax2.bar(teams, miss_vals, bottom=succ_vals, label="Missed")
        ax2.set_title("Passes (Succ vs Missed)")
        ax2.legend()
        canvas2 = FigureCanvasTkAgg(fig2, master=charts_frame)
        canvas2.get_tk_widget().pack(side="left", padx=15)

    except Exception as e:
  
        messagebox.showerror("Analysis Error", f"Analysis Error:\n{e}")
        back_to_page2()
        return


root.mainloop()
