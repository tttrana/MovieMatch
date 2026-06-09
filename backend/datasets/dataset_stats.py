import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("imdb.csv")

title_type_counts = df['titleType'].value_counts()
print("Distribuția tipurilor de titlu:")
print(title_type_counts)

plt.figure(figsize=(8,4))
title_type_counts.plot(kind='bar')
plt.xlabel('Tip titlu')
plt.ylabel('Număr de filme')
plt.title('Distribuția tipurilor de titlu')
plt.tight_layout()
plt.savefig("title_type_distribution.svg")
plt.close()

year_counts = df['startYear'].value_counts().sort_index()
print("\nDistribuția pe ani:")
print(year_counts)

plt.figure(figsize=(12,5))
year_counts.plot(kind='bar')
plt.xlabel('An')
plt.ylabel('Număr de filme')
plt.title('Distribuția filmelor pe ani')
plt.tight_layout()
plt.savefig("year_distribution.svg")
plt.close()