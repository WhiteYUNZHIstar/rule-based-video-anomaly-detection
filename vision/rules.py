"""规则驱动的异常检测模块

当前实现：简单的滞留（loitering）规则。

函数:
    detect_anomalies(objects, loiter_time=10.0)
        objects: tracker 返回的 dict (id -> {'start_time', 'last_seen', 'center', 'box', ...})
        返回: dict: obj_id -> reason
"""
import time


def detect_anomalies(objects, loiter_time=10.0):
    """检测简单规则：当目标存在时间超过 loiter_time 视为滞留异常。

    Args:
        objects: dict, tracker 输出
        loiter_time: 秒

    Returns:
        anomalies: dict of id -> reason string
    """
    anomalies = {}
    now = time.time()
    for obj_id, obj in objects.items():
        start = obj.get('start_time', now)
        duration = now - start
        if duration >= loiter_time:
            anomalies[obj_id] = f'loitering:{duration:.1f}s'
    return anomalies


__all__ = ['detect_anomalies']
