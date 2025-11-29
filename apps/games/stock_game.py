import matplotlib.pyplot as plt
import japanize_matplotlib

x = [1, 2, 3, 4, 5]
y = [1, 4, 9, 16, 25]

plt.plot(x, y)       # 折れ線グラフの描画
plt.xlabel('X軸')    # X軸ラベル
plt.ylabel('Y軸')    # Y軸ラベル
plt.title('折れ線グラフの例') # グラフタイトル
plt.grid(True)       # グリッド表示
plt.show()  # グラフの表示
