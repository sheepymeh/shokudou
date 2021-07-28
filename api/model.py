import pandas as pd

def model(buffer):
	df = pd.DataFrame.from_dict(buffer)
	return list(df.idxmax(axis='columns').value_counts().reindex(buffer.keys(), fill_value=0).sort_index(ascending=True))
