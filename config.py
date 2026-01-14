# 全局可配置参数
# 推荐默认值（可在运行时/部署时修改）
CONF_THRES = 0.35
MIN_AREA = 500
CONFIRM_THRESHOLD = 2
MAX_MISSED = 10

# tracker 其他建议参数
MAX_DISTANCE = 60
MAX_LOST_TIME = 2.0
 
# same-frame deduplication (IoU threshold)
# IoU 阈值用于同一帧高度重叠框的去重，建议 0.6，可根据实验调整
IOU_THRESHOLD = 0.6
 
# 显示层空间去重阈值（像素），用于前端显示层避免同一帧多 ID 可视化
# 建议值 55（或 60），可通过页面热调节
SPATIAL_THRESHOLD = 55
 