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

with open("possessions_new_version.json", "r") as f:
    possessions = json.load(f)

# -----------------------------
# Helpers & Pitch Drawing
# -----------------------------
def draw_pitch(ax, length=105, width=68):
    ax.clear()
    ax.set_xlim(0, width)
    ax.set_ylim(0, length)
    ax.set_aspect('equal')
    ax.set_facecolor("green")

    ax.plot([0, width], [0, 0], color="white")
    ax.plot([0, width], [length, length], color="white")
    ax.plot([0, 0], [0, length], color="white")
    ax.plot([width, width], [0, length], color="white")
    ax.plot([0, width], [length/2, length/2], color="white", linestyle="--")

   
    ax.add_patch(patches.Rectangle(((width/2)-20.15, 0), 40.3, 16.5,
                                   fill=False, edgecolor="blue", lw=2))
    ax.add_patch(patches.Rectangle(((width/2)-20.15, length-16.5), 40.3, 16.5,
                                   fill=False, edgecolor="blue", lw=2))

def scale_coords(x, y, max_x=80, max_y=120):
    return x * (68/max_x), y * (105/max_y)

def normalize_coords(x, y, width=68, length=105):
    try:
        x = float(x)
        y = float(y)
    except Exception:
        return None
    if x > width or y > length:
        return scale_coords(x, y)
    return x, y

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
    ]
    ax.legend(handles=elems, loc="center left", bbox_to_anchor=(1.02, 0.5),
              frameon=True, fontsize=10, title="Possession Legend", title_fontsize=11)

# -------------------------------
# Plot Possession
# -------------------------------
def plot_possession(ax, pos):
    actions = pos.get("actions", []) or []
    valid = []
    for act in actions:
        loc = act.get("location_m") or act.get("start_location_m") or act.get("end_location_m")
        if isinstance(loc, (list, tuple)) and len(loc) >= 2:
            norm = normalize_coords(loc[0], loc[1])
            if norm is not None:
                valid.append((act, norm))

    if not valid:
        return

    prev = None
    team_color = "blue" if pos.get("team") == "USA" else "red"
    seen_labels = []

    for idx, (act, (x, y)) in enumerate(valid):
        if idx == 0:
            ax.plot(x, y, "o", color="#000000", markersize=7, zorder=5)
            ax.text(x + 0.6, y + 0.6, "START", fontsize=7, color="white", weight="bold", zorder=6)
        elif idx == len(valid) - 1:
            ax.plot(x, y, "o", color="#FFFF00", markersize=7, zorder=5)
            ax.text(x + 0.6, y + 0.6, "END", fontsize=7, color="white", weight="bold", zorder=6)
        else:
            typ = str(act.get("type", "")).lower()
            player_num = act.get("player_number") or act.get("player") or idx

            if typ == "receive":
                ax.plot(x, y, "^", color='blue', markersize=7.5, zorder=5)
                duplicate = any(p == player_num and abs(px - x) < 1 and abs(py - y) < 1 for p, px, py in seen_labels)
                if not duplicate:
                    ax.text(x + 0.4, y + 0.4, str(player_num), fontsize=7, color="white", weight="bold", zorder=6)
                    seen_labels.append((player_num, x, y))
            elif "controlled_pass" in typ:
                if prev is not None:
                    dx = x - prev[0]
                    dy = y - prev[1]
                    ax.arrow(prev[0], prev[1], dx, dy,
                             head_width=1.0, head_length=1.5, length_includes_head=True,
                             fc='#00FFFF', ec='#00FFFF', alpha=0.9, linewidth=1.5, zorder=3)
            elif "intercept" in typ or "pass_intercepted" in typ:
                ax.plot(x, y, "x", color="orange", markersize=8, zorder=5)
            elif "dribble" in typ:
                ax.plot(x, y, marker='.', color='purple', markersize=8, zorder=5)
            else:
                ax.plot(x, y, "o", color='#00FFFF', markersize=5, zorder=5)
        prev = (x, y)

    start_team = pos.get("team", "Unknown")
    end_team = pos.get("end_team" "Unknown")
    outcome = pos.get("outcome", "N/A")
    start_x, start_y = -5, 106
    text = f"Start Team: {start_team}   |   End Team: {end_team}   |   Outcome: {outcome}"
    ax.text(start_x + 3, start_y + 3, text, ha="left", va="center",
            fontsize=12, color="white", weight="bold",
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
            fontsize=14, weight="bold",
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
            norm = normalize_coords(loc[0], loc[1])
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
details_container = None  # frame for details

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
        card = tk.Label(card_frame, text=f"{k}: {v}", font=("Arial", 12, "bold"),
                        bg=SUCCESS, fg="white", padx=10, pady=6, relief="raised", bd=2)
        card.pack(side="left", padx=6, pady=2)

    # Table area with its own vertical scrollbar
    table_frame = tk.Frame(details_container, bg="white")
    table_frame.pack(pady=6, padx=6, fill="both", expand=False)

    columns = ("#", "Type", "From", "To", "Player", "Location")
    tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=10)

    col_widths = {"#": 60, "Type": 160, "From": 120, "To": 120, "Player": 140, "Location": 220}
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=col_widths.get(col, 100), anchor="center", stretch=True)

    vsb = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)

    tree.pack(side="left", fill="both", expand=True)
    vsb.pack(side="right", fill="y")

    for i, act in enumerate(actions, start=1):
        action_type = act.get("type", "")
        from_player = act.get("from", "")
        to_player = act.get("to", "")
        player = act.get("player", "")
        location = act.get("location_m") or act.get("end_location_m") or ""
        tree.insert("", "end", values=(i, action_type, from_player, to_player, player, location))

    # close button (returns to info_box)
    btn_close = tk.Button(details_container, text="Close Details", bg=SECONDARY, fg="white",
                          command=close_details)
    btn_close.pack(pady=6, anchor="e", padx=6)

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
        tk.Label(event_controls_frame, text="Select Event:", font=("Arial", 11, "bold"), bg="white", fg=TITLE_COLOR).pack(side="left", padx=5)
        event_types = sorted({ev.get("event", "") for ev in events_data})
        event_combo = ttk.Combobox(event_controls_frame, values=event_types, font=("Arial", 11))
        event_combo.pack(side="left", padx=5)

        tk.Button(event_controls_frame, text="Show Selected Event", bg=PRIMARY, fg="white",
                  command=lambda: draw_selected_events(event_combo.get(), selected_team)).pack(side="left", padx=5)

        tk.Button(event_controls_frame, text="Show Event Counts", bg=SUCCESS, fg="white",
                  command=lambda: show_event_counts(selected_team)).pack(side="left", padx=5)

    elif selected_mode == "Possession":
        filtered_possessions = filter_possessions(selected_team)
        if filtered_possessions:
            tk.Label(event_controls_frame, text="Select Possession:", font=("Arial", 11, "bold"), bg="white", fg=TITLE_COLOR).pack(side="left", padx=5)
            possession_combo = ttk.Combobox(event_controls_frame,
                                           values=[f"Possession {i+1}" for i in range(len(filtered_possessions))],
                                           font=("Arial", 11))
            possession_combo.pack(side="left", padx=5)
            tk.Button(event_controls_frame, text="Show", bg=PRIMARY, fg="white", command=show_selected_possession).pack(side="left", padx=5)
            tk.Button(event_controls_frame, text="Details", bg=WARN, fg="white", command=show_possession_details).pack(side="left", padx=5)

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
fig, ax = plt.subplots(figsize=(8, 10))
draw_pitch(ax)
plt.subplots_adjust(left=0.05, right=0.78, top=0.95, bottom=0.1)

canvas = FigureCanvasTkAgg(fig, master=canvas_frame)
canvas.get_tk_widget().pack(fill="both", expand=True)

event_controls_frame = tk.Frame(info_frame, bg="white")
event_controls_frame.pack(pady=5, fill="x")

info_box = tk.Text(info_frame, height=25, width=60, font=("Consolas", 12), wrap="word",
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
