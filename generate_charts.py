import matplotlib.pyplot as plt
import numpy as np
import os

# Create output directory if it doesn't exist
out_dir = "/Users/apple/Documents/graduation project/charts"
os.makedirs(out_dir, exist_ok=True)

# 1. System Latency Comparison
labels = ['Baseline (HTTP + RAG)', 'Proposed (WebRTC + CRAG)']
values = [6.5, 2.85]
colors = ['#ff9999', '#66b3ff']

plt.figure(figsize=(8, 5))
bars = plt.bar(labels, values, color=colors, width=0.5)
plt.ylabel('Total Latency (Seconds)', fontsize=12)
plt.title('System Latency Comparison (Lower is Better)', fontsize=14, pad=15)
plt.ylim(0, 8)

# Add values on top of bars
for bar in bars:
    yval = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2, yval + 0.2, f'{yval}s', ha='center', va='bottom', fontweight='bold', fontsize=11)

plt.tight_layout()
plt.savefig(os.path.join(out_dir, 'chart_latency.png'), dpi=300)
plt.close()

# 2. RAGAS Evaluation Metrics
labels_ragas = ['Faithfulness', 'Answer\nRelevance', 'Context\nPrecision', 'Context\nRecall']
values_ragas = [94, 89, 91, 88]
colors_ragas = ['#4CAF50', '#2196F3', '#FFC107', '#9C27B0']

plt.figure(figsize=(9, 5))
bars2 = plt.bar(labels_ragas, values_ragas, color=colors_ragas, width=0.6)
plt.ylabel('Score (%)', fontsize=12)
plt.title('RAG Quality Metrics (RAGAS)', fontsize=14, pad=15)
plt.ylim(0, 110)

# Add values on top of bars
for bar in bars2:
    yval = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2, yval + 2, f'{yval}%', ha='center', va='bottom', fontweight='bold', fontsize=11)

plt.tight_layout()
plt.savefig(os.path.join(out_dir, 'chart_ragas.png'), dpi=300)
plt.close()

print(f"Charts generated successfully in {out_dir}")
