# 复活功能说明

## 功能概述

在游戏结束时，玩家可以选择"复活"来继续游戏。复活会删除3个数值最小的方块，为玩家创造继续游戏的空间。

## 实现细节

- **删除数量**: 3个最小方块（如果最小值方块少于3个，则全部删除）
- **复活次数**: 无限制
- **保留分数**: 复活后保持当前分数不变
- **不可撤销**: 复活操作不能通过"撤销"功能恢复

## 平台支持

已在以下三个平台实现：

### 1. Python 桌面版
- 文件: `game.py`, `ui.py`
- 运行: `python main.py`
- 游戏结束时会弹出对话框询问"是否使用复活？"

### 2. Web 版本
- 文件: `web/game.mjs`, `web/app.mjs`
- 运行: 打开 `web/index.html` 或运行 `python mobile.py`
- 游戏结束对话框中显示"复活"按钮

### 3. 抖音小程序版
- 文件: `douyin-miniapp/utils/game.js`, `douyin-miniapp/pages/index/`
- 游戏结束对话框中显示"复活"按钮

## 测试方法

### 自动测试
```bash
# Python 版本单元测试
python -m unittest tests.test_game -v

# 包含以下复活功能测试:
# - test_revive_removes_smallest_tiles: 测试删除最小方块
# - test_revive_fails_when_not_game_over: 测试非游戏结束状态
# - test_revive_with_fewer_than_3_min_tiles: 测试少于3个最小方块的情况
```

### 手动测试步骤

1. **启动游戏**
   - Python: `python main.py`
   - Web: `python mobile.py` 然后访问 http://localhost:8000

2. **玩到游戏结束**
   - 移动方块直到棋盘填满且无法移动

3. **测试复活功能**
   - 游戏结束后会出现对话框
   - Python版: 点击"是"使用复活
   - Web版: 点击"复活"按钮
   
4. **验证结果**
   - 棋盘上最小值的方块被删除（最多3个）
   - 游戏可以继续移动
   - 分数保持不变
   - 可以再次游戏直到结束并再次复活

## 技术实现

### 核心算法 (revive 方法)

1. 检查游戏是否处于结束状态
2. 找出棋盘上所有非零方块中的最小值
3. 收集所有等于最小值的方块位置
4. 随机打乱这些位置
5. 删除前3个位置的方块（设置为0）
6. 将 `game_over` 标志设置为 `False`
7. 返回成功

### 代码位置

- **Python**: `game.py` 第80-111行
- **Web**: `web/game.mjs` 第122-142行  
- **Douyin**: `douyin-miniapp/utils/game.js` 第163-183行
