from flask import Flask, render_template, Response
import cv2
import time

# vision modules
from vision.detector import PersonDetector
from vision.tracker import SimpleTracker
from vision.rules import detect_anomalies
import config

app = Flask(__name__)

VIDEO_PATH = "static/videos/test.mp4"

# initialize detector and tracker
# 使用本地 YOLO11 权重（严格使用 YOLO11 作为唯一检测器）
MODEL_PATH = 'models/yolo11n.pt'
# 使用配置文件中的参数
detector = PersonDetector(model_path=MODEL_PATH, conf_thres=config.CONF_THRES)
tracker = SimpleTracker(max_distance=config.MAX_DISTANCE,
                        max_lost_time=config.MAX_LOST_TIME,
                        max_missed=config.MAX_MISSED,
                        confirm_threshold=config.CONFIRM_THRESHOLD)

# 最小面积过滤（兜底）
MIN_AREA = config.MIN_AREA

def generate_frames():
    cap = cv2.VideoCapture(VIDEO_PATH)
    print("Video opened:", cap.isOpened())

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.resize(frame, (640, 480))

        # detect people
        try:
            boxes = detector.detect(frame)
        except Exception:
            boxes = []

        # 最小面积过滤（去除小噪声框）
        if boxes:
            boxes = [b for b in boxes if (b[2] * b[3]) >= MIN_AREA]

        # draw detection boxes
        if boxes:
            detector.draw_boxes(frame, boxes)

        # update tracker and display IDs and durations
        try:
            objects = tracker.update(boxes)
            # check rules for anomalies
            anomalies = detect_anomalies(objects, loiter_time=10.0)
            for obj_id, obj in objects.items():
                # 只显示已确认的 track，避免瞬时误检生成持久框
                if not obj.get('confirmed', True):
                    continue
                cx, cy = obj['center']
                duration = time.time() - obj['start_time']
                label = f"ID {obj_id} {duration:.1f}s"
                cv2.putText(frame,
                            label,
                            (int(cx) - 20, int(cy) - 10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.5,
                            (0, 0, 255),
                            2)
                # draw bounding box if available
                box = obj.get('box')
                if box is not None:
                    x, y, w, h = box
                    color = (0, 255, 0)
                    thickness = 2
                    # highlight anomalies in red
                    if obj_id in anomalies:
                        color = (0, 0, 255)
                        cv2.putText(frame, anomalies[obj_id], (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                        thickness = 3
                    cv2.rectangle(frame, (x, y), (x + w, y + h), color, thickness)
        except Exception:
            pass

        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    cap.release()

@app.route('/')
def index():
    return render_template('index.html', config=config)

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(debug=True)
