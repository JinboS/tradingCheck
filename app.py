import numpy as np
import pandas as pd
import pytz
import yfinance as yf
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# 预定义需要跟踪的美股股票列表（去掉 FB，或改为 META 等）
STOCKS = ["AAPL", "GOOGL", "AMZN", "TSLA", "MSFT", "NFLX", "NVDA", "INTC", "AMD"]

# 时区映射，可根据需要扩展更多选项
TIMEZONE_MAPPING = {
    "1": "America/New_York",   # 纽约
    "2": "America/Vancouver"   # 温哥华
}

def get_stock_data(ticker, interval, tz, period="1d"):
    """
    使用 yfinance 获取单个股票的历史数据，并转换到指定时区。
    period 参数：当使用分钟级别的数据时建议使用 "1d"，否则可以扩展为 "7d" 或更长。
    """
    try:
        data = yf.download(ticker, period=period, interval=interval, auto_adjust=False)
        if data.empty:
            return None
        
        # 检查索引是否已有时区，如果没有则本地化为UTC
        if data.index.tz is None:
            data.index = data.index.tz_localize('UTC')
        # 转换到指定时区
        data.index = data.index.tz_convert(tz)
        
        # 重置索引到普通列
        data.reset_index(inplace=True)
        
        # 如果是多级索引（MultiIndex），只取第一级
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        else:
            # 将所有列名转换为字符串，避免 JSON 序列化时的 tuple 键报错
            data.columns = data.columns.map(str)
        
        # 将时间列转换为字符串
        data['Datetime'] = data['Datetime'].astype(str)
        return data
    except Exception as e:
        print(f"获取 {ticker} 数据出错：{e}")
        return None

def compute_signals(df):
    """
    根据均线交叉策略计算买卖信号
    使用 5 日均线和 20 日均线进行判断：
      - 当上一时刻短期均线 <= 长期均线，而当前时刻短期均线 > 长期均线 => 买入
      - 当上一时刻短期均线 >= 长期均线，而当前时刻短期均线 < 长期均线 => 卖出
      - 其它情况 => 观望
    """
    short_window = 5
    long_window = 20
    
    # 数据不足时无法计算均线，默认信号为“观望”
    if len(df) < long_window:
        return df, "观望", []
    
    # 计算均线
    df['MA_short'] = df['Close'].rolling(window=short_window).mean()
    df['MA_long']  = df['Close'].rolling(window=long_window).mean()
    
    signals = []
    current_signal = "观望"
    
    for i in range(long_window, len(df)):
        prev_short = df['MA_short'].iat[i-1]
        prev_long  = df['MA_long'].iat[i-1]
        if pd.isna(prev_short) or pd.isna(prev_long):
            continue
        curr_short = df['MA_short'].iat[i]
        curr_long  = df['MA_long'].iat[i]
        
        if prev_short <= prev_long and curr_short > curr_long:
            signals.append({"index": i, "signal": "买入"})
            current_signal = "买入"
        elif prev_short >= prev_long and curr_short < curr_long:
            signals.append({"index": i, "signal": "卖出"})
            current_signal = "卖出"
    
    return df, current_signal, signals

@app.route("/")
def index():
    return render_template("index.html", stocks=STOCKS)

@app.route("/data")
def data():
    # 从前端获取 interval / tz 参数
    interval = request.args.get("interval", "1m")
    tz_option = request.args.get("tz", "1")
    tz = TIMEZONE_MAPPING.get(tz_option, "America/New_York")
    
    # 根据间隔选择查询周期
    # 分钟级用 "1d"，小时级或日级可以用更长周期
    if interval in ["1m", "5m", "15m", "10m"]:
        period = "1d"
    else:
        period = "7d"
    
    all_data = {}
    
    for ticker in STOCKS:
        df = get_stock_data(ticker, interval, tz, period)
        # 如果下载失败或为空，跳过
        if df is None or df.empty:
            continue
        
        # 计算信号
        df, current_signal, signals = compute_signals(df)
        
        # 将 NaN/Inf 替换为 None，避免 JSON 序列化错误
        df.replace({np.nan: None, np.inf: None, -np.inf: None}, inplace=True)
        
        # 获取最新价格（最后一行 Close）
        last_price = None
        if len(df) > 0 and df['Close'].iat[-1] is not None:
            last_price = float(df['Close'].iat[-1])
        
        all_data[ticker] = {
            "data": df.to_dict(orient="list"),
            "current_signal": current_signal,
            "signals": signals,
            "last_price": last_price
        }
    
    return jsonify(all_data)

if __name__ == "__main__":
    # 启动 Flask
    app.run(debug=True)
