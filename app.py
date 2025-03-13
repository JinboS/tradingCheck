import datetime
import math
import pandas as pd
import numpy as np
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from data_retriever import get_stock_data, get_latest_price
from strategy import get_signals

app = FastAPI(title="美股量化交易系统")
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# 关注列表
watchlist = ['AAPL', 'MSFT', 'GOOG', 'AMZN', 'TSLA', 'META', 'NFLX', 'NVDA', 'BABA', 'INTC']

def convert_value(val):
    """递归将 NaN 转成 None，并把 numpy 类型转换为 Python 原生类型。"""
    if isinstance(val, float) and math.isnan(val):
        return None
    if isinstance(val, np.generic):
        val = val.item()
        if isinstance(val, float) and math.isnan(val):
            return None
        return val
    if isinstance(val, list):
        return [convert_value(x) for x in val]
    if isinstance(val, dict):
        return {str(k): convert_value(v) for k, v in val.items()}
    return val

def convert_records(records):
    """对每条记录做 convert_value 转换。"""
    new_records = []
    for r in records:
        new_records.append({str(k): convert_value(v) for k, v in r.items()})
    return new_records

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "watchlist": watchlist})

@app.get("/api/data")
async def api_data(symbol: str, interval: str = "1m"):
    try:
        end = datetime.datetime.now()
        start = end - datetime.timedelta(days=5)

        # 获取数据
        df = get_stock_data(symbol, start, end, interval)
        if df.empty:
            raise HTTPException(status_code=404, detail="未获取到数据")

        # 计算策略信号
        df = get_signals(df)

        # 如果存在多级列，则降级为单级列
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # 如果存在日期字段，转换为字符串格式
        if 'Datetime' in df.columns:
            df['Datetime'] = df['Datetime'].astype(str)

        # 将所有 NaN 值替换为 None
        df = df.where(pd.notnull(df), None)

        # 将 DataFrame 转换为字典列表，并递归转换数据类型
        records = df.to_dict(orient="records")
        records = convert_records(records)

        # 判断最新信号
        latest_signal = df['Position'].iloc[-1]
        if latest_signal == 1:
            signal_text = "买入信号"
        elif latest_signal == -1:
            signal_text = "卖出信号"
        else:
            signal_text = "观望"

        return {"data": records, "signal": signal_text}
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"error": e.detail})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/api/watchlist")
async def api_watchlist():
    try:
        results = []
        for symbol in watchlist:
            price = get_latest_price(symbol)
            # 在此打印，看看是什么
            print(f"symbol={symbol}, price={price}, type={type(price)}")
            results.append({"symbol": symbol, "price": price})
        return {"watchlist": results}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

if __name__ == '__main__':
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
