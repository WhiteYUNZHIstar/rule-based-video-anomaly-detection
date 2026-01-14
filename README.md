# 基于规则驱动的视频异常行为检测系统（最终交付版）

本 README 与当前代码实现保持一致，用于项目最终交付与复现说明。

## 项目简介

本项目采用规则驱动（rule-based）方法对视频中的人员行为进行异常检测，强调可解释性、工程可控性与实验可复现性。系统不进行端到端行为分类训练，而是基于稳定的人体检测与可调轨迹规则来判定异常（例如长时间停留）。

设计思路：高质量输入（稳定目标检测） → 可解释规则 → 可视化与实验验证。

该系统作为一个轻量级异常检测基线，适用于教学、实验验证与工程原型展示。

## 系统架构

整体流程：

- **YOLO11n**：逐帧人体检测（项目中作为唯一检测器，模型文件位于 `models/yolo11n.pt`）。
- **SimpleTracker**：基于中心点距离的多目标跟踪（含确认与丢弃机制）。
- **Rules**：基于轨迹与时间的规则判断（如滞留/loitering）。
- **Visualization**：OpenCV 用于视频读取与绘制，Flask 提供前端展示与参数调节。

注：OpenCV 在本系统中仅用于视频 I/O 与结果可视化，不作为检测算法实现。

## 核心模块说明

- `vision/detector.py`：封装 Ultralytics YOLO（YOLO11n）为 `PersonDetector`，接口：`detect(frame) -> [(x, y, w, h)]`。
- `vision/tracker.py`：`SimpleTracker`，基于中心点距离匹配，包含 `missed`/`max_missed` 与 `confirm_frames`/`confirmed` 等机制，用于抑制瞬时误检与幽灵目标。
- `vision/rules.py`：规则集合，目前实现滞留检测函数 `detect_anomalies(objects, loiter_time)`。
- `app.py`：Flask 服务入口，提供视频流接口 `video_feed`、主页面 `index.html`，并支持前端运行时参数调节接口 `/set_params`。
- `config.py`：集中管理检测、跟踪与显示相关阈值，便于实验调参与复现。

## 模型选择（YOLO11n）

采用 Ultralytics YOLO11n 作为唯一人体检测模型（`models/yolo11n.pt`）。选择理由：

- 稳定性：YOLO 系列在行人检测上表现稳定，逐帧误差小，利于规则判定。
- 实时性：`n` 级模型计算开销低，适合 CPU/边缘设备演示。
- 可复现性：单一确定模型减少实验变量。

开发调试阶段可临时使用 Ultralytics 内置模型名（如 `yolov8n`），正式复现建议使用本地 `yolo11n.pt`。

## 快速复现（Quick Start）

1. 创建并激活虚拟环境（推荐）：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. 安装依赖：

```powershell
pip install -r requirements.txt
```

3. 放置模型：将 `yolo11n.pt` 放入 `models/` 目录（开发阶段可用 ultralytics 名称替代）。

4. 启动服务并访问：

```powershell
python app.py
# 浏览器访问: http://127.0.0.1:5000/
```

## 配置与参数（`config.py`）

关键阈值集中在 `config.py`，默认值示例如下：

```python
CONF_THRES = 0.35         # 检测置信度阈值
MIN_AREA = 500            # 最小检测框面积（像素）
CONFIRM_THRESHOLD = 2     # 目标确认所需连续帧数
MAX_MISSED = 10           # 最大未匹配帧数
MAX_DISTANCE = 60         # 中心点匹配最大距离（像素）
MAX_LOST_TIME = 2.0       # 基于时间的目标删除阈值（秒）
SPATIAL_THRESHOLD = 55    # 显示层同帧空间去重阈值（像素）
IOU_THRESHOLD = 0.6       # 保留用于实验记录（通常不在检测层直接使用）
```

建议调参：

- 若仍有极少误检：将 `CONF_THRES` 提高至 `0.40` 或把 `MIN_AREA` 提高到 `600`。
- 若远处小人漏检：把 `MIN_AREA` 降到 `400`。
- 若偶发一帧闪现的框：把 `CONFIRM_THRESHOLD` 提高到 `3`。
- 若遮挡后 ID 容易丢失：把 `MAX_MISSED` 提高到 `12`。

这些参数可直接在 `config.py` 修改，或通过前端控制面板热更新 `MIN_AREA` 与 `SPATIAL_THRESHOLD`（无需重启）。

## 前端热调（运行时生效）

主页面提供参数控制面板，支持热更新：

- `MIN_AREA`（检测兜底）
- `SPATIAL_THRESHOLD`（显示层同帧去重阈值）

提交后参数即时生效，不会直接改变 tracker 内部匹配逻辑，仅影响检测过滤与显示层可视化，适合用于实验对比与论文/答辩演示。

## 实验验证与结果

在测试视频 `static/videos/test.mp4` 上以默认参数进行端到端验证（示例）：

- 处理帧数：100
- 应用 `MIN_AREA=500` 后检测框数：26
- 累计确认轨迹数：25
- 当前稳定跟踪对象数：1
- 滞留异常（阈值 3s）：0（无误报）

结论：通过检测置信度控制、最小面积过滤与目标确认机制，系统在该测试集上有效抑制瞬时误检与幽灵目标，满足规则驱动异常检测对稳定输入的需求。

## 已知限制与改进方向

- **简化的跟踪器**：当前使用基于位置的 `SimpleTracker`，适合低复杂度场景；复杂场景建议引入外观特征或更先进的跟踪算法。
- **单摄像头假设**：未考虑相机运动补偿或多视角融合。
- **规则可扩展**：当前以滞留检测为主，可扩展区域闯入、异常移动等规则，并加入事件日志或告警机制。

## 项目说明

本项目为计算机视觉应用实训项目，主要用于教学与实验研究，不作为实际安防系统部署的最终解决方案。

---

更多实现细节请参阅代码：`config.py`、`app.py` 与 `vision/` 子模块。
# 最终版本声明：本 README 为项目最终交付版本，内容与当前代码实现保持一致。

# 基于规则驱动的视频异常行为检测系统

## 项目简介

本项目采用规则驱动（rule-based）方法对视频中的人员行为进行异常检测，强调可解释性与工程可复现性。系统不进行端到端行为分类训练，而是基于稳定的人体检测（YOLO11n）与简单可控的轨迹分析规则来判定异常（例如长时间停留、区域闯入）。

设计目标是提供一个轻量、易调参、便于教学与工程验证的异常检测基线：高质量输入（稳定目标检测）→ 简明可解释的规则 → 可视化与实验验证。

## 系统架构

总体流程：

- YOLO11n（逐帧检测，模型为唯一检测器）
- SimpleTracker（基于中心点匹配，含确认与丢弃策略）
- Rules（基于轨迹与时间的规则判断，如滞留）
- Visualization（OpenCV 用于视频读取、绘制与 Flask 前端展示）

注意：OpenCV 在本系统中仅用于视频 I/O 与结果可视化，不作为检测算法。

## 核心模块说明

- `vision/detector.py`：封装 Ultralytics YOLO（YOLO11n）为 `PersonDetector`，接口 `detect(frame) -> [(x,y,w,h)]`。
- `vision/tracker.py`：`SimpleTracker`，基于中心点距离匹配，包含 `missed`、`max_missed`、`confirm_frames` 与 `confirmed` 机制以避免幽灵目标与瞬时误检。
- `vision/rules.py`：规则集合，目前包含滞留（loitering）检测函数 `detect_anomalies(objects, loiter_time)`。
- `app.py`：Flask 服务，提供视频流 `video_feed` 及主页面 `index.html`（前端展示检测框、ID 与当前配置）。
- `config.py`：集中配置（检测与跟踪阈值），便于复现实验。

## 模型选择说明（YOLO11n）

本系统严格采用 Ultralytics YOLO11n 作为唯一人体检测器（`models/yolo11n.pt`）。理由：

- 稳定性：YOLO 系列在目标检测（尤其行人检测）上表现稳定，逐帧检测误差低，有利于后续规则判定。 
- 资源与实时性：选择轻量化的 `n`（nano）或相近权重以兼顾 CPU/边缘设备的推理速度，便于演示与部署。 
- 可复现性：使用单一确定模型简化实验变量，便于比较与调参。

如果没有本地权重文件，开发模式下可使用 ultralytics 自带的模型名（如 `yolov8n`）作暂时替代，但生产/演示应把 `yolo11n.pt` 放在 `models/` 目录。

## 运行与复现（Quick Start）

1. 创建并激活虚拟环境（推荐）：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. 安装依赖：

```powershell
pip install -r requirements.txt
```

3. 放置模型：将 `yolo11n.pt` 放入项目 `models/` 目录。若无，可先用 ultralytics hub 名称进行开发调试（见上节）。

4. 启动服务：

```powershell
python app.py
# 浏览器访问: http://127.0.0.1:5000/
```

## 配置与默认参数（config.py）

系统将重要阈值集中放在 `config.py`，默认值如下（工程含义同注释）：

```python
CONF_THRES = 0.35         # 检测置信度阈值
MIN_AREA = 500            # 最小检测框面积（像素）
CONFIRM_THRESHOLD = 2     # 新目标被标记为 `confirmed` 前需连续检测到的帧数
MAX_MISSED = 10           # 连续未匹配的最大帧数（超出则删除轨迹）
MAX_DISTANCE = 60         # 匹配中心点的最大距离（像素）
MAX_LOST_TIME = 2.0       # 基于时间的目标删除阈值（秒）
```

调参速查：

- 若仍有极少误检：`CONF_THRES -> 0.40` 或 `MIN_AREA -> 600`。
- 若远处小人被漏检：`MIN_AREA -> 400`。
- 若偶发 1 帧闪现的框：`CONFIRM_THRESHOLD -> 3`。
- 若遮挡后 ID 容易消失：`MAX_MISSED -> 12`。

这些配置均可直接在 `config.py` 修改，无需改代码。

## 实验验证与结果

对同一测试视频（`static/videos/test.mp4`）执行 100 帧的端到端验证（参数使用 `config.py` 默认值）：

- 处理帧数：100
- 检测到的总框数（应用 `MIN_AREA=500` 后）：26
- 确认的轨迹观察累计（跨帧计数）：25
- 当前跟踪对象数：1（已确认对象）
- 检测到的滞留异常（loitering, 阈值 3s）：0（无滞留误报）

结论：通过提高检测置信度、最小面积过滤以及引入目标确认机制，系统有效抑制了瞬时误检与幽灵目标问题，满足规则驱动异常检测模块对稳定输入的需求。

## 已知限制与未来改进方向

- Tracker 简单：当前使用基于位置的 `SimpleTracker`（非 DeepSORT/ByteTrack），适合单摄像头与相对低复杂度场景；复杂场景建议引入外观信息或更先进的多目标跟踪算法。 
- 单摄像头：系统未做相机运动补偿与视角鲁棒性处理。 
- 规则可扩展：当前规则以滞留为主，可按需求扩展区域闯入、异常移动等，并可加入阈值化的告警策略（邮件/SMS/日志）。

可选后续工作：将前端配置调整为可交互表单、集成事件日志、或替换为更高级的 tracker 以支持复杂场景。
本项目为计算机视觉应用开发实训项目，主要用于教学与实验研究，不涉及实际安防系统部署。

**配置与默认参数**

推荐默认配置（可在 `config.py` 中调整）：

- **CONF_THRES**: 0.35  — 检测置信度阈值，过滤低置信度误检。
- **MIN_AREA**: 500  — 检测框最小面积（像素），用于去除远处或噪声小框。
- **CONFIRM_THRESHOLD**: 2  — 新目标被标记为 `confirmed` 前需连续检测到的帧数。
- **MAX_MISSED**: 10  — 连续未匹配帧数超过该值则删除 track（防止幽灵目标）。
- **MAX_DISTANCE**: 60  — 中心匹配的最大距离（像素）。
- **MAX_LOST_TIME**: 2.0  — 基于时间的目标删除阈值（秒）。

调参建议（快速参考）：

- 若仍有极少误检：将 `CONF_THRES` 调至 0.40 或把 `MIN_AREA` 提高到 600。
- 若远处小人漏检：把 `MIN_AREA` 降到 400。
- 若偶发 1 帧闪现的框：把 `CONFIRM_THRESHOLD` 提高到 3。
- 若遮挡后 ID 容易消失：把 `MAX_MISSED` 提高到 12。

测试说明：系统通过提高检测置信度、最小面积过滤以及引入目标确认机制（confirmed tracks），有效抑制了瞬时误检与幽灵目标问题。在 100 帧真实视频验证中，系统仅保留稳定目标轨迹，未产生异常误报，验证了规则驱动异常检测在稳定输入条件下的可靠性。
