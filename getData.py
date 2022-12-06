import  tushare as ts
import time

# Format 2016-03-20 11:45:39

today=str(time.strftime("%Y%m%d", time.localtime()))
print(today)
pro = ts.pro_api("a14baf518dcd65b3cd7f8efee461df9467d1c3b6d6496cc181b33885")

# Acquire a single stock data.
df = pro.daily(ts_code='000001.SZ', start_date='20190101', end_date='20190904')
print(df)


