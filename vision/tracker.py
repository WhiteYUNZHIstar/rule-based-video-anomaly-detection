import time
import math

class SimpleTracker:
    def __init__(self, max_distance=50, max_lost_time=2.0, max_missed=10, confirm_threshold=2):
        """
        Args:
            max_distance: 中心点匹配的最大距离（像素）
            max_lost_time: 目标消失多久后按时间删除（秒）
            max_missed: 连续未匹配的最大帧数，超过则删除（ghost track 处理）
            confirm_threshold: 新目标确认所需连续检测帧数
        """
        self.next_id = 0
        self.objects = {}  # id -> data
        self.max_distance = max_distance
        self.max_lost_time = max_lost_time
        self.max_missed = max_missed
        self.confirm_threshold = confirm_threshold

    def _center(self, box):
        x, y, w, h = box
        return (x + w // 2, y + h // 2)

    def _distance(self, c1, c2):
        return math.hypot(c1[0] - c2[0], c1[1] - c2[1])

    def update(self, boxes):
        """
        Update tracker with detected boxes.
        Args:
            boxes: list of (x,y,w,h)
        Returns:
            objects: dict of tracked objects
        """
        now = time.time()
        centers = [self._center(b) for b in boxes]

        used = set()
        # 尝试匹配已有对象
        for obj_id, obj in list(self.objects.items()):
            min_dist = float('inf')
            min_idx = -1
            for i, c in enumerate(centers):
                if i in used:
                    continue
                d = self._distance(obj['center'], c)
                if d < min_dist:
                    min_dist = d
                    min_idx = i

            if min_dist < self.max_distance and min_idx != -1:
                # 匹配成功：重置 missed，并更新信息；同时增加确认计数
                obj['center'] = centers[min_idx]
                obj['box'] = boxes[min_idx]
                obj['last_seen'] = now
                obj['frames'] += 1
                obj['missed'] = 0
                # increase confirm frames when matched
                obj['confirm_frames'] = obj.get('confirm_frames', 0) + 1
                if not obj.get('confirmed', False) and obj['confirm_frames'] >= self.confirm_threshold:
                    obj['confirmed'] = True
                used.add(min_idx)
            else:
                # 未匹配：增加 missed 计数并根据阈值删除幽灵目标
                obj['missed'] = obj.get('missed', 0) + 1
                if obj['missed'] > self.max_missed or (now - obj.get('last_seen', now)) > self.max_lost_time:
                    del self.objects[obj_id]

        # 新增未匹配的检测框
        for i, c in enumerate(centers):
            if i not in used:
                # 新目标初始时未确认
                confirmed = True if self.confirm_threshold <= 1 else False
                self.objects[self.next_id] = {
                    'center': c,
                    'box': boxes[i],
                    'start_time': now,
                    'last_seen': now,
                    'frames': 1,
                    'missed': 0,
                    'confirm_frames': 1,
                    'confirmed': confirmed
                }
                self.next_id += 1

        return self.objects


__all__ = ['SimpleTracker']
 