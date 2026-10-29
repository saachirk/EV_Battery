import os, pandas as pd
path = r'C:\EV_Vehicle\ev_battery_test_data (1).xlsx'
print('exists=', os.path.exists(path))
xl = pd.ExcelFile(path)
print('sheets=', xl.sheet_names)
for sheet in xl.sheet_names:
    df = pd.read_excel(path, sheet_name=sheet)
    print('\nSHEET', sheet)
    print(df.head().to_string(index=False))
    print('shape=', df.shape)
    print('columns=', list(df.columns))
    print('dtypes=')
    print(df.dtypes.to_string())
    print('missing=')
    print(df.isna().sum().to_dict())
    for c in df.columns:
        lc = c.lower()
        if lc in {'fault','fault_type','label','battery_condition','condition','status','target','class'}:
            print('TARGET', c)
            print(df[c].value_counts(dropna=False).to_string())
