from PIL import Image, ImageDraw
from exp import _EXP

# パラメータ
CELL_SIZE = 20
GRID_COLOR = (255, 182, 193)    # 薄いピンク
FILL_COLOR = (255, 0, 127)      # 濃いピンク
BG_COLOR = (240, 245, 255)      # 薄い青（背景）

def render_exp(exp, name):
	# グリッドデータ作成
	rows = exp.strip().split("\n")
	grid = [[1 if c.strip() == '1' else 0 for c in row.split(",")] for row in rows]
	height, width = len(grid), len(grid[0])-1

	# 画像作成
	img = Image.new("RGB", (width * CELL_SIZE, height * CELL_SIZE), BG_COLOR)
	draw = ImageDraw.Draw(img)

	# 描画処理
	for y in range(height):
	    for x in range(width):
	        x0, y0 = x * CELL_SIZE, y * CELL_SIZE
	        x1, y1 = x0 + CELL_SIZE - 1, y0 + CELL_SIZE - 1

	        if grid[y][x] == 1:
	            draw.rectangle([x0, y0, x1, y1], fill=FILL_COLOR)

	        # グリッド線
	        draw.rectangle([x0, y0, x1, y1], outline=GRID_COLOR)

	# 表示
	# img.show()
	# 保存
	img.save(f"exp_rend/{name}.png")


# _EXPの全要素を描画
for key in _EXP:
	render_exp(_EXP[key], key)