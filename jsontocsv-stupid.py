import pandas as pd

df = pd.read_json (r'text.xml')
df.to_csv (r'output.csv', index = None)