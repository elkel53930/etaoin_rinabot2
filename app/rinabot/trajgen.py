from math import fabs, sin, pi

# サイン補間により、startからendまでtime秒かけて遷移する値のリストを生成する関数
def t_sin(start, end, time, dt=0.05):
    if time == 0:
        # 時間がゼロなら一瞬で終了 → 終点のみ返す
        return [end]
    if start == end:
        # 移動がない場合は、すべて同じ値を返す（長さ = time / dt）
        return [start] * (int(time / dt) + 1)

    result = []
    S = end - start  # 変位（移動量）
    step = int(time / dt)  # サンプル数（繰り返し回数）
    
    # サインカーブの周期に合わせて dt を角度（ラジアン）単位に変換
    dt = dt * 2 * pi / time

    # 補間用スケール変換（後で積分に相当する形で使う）
    S = S / 2 / pi

    # サイン関数を積分したような形でなめらかに遷移する値を計算
    for i in range(step):
        t = i * dt
        # サインカーブに沿って滑らかに変化する値を計算しリストに追加
        result.append((t - sin(t)) * S + start)

    result.append(end)  # 最後は必ずendを追加して終了位置を保証
    return result


def t_linear(start, end, time, dt=0.05):
    if time == 0:
        return [end]
    if start == end:
        return [start] * (int(time / dt) + 1)
    t_step = int(time/dt)
    x_step = (end-start)/t_step
    result = [start + x_step * i for i in range(t_step)]
    result.append(end)
    return result
