import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os
from sklearn.cluster import KMeans
import numpy as np

def generate_graphs(path, x_col, y_col, chart_type):
    try:
        if path.endswith('.csv'):
            df = pd.read_csv(path)
        elif path.endswith('.xlsx'):
            df = pd.read_excel(path, engine='openpyxl')
        else:
            return []
    except Exception as e:
        print(f"Failed to load file: {e}")
        return []

    # Drop rows with NaNs in selected columns
    df = df[[x_col, y_col]].dropna()

    # Convert non-numeric columns to string (for display)
    if not pd.api.types.is_numeric_dtype(df[x_col]):
        df[x_col] = df[x_col].astype(str)
    if not pd.api.types.is_numeric_dtype(df[y_col]):
        df[y_col] = df[y_col].astype(str)

    # Convert for KMeans if both columns are numeric
    if pd.api.types.is_numeric_dtype(df[x_col]) and pd.api.types.is_numeric_dtype(df[y_col]):
        if len(df) > 50:
            kmeans = KMeans(n_clusters=50, random_state=0)
            kmeans.fit(df[[x_col, y_col]])
            df['cluster'] = kmeans.labels_

            # Take the point closest to each cluster center
            df['distance'] = np.linalg.norm(df[[x_col, y_col]] - kmeans.cluster_centers_[df['cluster']], axis=1)
            df = df.loc[df.groupby('cluster')['distance'].idxmin()]

        df = df.sort_values(by=x_col)

    os.makedirs("media/graphs", exist_ok=True)
    file = f'media/graphs/{chart_type}_{x_col}_{y_col}.png'

    plt.figure(figsize=(8, 6))
    try:
        if chart_type == 'bar':
            sns.barplot(x=df[x_col], y=df[y_col])
        elif chart_type == 'line':
            sns.lineplot(x=df[x_col], y=df[y_col])
        elif chart_type == 'scatter':
            sns.scatterplot(x=df[x_col], y=df[y_col])
        elif chart_type == 'pie':
            if not pd.api.types.is_numeric_dtype(df[y_col]):
                df[y_col] = df[y_col].astype(float)
            df.groupby(x_col)[y_col].sum().plot.pie(autopct='%1.1f%%')
        else:
            return []
    except Exception as e:
        print(f"Plot error: {e}")
        return []

    plt.title(f"{chart_type.capitalize()} of {y_col} vs {x_col}")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(file)
    plt.close()

    return ["/" + file]
