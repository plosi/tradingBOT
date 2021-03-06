# Overview
Simple python app that makes an API call to alphavantage to retrieve the exchange rate from BTC to EUR and simulate trading based on MACD strategy. Graphs are generated and displayed using plotly dash.

#### Lesson learnt - note to my future self
There is an issue when you run the app in a docker container, that I didn't know at the beginning. Basically it looks like the dash app goes to sleep when there are no clients connected, and in fact the interval update callback function stops. So if you put the fucntion to make the API call in the dash app, this will work only as long as there is a client connected to the webpage. The workaround is to make a script which is not called directly by the dash app but that can be called via crontab, and then to make it available on the host computer by mounting a volume when running the container.

# Set-up instructions

## docker
#### folder structure:
<pre><code>
/app
  |_/data
      |_btc_trend.csv
      |_bal.csv
  |_dashboard.py
  |_Dockerfile
  |_requirements.txt
</code></pre>

#### build the image:
<pre><code>docker build -t tradingbot .</code></pre>

#### save image to tar:
<pre><code>docker save -o /full/path/to/tradingbot.tar tradingbot</code></pre>

#### copy the image to the new system and then load it with the following command:
<pre><code>docker load -i /full/path/to/tradingbot.tar</code></pre>

#### run the image into a container:
<pre><code>docker run -d -p 8050:8050 -v /full/path/to/workdir/data:/app/data --name tradingbot tradingbot:latest</code></pre>

## crontab

#### call the tradingbot script every 5 minutes:
<pre><code>*/5 * * * * cd /full/path/to/workdir && /usr/bin/python3 /full/path/to/workdir/tradingbot.py</code></pre>
