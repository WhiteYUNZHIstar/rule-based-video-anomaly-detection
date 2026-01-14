# Flask Web 框架相关
from flask import Flask, render_template, Response, request, redirect

# OpenCV 用于视频读取、绘制与编码
import cv2

# time 用于计算目标停留时长
import time

# =========================
# 视觉模块（自定义）
# =========================
# 人体检测器（YOLO11n 封装）
from vision.detector import PersonDetector

# 简单多目标跟踪器（基于中心点匹配）
from vision.tracker import SimpleTracker

# 规则模块（异常行为检测）
from vision.rules import detect_anomalies

# 配置文件（集中管理所有阈值）
import config

# =========================
# Flask 应用初始化
# =========================
app = Flask(__name__)

# 视频路径（本地测试视频）
VIDEO_PATH = "static/videos/test.mp4"

# =========================
# 初始化检测器与跟踪器
# =========================

# 使用本地 YOLO11n 权重（严格作为唯一检测器）
MODEL_PATH = 'models/yolo11n.pt'

# 初始化人体检测器
# conf_thres 从 config 中读取，便于统一调参
detector = PersonDetector(
    model_path=MODEL_PATH,
    conf_thres=config.CONF_THRES
)

# 初始化简单跟踪器
# 所有参数均来自 config，保证工程可复现
tracker = SimpleTracker(
    max_distance=config.MAX_DISTANCE,
    max_lost_time=config.MAX_LOST_TIME,
    max_missed=config.MAX_MISSED,
    confirm_threshold=config.CONFIRM_THRESHOLD
)

# =========================
# 视频帧生成器（核心处理逻辑）
# =========================
def generate_frames():
    """
    从视频中逐帧读取画面，执行：
    1. 人体检测
    2. 最小面积过滤
    3. 多目标跟踪
    4. 规则驱动异常检测
    5. 可视化绘制
    并以 MJPEG 流形式返回给前端
    """

    cap = cv2.VideoCapture(VIDEO_PATH)
    print("Video opened:", cap.isOpened())

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # 统一分辨率，保证参数（像素阈值）稳定
        frame = cv2.resize(frame, (640, 480))

        # =========================
        # 人体检测
        # =========================
        try:
            boxes = detector.detect(frame)
        except Exception:
            # 检测异常时兜底为空
            boxes = []

        # =========================
        # 最小面积过滤（检测兜底）
        # 使用 config.MIN_AREA，支持运行时热更新
        # =========================
        if boxes:
            boxes = [
                b for b in boxes
                if (b[2] * b[3]) >= config.MIN_AREA
            ]

        # 绘制检测框（仅用于可视化）
        if boxes:
            detector.draw_boxes(frame, boxes)

        # =========================
        # 跟踪与规则检测
        # =========================
        try:
            # 更新跟踪器，返回当前所有 track
            objects = tracker.update(boxes)

            # 基于规则检测异常（如滞留）
            anomalies = detect_anomalies(objects, loiter_time=10.0)

            # =========================
            # 显示层去重（同帧空间过滤）
            # 仅影响显示，不影响 tracker 内部状态
            # =========================
            shown_centers = []

            for obj_id, obj in objects.items():

                # 仅显示已确认的 track，避免瞬时误检
                if not obj.get('confirmed', True):
                    continue

                cx, cy = obj['center']

                # 若与已显示目标过近，则跳过（防止同帧多 ID）
                if any(
                    abs(cx - x) < config.SPATIAL_THRESHOLD and
                    abs(cy - y) < config.SPATIAL_THRESHOLD
                    for x, y in shown_centers
                ):
                    continue

                shown_centers.append((cx, cy))

                # 计算目标停留时间
                duration = time.time() - obj['start_time']
                label = f"ID {obj_id} {duration:.1f}s"

                # 绘制 ID 与时间标签
                cv2.putText(
                    frame,
                    label,
                    (int(cx) - 20, int(cy) - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 0, 255),
                    2
                )

                # 绘制目标框
                box = obj.get('box')
                if box is not None:
                    x, y, w, h = box
                    color = (0, 255, 0)
                    thickness = 2

                    # 若触发异常规则，用红色高亮
                    if obj_id in anomalies:
                        color = (0, 0, 255)
                        cv2.putText(
                            frame,
                            anomalies[obj_id],
                            (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.5,
                            color,
                            2
                        )
                        thickness = 3

                    cv2.rectangle(
                        frame,
                        (x, y),
                        (x + w, y + h),
                        color,
                        thickness
                    )
        except Exception:
            # 跟踪或规则异常时兜底
            pass

        # =========================
        # 编码为 JPEG 并输出给前端
        # =========================
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        yield (
            b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n' +
            frame +
            b'\r\n'
        )

    cap.release()

# =========================
# Flask 路由
# =========================

@app.route('/')
def index():
    """
    主页面，传入 config 以显示当前参数值
    """
    return render_template('index.html', config=config)


@app.route('/set_params', methods=['POST'])
def set_params():
    """
    前端参数调节接口：
    - SPATIAL_THRESHOLD（显示层去重）
    - MIN_AREA（检测兜底）
    参数修改后即时生效，无需重启
    """
    try:
        # 显示层空间去重阈值
        val = int(request.form.get(
            'spatial_threshold',
            config.SPATIAL_THRESHOLD
        ))
        val = max(20, min(100, val))
        config.SPATIAL_THRESHOLD = val

        # 最小检测面积
        min_a = int(request.form.get(
            'min_area',
            config.MIN_AREA
        ))
        min_a = max(100, min(5000, min_a))
        config.MIN_AREA = min_a

        print(
            f"[INFO] Params updated: "
            f"SPATIAL_THRESHOLD={config.SPATIAL_THRESHOLD}, "
            f"MIN_AREA={config.MIN_AREA}"
        )
    except Exception as e:
        print("[WARN] Failed to update parameters:", e)

    return redirect('/')


@app.route('/video_feed')
def video_feed():
    """
    视频流接口（MJPEG）
    """
    return Response(
        generate_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

# =========================
# 程序入口
# =========================
if __name__ == '__main__':
    # debug=True 仅用于开发与教学演示
    app.run(debug=True)
