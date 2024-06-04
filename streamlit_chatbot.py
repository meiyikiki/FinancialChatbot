import json
import openai
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
import yfinance as yf
import requests


openai.api_key = st.secrets["OPENAI_API_KEY"]


def get_stock_price(ticker):
    return str(yf.Ticker(ticker).history(period='1y').iloc[-1].Close)


def calculate_SMA(ticker, window):
    data = yf.Ticker(ticker).history(period='1y').Close
    return str(data.rolling(window=window).mean().iloc[-1])


def calculate_EMA(ticker, window):
    data = yf.Ticker(ticker).history(period='1y').Close
    return str(data.ewm(span=window, adjust=False).mean().iloc[-1])


def calculate_RSI(ticker):
    data = yf.Ticker(ticker).history(period='1y').Close
    data = data.diff()
    up = data.clip(lower=0)
    down = -1 * data.clip(upper=0)
    ema_up = up.ewm(com=14 - 1, adjust=False).mean()
    ema_down = down.ewm(com=14 - 1, adjust=False).mean()
    rs = ema_up / ema_down
    return str(100 - (100 / (1 + rs)).iloc[-1])


def calculate_MACD(ticker):
    data = yf.Ticker(ticker).history(period='1y').Close
    short_EMA = data.ewm(span=12, adjust=False).mean()
    long_EMA = data.ewm(span=26, adjust=False).mean()

    MACD = short_EMA - long_EMA
    signal = MACD.ewm(span=9, adjust=False).mean()
    MACD_histogram = MACD - signal

    return f'{MACD[-1]}, {signal[-1]}, {MACD_histogram[-1]}'


def plot_stock_price(ticker):
    data = yf.Ticker(ticker).history(period='1y')
    plt.figure(figsize=(10, 5))
    plt.plot(data.index, data.Close)
    plt.title('{ticker} Stock Price Over Last Year')
    plt.xlabel('Date')
    plt.ylabel('Stock Price ($)')
    plt.grid(True)
    plt.savefig('stock.png')
    plt.close()

# Will put more functions that could take the ticker variable


def identify_request(user_input):
    if 'SMA' in user_input:
        return 'SMA'
    elif 'EMA' in user_input:
        return 'EMA'
    elif 'RSI' in user_input:
        return 'RSI'
    elif 'MACD' in user_input:
        return 'MACD'
    elif 'stock price' in user_input:
        return 'stock price'
    else:
        return None


def extract_ticker_with_chatgpt(user_input):
    try: 
        response = openai.ChatCompletion.create(
            model='gpt-4',
            
            messages=[
                {"role": "system", "content": "You are a financial assistant. Extract the ticker symbol from user requests."},
                {"role": "user", "content": user_input}
            ],
            # prompt="Extract the ticker symbol from this request: '{user_input}'",
            max_tokens=10
        )
        print(response)
        content = response['choices'][0]['message']['content']
        print("API response:", content)  # This will print the API response to the console
        return content.strip()
    except Exception as e:
        print(f"Error: {e}")  # This will print any errors that occur during the API call
        return str(e)
    
if 'messages' not in st.session_state:
    st.session_state['messages'] = []

st.title('Stock Analyst Chaptbot Assistant')

# Initialize user_input
user_input = st.text_input('Your Input:', '')  # Default value set to an empty string

# Main logic in your Streamlit app
if st.button('Analyze'):
    st.session_state['messages'].append({'role': 'user', 'content': user_input})

    # Assuming the function identify_request exists and is designed to determine the type of financial analysis to perform
    ticker = extract_ticker_with_chatgpt(user_input)
    st.write(f"Extracted ticker: {ticker}")
    
    request_type = identify_request(user_input)

    financial_data = None
    if request_type == 'stock price':
        financial_data = get_stock_price(ticker)
    elif request_type == 'SMA':
        financial_data = calculate_SMA(ticker, window=20)  # Use the extracted ticker
    elif request_type == 'EMA':
        financial_data = calculate_EMA(ticker, window=20)
    elif request_type == 'RSI':
        financial_data = calculate_RSI(ticker)
    elif request_type == 'MACD':
        financial_data = calculate_MACD(ticker)



    if financial_data:
            try:
                openai_response = openai.ChatCompletion.create(
                    model='gpt-4',
                    messages=[
                        {"role": "system", "content": "You are a professional Financial Analyst that provides easy to understand responses to requests."},
                        {"role": "user", "content": f"Interpret this financial data: {financial_data}\n{user_input}"}
                    ],
                    max_tokens=250
                )
                openai_interpretation = openai_response['choices'][0]['message']['content'].strip()

                combined_interpretation = openai_interpretation + "\n"
                st.session_state['messages'].append({'role': 'assistant', 'content': combined_interpretation})
                # st.text(combined_interpretation)
                st.text_area("Response", value=combined_interpretation, height=300)
            except Exception as e:
                st.error(f"Error interpreting financial data: {e}")

# Display all messages
# for message in st.session_state['messages']:
#     if message['role'] == 'user':
#         st.text(f"User: {message['content']}")
#     else:
#         st.text(f"Assistant: {message['content']}")