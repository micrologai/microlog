import squarify
import folderstats
import matplotlib.pyplot as plt

df = folderstats.folderstats('../pandas/', ignore_hidden=True)


# Group by extension and sum all sizes for each extension
extension_sizes = df.groupby('extension')['size'].sum()
# Sort elements by size
extension_sizes = extension_sizes.sort_values(ascending=False)

squarify.plot(sizes=extension_sizes.values, label=extension_sizes.index.values)
plt.title('Extension Treemap by Size')
plt.axis('off')
