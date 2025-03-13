// script.js

/**
 * 从后端获取指定股票的数据
 * @param {string} symbol 股票代码
 * @param {string} interval 数据间隔
 * @returns {Object|null} 后端返回的 JSON 对象 { data: [...], signal: ... }
 */
async function fetchData(symbol, interval) {
    const url = `/api/data?symbol=${symbol}&interval=${interval}`;
    try {
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`接口错误: ${response.statusText}`);
      }
      const data = await response.json();
      console.log("API Data:", data);
      return data;
    } catch (err) {
      console.error(err);
      alert("获取数据失败：" + err.message);
      return null;
    }
  }
  
  /**
   * 更新图表，基于所选时区 & 所选数据间隔 & 指定的股票代码
   * @param {string} symbol 要显示的股票代码
   */
  async function updateChart(symbol) {
    // 1. 获取后端数据
    if (!symbol) symbol = "AAPL";
    const interval = document.getElementById("interval").value;
    const selectedTz = document.getElementById("timezone").value;
  
    const dataObj = await fetchData(symbol, interval);
    if (!dataObj) return;
  
    const chartData = dataObj.data;
    const signal = dataObj.signal;
    document.getElementById("current-signal").innerText = signal;
  
    if (!chartData || chartData.length === 0) {
      alert("未获取到数据");
      return;
    }
  
    // 2. 处理日期
    const dates = chartData.map(item => new Date(item.Datetime));
    const openArr = chartData.map(item => item.Open);
    const highArr = chartData.map(item => item.High);
    const lowArr = chartData.map(item => item.Low);
    const closeArr = chartData.map(item => item.Close);
  
    // 3. 生成蜡烛图
    const candlestick = {
      x: dates,
      open: openArr,
      high: highArr,
      low: lowArr,
      close: closeArr,
      type: 'candlestick',
      name: '价格'
    };
  
    // 4. 如果有均线，添加均线
    const maShortArr = chartData.map(item => item.MA_short);
    const maLongArr = chartData.map(item => item.MA_long);
  
    const traceShort = {
      x: dates,
      y: maShortArr,
      mode: 'lines',
      name: '短期均线'
    };
    const traceLong = {
      x: dates,
      y: maLongArr,
      mode: 'lines',
      name: '长期均线'
    };
  
    // 5. 生成买卖点散点
    //    Position == 1 => 买入，Position == -1 => 卖出
    //    通常买入点画在 K 线的 Low，卖出点画在 High
    const buyX = [];
    const buyY = [];
    const sellX = [];
    const sellY = [];
  
    chartData.forEach(item => {
      if (item.Position === 1) {
        buyX.push(new Date(item.Datetime));
        buyY.push(item.Low);   // 你也可以用 item.Close
      } else if (item.Position === -1) {
        sellX.push(new Date(item.Datetime));
        sellY.push(item.High);
      }
    });
  
    const buyTrace = {
      x: buyX,
      y: buyY,
      mode: 'markers',
      marker: {
        symbol: 'triangle-up',
        color: 'green',
        size: 10
      },
      name: '买入'
    };
  
    const sellTrace = {
      x: sellX,
      y: sellY,
      mode: 'markers',
      marker: {
        symbol: 'triangle-down',
        color: 'red',
        size: 10
      },
      name: '卖出'
    };
  
    // 6. 计算并设置默认显示区间(纽约 9:30–16:00 -> 转到 selectedTz)
    const nyNow = moment().tz("America/New_York");
    const yNY = nyNow.year();
    const mNY = nyNow.month();
    const dNY = nyNow.date();
    const nyOpen = moment.tz([yNY, mNY, dNY, 9, 30], "America/New_York");
    const nyClose = moment.tz([yNY, mNY, dNY, 16, 0], "America/New_York");
    const marketOpen = nyOpen.clone().tz(selectedTz);
    const marketClose = nyClose.clone().tz(selectedTz);
    const layout = {
      title: `${symbol} K线图`,
      xaxis: {
        title: '时间',
        type: 'date',
        range: [marketOpen.toDate(), marketClose.toDate()],
        fixedrange: false
      },
      yaxis: {
        title: '价格',
        fixedrange: false
      },
      dragmode: 'pan',
      font: { family: 'Microsoft YaHei, sans-serif' }
    };
  
    const config = {
      scrollZoom: true,
      displaylogo: false
    };
  
    // 7. 合并所有 trace
    //    [candlestick, traceShort, traceLong, buyTrace, sellTrace]
    Plotly.newPlot('chart', [
      candlestick,
      traceShort,
      traceLong,
      buyTrace,
      sellTrace
    ], layout, config);
  }
  
  
  
  /**
   * 更新关注列表，并为每行绑定点击事件，点击后调用 updateChart(symbol)
   */
  async function updateWatchlist() {
    try {
      const response = await fetch(`/api/watchlist`);
      if (!response.ok) {
        throw new Error("关注列表接口错误");
      }
      const data = await response.json();
      console.log("Watchlist:", data);
  
      const tbody = document.querySelector("#watchlist-table tbody");
      tbody.innerHTML = "";
  
      data.watchlist.forEach(item => {
        const row = document.createElement("tr");
        // 把股票代码存到行属性里
        row.dataset.symbol = item.symbol;
  
        // 点击该行时，调用 updateChart
        row.addEventListener("click", function() {
          const clickedSymbol = this.dataset.symbol;
          updateChart(clickedSymbol);
        });
  
        // 创建单元格：股票代码、价格
        const tdSymbol = document.createElement("td");
        tdSymbol.innerText = item.symbol;
  
        const tdPrice = document.createElement("td");
        tdPrice.innerText = item.price;
  
        row.appendChild(tdSymbol);
        row.appendChild(tdPrice);
        tbody.appendChild(row);
      });
    } catch (err) {
      console.error(err);
    }
  }
  
  /**
   * 页面加载后初始化
   */
  document.addEventListener("DOMContentLoaded", () => {
    // 初始化图表和关注列表
    updateChart();       // 默认股票: AAPL
    updateWatchlist();
  
    // 如果有“刷新图表”按钮，就绑定事件
    const refreshBtn = document.getElementById("refreshBtn");
    if (refreshBtn) {
      refreshBtn.addEventListener("click", () => {
        // 这里也可以指定一个默认股票
        updateChart();
      });
    }
  
    // 每分钟自动刷新一次
    setInterval(() => {
      // 刷新图表，保留当前图表的 symbol
      // 这里可以自己决定：保留上次点击的 symbol？还是默认 "AAPL"？
      // 如果要保留上次 symbol，需要存个全局变量 lastSymbol
      updateChart();
      updateWatchlist();
    }, 60000);
  });
  