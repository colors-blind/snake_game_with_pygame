# Snake Lab (pygame)

一个多模块结构的贪吃蛇实验项目，带有基础状态机、日志面板、加速机制、毒果机制和本地存档。

## 模块划分

- `src/config.py`: 游戏配置、颜色主题
- `src/events.py`: 枚举状态和食物类型
- `src/models.py`: 数据模型（Snake/Food/Stats）
- `src/systems.py`: 输入缓冲、规则系统、存档系统、生成系统
- `src/ui.py`: 绘制逻辑和面板 UI
- `src/game.py`: 主游戏状态机与主循环
- `src/main.py`: 启动入口

## 运行

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m src.main
```

## 操作

- `Enter`: 开始游戏
- `WASD` / `方向键`: 移动
- `P`: 暂停/继续
- `R`: 游戏结束后重开
- `Esc`: 退出
