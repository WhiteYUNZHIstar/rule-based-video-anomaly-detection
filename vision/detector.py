import cv2
import numpy as np
from ultralytics import YOLO


class PersonDetector:
	"""YOLO11 人体检测器（本模块唯一检测实现）

	职责：加载 YOLO11 权重并返回检测框列表 (x,y,w,h)。
	"""

	def __init__(self, model_path='models/yolo11n.pt', conf_thres=0.35, device=None):
		# 直接加载模型（无任何回退逻辑）
		self.model = YOLO(model_path)
		self.conf_thres = float(conf_thres)

	def detect(self, frame):
		"""在单帧图像上运行检测。

		Args:
			frame: BGR numpy 数组

		Returns:
			boxes: list of (x,y,w,h)（整数）
		"""
		if frame is None:
			return []

		# Ultralytics 接受 RGB 图像或文件路径
		img = frame[:, :, ::-1]

		results = self.model(img, imgsz=640)
		if len(results) == 0:
			return []

		r = results[0]
		boxes = []
		if hasattr(r, 'boxes') and r.boxes is not None:
			xyxy = r.boxes.xyxy.cpu().numpy()
			confs = r.boxes.conf.cpu().numpy()
			cls = r.boxes.cls.cpu().numpy()
			for xy, conf, c in zip(xyxy, confs, cls):
				# 仅保留类别 0（person）
				if int(c) != 0:
					continue
				if conf < self.conf_thres:
					continue
				x1, y1, x2, y2 = map(int, xy)
				boxes.append((x1, y1, x2 - x1, y2 - y1))

		return boxes

	def draw_boxes(self, frame, boxes, color=(0, 255, 0), thickness=2):
		for (x, y, w, h) in boxes:
			cv2.rectangle(frame, (x, y), (x + w, y + h), color, thickness)
		return frame


__all__ = ['PersonDetector']

 