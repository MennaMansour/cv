import cv2
from ultralytics import YOLO
from collections import defaultdict

# -------------------------------
# indicate name of group based on each class
# -------------------------------
def get_group_key(class_name):
    name = class_name.lower()
    if "usa_gk" in name:
        return "USA_GK"
    elif "france_gk" in name:
        return "france_GK"
    elif "usa" in name and "player" in name:
        return "USA_players"
    elif "france" in name and "player" in name:
        return "france_players"
    elif "ref" in name:
        return "refs"
    elif "ball" in name:
        return "ball"
    return None

# -------------------------------
# draw box and id 
# -------------------------------
def draw_box(frame, x1, y1, x2, y2, assigned_id, class_name, color):
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
    text = f"ID {assigned_id} | {class_name}"
    (text_w, text_h), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1)
    cv2.rectangle(frame, (x1, y1 - 10), (x1 + text_w, y1), color, -1)
    cv2.putText(frame, text, (x1, y1 - 2),
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1)

# -------------------------------
# process each frame 
# -------------------------------
def process_frame(frame, model, tracker_type, id_map, available_ids, colors, lost_ids, delay_frames, frame_count):
    results = model.track(frame, tracker=tracker_type, persist=True)

    current_keys = set()

    if results[0].boxes.id is not None:
        track_ids = results[0].boxes.id.cpu().numpy().astype(int)
        boxes = results[0].boxes.xyxy.cpu().numpy()
        classes = results[0].boxes.cls.cpu().numpy().astype(int)

        for box, track_id, cls in zip(boxes, track_ids, classes):
            x1, y1, x2, y2 = map(int, box)
            class_name = model.names[int(cls)]
            group_key = get_group_key(class_name)
            key = (class_name, track_id)

            if group_key:
                current_keys.add(key)

                
                if key not in id_map:
              
                    if key in lost_ids and frame_count - lost_ids[key][1] <= delay_frames: 
                        assigned_id, g_key = lost_ids[key][0]
                        id_map[key] = (assigned_id, g_key)
                        del lost_ids[key]
                    elif available_ids[group_key]:
                        assigned_id = available_ids[group_key].pop(0)
                        id_map[key] = (assigned_id, group_key)
                    else:
                        continue 

                assigned_id, g_key = id_map[key]
                color = colors.get(g_key, (255, 255, 255))
                draw_box(frame, x1, y1, x2, y2, assigned_id, class_name, color)


    to_remove = []
    for key, (assigned_id, g_key) in id_map.items():
        if key not in current_keys:
         
            lost_ids[key] = ((assigned_id, g_key), frame_count)
            to_remove.append(key)

    for key in to_remove:
        del id_map[key]

  
    to_free = []
    for key, ((assigned_id, g_key), last_frame) in lost_ids.items():
        if frame_count - last_frame > delay_frames:
            available_ids[g_key].append(assigned_id)
            available_ids[g_key] = sorted(available_ids[g_key])
            to_free.append(key)

    for key in to_free:
        del lost_ids[key]

    return frame


# -------------------------------
# Main Function
# -------------------------------
def main():
    model_path = "OD_YOLO11_V2.pt"
    video_path = "france_usa_final.mp4"
    tracker_type = "botsort_custom.yaml"

    model = YOLO(model_path)
    cap = cv2.VideoCapture(video_path)

    id_map = {}
    lost_ids = {}  
    frame_count = 0
    delay_frames = 10  
    available_ids = {
        "france_players": list(range(1, 11)),
        "USA_players": list(range(11, 21)),
        "refs": [21, 22, 23],
        "USA_GK": [24],
        "france_GK": [25],
        "ball": [26]
    }

    colors = {
        "USA_players": (0, 165, 255),  
        "france_players": (255, 0, 255), 
        "refs": (0, 255, 0), 
        "ball": (255, 0, 0),  
        "USA_GK": (0, 255, 255),  
        "france_GK": (0, 0, 255) 
    }

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1
        frame = process_frame(frame, model, tracker_type, id_map, available_ids, colors, lost_ids, delay_frames, frame_count)
        frame = cv2.resize(frame, (1000, 800))
        cv2.imshow(f"YOLOv8 + {tracker_type.split('.')[0].upper()}", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
