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

with open("possessions_2_10.json", "r") as f:
    possessions = json.load(f)
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
        mlines.Line2D([], [], marker='.', color='purple', linestyle='None', markersize=9, label="Dribble"),
        mlines.Line2D([], [], color='red', lw=2, label="Pass leading to Throw-in"),
        mlines.Line2D([], [], color='red', marker=r'',markersize=0, label='Pass before Interception')
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
            f"Start Team: {start_team} | End Team: {end_team} | "
            f"End Reason: {end_reason}\n"
            f"Time: {start_time} → {end_time}"
        )

        ax.text(0.005, 112, text,
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
            ax.plot(x, y, marker='.', color='purple', markersize=8, zorder=5)

        else:
            ax.plot(x, y, "o", color='#00FFFF', markersize=5, zorder=5)

    # 🎯 END marker
    if end_norm:
        x, y = end_norm
        ax.plot(x, y, "o", color="#FFFF00", markersize=7, zorder=5)
        # move the word END slightly left of the circle to keep it clear
        ax.text(x - 1.0, y, "END", fontsize=7, color="white", weight="bold", ha="right", zorder=6)

    start_team = pos.get("team", "Unknown")
    end_team = pos.get("end_team", "Unknown")
    end_reason = pos.get("end_reason", "N/A")
    start_frame = pos.get("start_frame", "N/A")
    end_frame = pos.get("end_frame", "N/A")
    start_time = frame_to_time(start_frame)
    end_time = frame_to_time(end_frame)

    text = (
        f"Start Team: {start_team} | End Team: {end_team} | "
        f"End Reason: {end_reason}\n"
        f"Time: {start_time} → {end_time}"
    )

    ax.text(0.005, 112, text,
            ha="left", va="center", fontsize=18, color="white", weight="bold",
            bbox=dict(facecolor="black", alpha=0.6, boxstyle="round,pad=0.3"))


    draw_possession_legend(ax)


# -------------------------------
# Filter Possessions
# -------------------------------
def filter_possessions(team):
    return [pos for pos in possessions if team == "Both" or pos.get("team") == team]

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
    details_container.pack(pady=6, padx=6, fill="both", expand=False)

    # Counts cards
    actions = pos.get("actions", [])
    counts = {
        "Passes": len([a for a in actions if a.get("type") == "controlled_pass"]),
        "Receives": len([a for a in actions if a.get("type") == "receive"]),
        "Intercepts": len([a for a in actions if "intercept" in str(a.get("type", "")).lower()]),
        "Dribbles": len([a for a in actions if "dribble" in str(a.get("type", "")).lower()])
    }

    card_frame = tk.Frame(details_container, bg="white")
    card_frame.pack(pady=5, fill="x", anchor="w", padx=6)

    for k, v in counts.items():
        card = tk.Label(card_frame, text=f"{k}: {v}", font=("Arial", 20, "bold"),
                        bg=SUCCESS, fg="white", padx=10, pady=10, relief="raised", bd=2)
        card.pack(side="left", padx=6, pady=2)

    # Table area with its own vertical scrollbar
    table_frame = tk.Frame(details_container, bg="white")
    table_frame.pack(pady=8, padx=8, fill="both", expand=True)

    columns = ("#", "Type", "From", "To", "Player", "Start Loc", "End Loc", "Time")

    # 🎨 Increase font and rows
    style = ttk.Style()
    style.configure("Custom.Treeview", font=("Arial", 15), rowheight=32)
    style.configure("Custom.Treeview.Heading", font=("Arial", 16, "bold"))

    tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=8, style="Custom.Treeview")

    col_widths = {
        "#": 50, "Type": 200, "From": 100, "To": 100,
        "Player": 100, "Start Loc": 180, "End Loc": 180,
        "Time": 150
    }

    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=col_widths.get(col, 100), anchor="center", stretch=True)

    vsb = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)

    tree.pack(side="left", fill="both", expand=True)
    vsb.pack(side="right", fill="y")

    def format_loc(loc):
        if isinstance(loc, (list, tuple)) and len(loc) == 2:
            return f"{loc[0]:.2f}, {loc[1]:.2f}"
        return ""

    for i, act in enumerate(actions, start=1):
        action_type = safe_value(act.get("type"), "N/A")
        from_player = safe_value(act.get("from"))
        to_player = safe_value(act.get("to"))
        player = safe_value(act.get("player"), "N/A")

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
            tk.Button(event_controls_frame, text="Show", bg=PRIMARY, fg="white", command=show_selected_possession).pack(side="left", padx=5)
            tk.Button(event_controls_frame, text="Details", bg=WARN, fg="white", command=show_possession_details).pack(side="left", padx=5)
            tk.Button(event_controls_frame, text="Missed Passes", bg="#C0392B", fg="white",
                    command=show_intercepted_pass_only).pack(side="left", padx=5)

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
info_frame.pack(side="right", padx=10, pady=10, fill="y")

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

root.mainloop()
