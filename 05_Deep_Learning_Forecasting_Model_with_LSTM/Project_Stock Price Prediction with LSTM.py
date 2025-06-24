# Project : Stock Price Prediction with Long Short-Term Memory (LSTM)
# This code is a part of a project that uses LSTM to predict stock prices.
# Data is fetched from Alpha Vantage API, and the model is trained using PyTorch.

# Libraries
import numpy as np
import pandas as pd
import requests

import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from sklearn.metrics import mean_squared_error
from datetime import timedelta

import matplotlib.pyplot as plt
from matplotlib.pyplot import figure
from sklearn.preprocessing import MinMaxScaler

# Define constants
URL = "https://www.alphavantage.co/query"
API_KEY = "YOUR_API_KEY"  # Replace with your own key
SYMBOL = "NVDA"
COMPANY_NAME = "NVIDIA Corporation"
INTERVAL = "60min"
OUTPUTSIZE = "full"

# Fetch data from Alpha Vantage
config = {
    "params": {
        "function": "TIME_SERIES_INTRADAY",
        "symbol": SYMBOL,
        "interval": INTERVAL,
        "outputsize": OUTPUTSIZE,
        "apikey": API_KEY
    },
    "data": {
        "window_size": 24,  # Number of time steps to look back
        "train_split_size": 0.8,  # Proportion of data to use for training
    },
    "plot":{
        "num_ticks": 12,  # Number of ticks on x-axis
        "figsize": (14, 6),
        "linewidth": 1,
        "color_actual": "#001f3f",
        "color_train": "#3D9970",
        "color_val": "#0074D9",
        "color_pred_train": "#3D9970",
        "color_pred_val": "#0074D9",
        "color_pred_test": "#FF4136",
    },
    "model": {
        "input_size": 1,  # Number of features in the input
        "num_layers": 2,  # Number of LSTM layers
        "lstm_size": 64, # Number of hidden units in LSTM
        "output_size": 1,  # Number of features in the output
        "dropout": 0.2,  # Dropout rate
    },
    "training": {
        "device": "cpu", # Device to use for training (cpu or cuda)
        "batch_size": 64,
        "num_epoch": 100,
        "learning_rate": 0.01,
        "scheduler_step_size": 40,
    }
}

def download_data(url, params):
    """
    Downloads and processes time series stock data from a specified API endpoint.
    Args:
        url (str): The API endpoint URL to fetch the stock data from.
        params (dict): A dictionary of query parameters to be sent with the API request.
    Returns:
        pandas.DataFrame: A DataFrame containing the processed time series data with columns:
            ['datetime', 'open', 'high', 'low', 'close', 'volume'].
    Raises:
        Exception: If the HTTP request fails or returns a non-200 status code.
        ValueError: If the expected time series data is not found in the API response.
    Notes:
        - The function expects the API response to contain a time series section keyed by the interval.
        - The function renames columns for clarity and converts all data to float type.
        - The 'datetime' column is converted to pandas datetime objects and sorted in ascending order.
    """
    response = requests.get(url, params=params)
    if response.status_code != 200:
        raise Exception(f"Error fetching data: {response.status_code} - {response.text}")
    data_json = response.json()

    # Parse time series data
    ts_key = f'Time Series ({INTERVAL})'
    if ts_key not in data_json:
        raise ValueError("Time series data not found. Check API key or symbol.")

    data = pd.DataFrame.from_dict(data_json[ts_key], orient='index')

    data.rename(columns={
        '1. open': 'open',
        '2. high': 'high',
        '3. low': 'low',
        '4. close': 'close',
        '5. volume': 'volume'
    }, inplace=True)

    # Convert index to datetime
    data.index = pd.to_datetime(data.index)
    data = data.sort_index()
    data = data.astype(float)
    data.reset_index(inplace=True)
    data.rename(columns={'index': 'datetime'}, inplace=True)

    return data

def create_sequences(data, window_size):
    """
    Create input sequences and corresponding targets for LSTM.
    Args:
        data (np.ndarray): 1D array of normalized data.
        window_size (int): Number of time steps to look back.
    Returns:
        tuple: (inputs, targets, unseen)
            inputs: shape (num_samples, window_size)
            targets: shape (num_samples,)
            unseen: shape (window_size,)
    """
    inputs = []
    targets = []
    for i in range(len(data) - window_size):
        inputs.append(data[i:i+window_size])
        targets.append(data[i+window_size])
    unseen = data[-window_size:]
    return np.array(inputs), np.array(targets), unseen

# Normalization function using Min-Max Scaler
class Normalizer():
    """
    A utility class for normalizing and inverse transforming data using MinMaxScaler.

    Methods
    -------
    fit_transform(x):
        Fits the MinMaxScaler to the input data and transforms it to a normalized range [0, 1].

    inverse_transform(x):
        Inversely transforms the normalized data back to the original scale using the fitted scaler.
    """
    def __init__(self):
        """
        Initializes the Normalizer with a MinMaxScaler set to scale features to the range [0, 1].
        """
        self.scaler = MinMaxScaler(feature_range=(0, 1))

    def fit_transform(self, x):
        """
        Fits the MinMaxScaler to the input data and transforms it to the normalized range [0, 1].

        Parameters
        ----------
        x : array-like
            The input data to be normalized.

        Returns
        -------
        normalized_x : ndarray
            The normalized data as a flattened NumPy array.
        """
        x = np.array(x).reshape(-1, 1)
        normalized_x = self.scaler.fit_transform(x).flatten()
        return normalized_x

    def inverse_transform(self, x):
        """
        Inversely transforms the normalized data back to the original scale using the fitted scaler.

        Parameters
        ----------
        x : array-like
            The normalized data to be inverse transformed.

        Returns
        -------
        original_x : ndarray
            The data transformed back to its original scale as a flattened NumPy array.
        """
        x = np.array(x).reshape(-1, 1)
        return self.scaler.inverse_transform(x).flatten()

class TimeSeriesDataset(Dataset):
    """
    A custom PyTorch Dataset for time series data, designed to prepare input and target sequences for models such as LSTM.
    Args:
        x (np.ndarray): Input features of shape [batch, time], where 'batch' is the number of samples and 'time' is the sequence length.
        y (np.ndarray): Target values corresponding to each input sequence.
    Attributes:
        x (np.ndarray): Input features with an added feature dimension, converted to float32.
        y (np.ndarray): Target values converted to float32.
    Methods:
        __len__(): Returns the number of samples in the dataset.
        __getitem__(idx): Retrieves the input and target pair at the specified index.
    Note:
        The input 'x' is automatically expanded to have a third dimension for features, making it compatible with models expecting input of shape [batch, time, features].
    """

    def __init__(self, x, y):
        x = np.expand_dims(x, 2)  # [batch, time, features]
        self.x = x.astype(np.float32)
        self.y = y.astype(np.float32)

    def __len__(self):
        return len(self.x)

    def __getitem__(self, idx):
        return self.x[idx], self.y[idx]    

def mean_absolute_percentage_error(y_true, y_pred):
    y_true, y_pred = np.array(y_true), np.array(y_pred)
    mask = y_true != 0  # avoid division by zero
    return np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100

# Model
class LSTMModel(nn.Module):
    """
    LSTMModel is a PyTorch neural network module for time series forecasting using Long Short-Term Memory (LSTM) layers.

    Architecture:
    - Input: [batch, time, features]
    - Linear layer to project input features to hidden size.
    - ReLU activation.
    - LSTM layers (stacked, configurable depth).
    - Dropout for regularization.
    - Final linear layer to produce output.

    Args:
        input_size (int): Number of input features per time step.
        hidden_layer_size (int): Number of hidden units in each LSTM layer.
        num_layers (int): Number of stacked LSTM layers.
        output_size (int): Number of output features.
        dropout (float): Dropout probability after LSTM.

    Methods:
        forward(x): Forward pass for input tensor x.
    """
    def __init__(self, input_size, hidden_layer_size, num_layers, output_size, dropout):
        super().__init__()
        self.linear_1 = nn.Linear(input_size, hidden_layer_size)
        self.relu = nn.ReLU()
        self.lstm = nn.LSTM(hidden_layer_size, hidden_layer_size, num_layers=num_layers, batch_first=True)
        self.dropout = nn.Dropout(dropout)
        self.linear_2 = nn.Linear(num_layers * hidden_layer_size, output_size)

        self.init_weights()

    def init_weights(self):
        for name, param in self.lstm.named_parameters():
            if 'bias' in name:
                nn.init.constant_(param, 0.0)
            elif 'weight_ih' in name:
                nn.init.kaiming_normal_(param)
            elif 'weight_hh' in name:
                nn.init.orthogonal_(param)

    def forward(self, x):
        batchsize = x.size(0)
        x = self.relu(self.linear_1(x))
        lstm_out, (h_n, _) = self.lstm(x)
        x = h_n.permute(1, 0, 2).reshape(batchsize, -1)
        x = self.dropout(x)
        return self.linear_2(x).squeeze()

# Training loop
def run_epoch(model, dataloader, optimizer, scheduler, criterion, is_training=False):
    epoch_loss = 0
    model.train() if is_training else model.eval()

    for x, y in dataloader:
        x = x.to(config["training"]["device"])
        y = y.to(config["training"]["device"])

        if is_training:
            optimizer.zero_grad()

        output = model(x)
        loss = criterion(output, y)

        if is_training:
            loss.backward()
            optimizer.step()

        epoch_loss += loss.item()

    if is_training:
        scheduler.step()

    avg_loss = epoch_loss / len(dataloader)
    return avg_loss

def predict_future(model, last_window, steps, scaler, device):
    model.train()
    # model.eval() # for smoothing

    predictions = []

    input_seq = last_window.reshape(1, -1, 1).astype(np.float32)  

    for _ in range(steps):
        inp = torch.tensor(input_seq).to(device)
        with torch.no_grad():
            pred = model(inp).cpu().numpy().flatten()[0]

        predictions.append(pred)

        # Append to sequence and slide window
        input_seq = np.append(input_seq[:, 1:, :], [[[pred]]], axis=1)

    # Inverse transform back to original scale
    return scaler.inverse_transform(np.array(predictions).reshape(-1, 1)).flatten()

# Download data
df = download_data(URL, config['params'])

# Display data info
start_date = df['datetime'].iloc[0].strftime('%Y-%m-%d %H:%M')
end_date = df['datetime'].iloc[-1].strftime('%Y-%m-%d %H:%M')
print(f"Number of data points: {len(df)} from {start_date} to {end_date}")

# Plotting
plt.figure(figsize=config['plot']['figsize'])
plt.plot(df['datetime'], df['close'], color=config['plot']['color_actual'], linewidth=1, label='Close Price')
plt.title(f'Hourly Close Price of {COMPANY_NAME}', fontsize=14)
plt.xlabel('Date', fontsize=12)
plt.ylabel('Price (USD)', fontsize=12)

# Improve x-ticks readability
num_ticks = config['plot']['num_ticks']
tick_indices = range(0, len(df), max(1, len(df) // num_ticks))
tick_labels = df['datetime'].dt.strftime('%Y-%m-%d %H:%M').iloc[tick_indices]

plt.xticks(ticks=df['datetime'].iloc[tick_indices], labels=tick_labels, rotation=45)
plt.grid(axis='y', linestyle='--', alpha=0.5)
plt.legend()
plt.tight_layout()
plt.show()

# Create lists for data processing
data_close_price = df['close'].to_list()
data_time = df['datetime'].to_list()
num_data_points = len(data_close_price)

# Normalize the close prices
scaler = Normalizer()
normalized_data_close_price = scaler.fit_transform(data_close_price)

# Create sequences for LSTM input
data_x, data_y, data_x_unseen = create_sequences(normalized_data_close_price, config["data"]["window_size"])

# Split dataset
split_index = int(data_y.shape[0]*config["data"]["train_split_size"])
data_x_train = data_x[:split_index]
data_x_val = data_x[split_index:]
data_y_train = data_y[:split_index]
data_y_val = data_y[split_index:]

# Initialize empty arrays for plotting
to_plot_data_y_train = np.full(num_data_points, np.nan)
to_plot_data_y_val = np.full(num_data_points, np.nan)

# Inverse transform
inv_y_train = scaler.inverse_transform(data_y_train.reshape(-1, 1)).flatten()
inv_y_val = scaler.inverse_transform(data_y_val.reshape(-1, 1)).flatten()

# Insert values into plotting arrays at correct positions
ws = config["data"]["window_size"]
to_plot_data_y_train[ws:split_index + ws] = inv_y_train
to_plot_data_y_val[split_index + ws:] = inv_y_val

# Plotting training vs validation
fig = plt.figure(figsize=(25, 5), dpi=80)
fig.patch.set_facecolor((1.0, 1.0, 1.0))

plt.plot(data_time, to_plot_data_y_train, label="Prices (train)", color=config["plot"]["color_train"])
plt.plot(data_time, to_plot_data_y_val, label="Prices (validation)", color=config["plot"]["color_val"])

# Fix xticks: only show limited number of ticks for readability
num_ticks = config["plot"]["num_ticks"]
tick_step = max(1, len(data_time) // num_ticks)
tick_indices = list(range(0, len(data_time), tick_step))
tick_labels = [data_time[i].strftime('%Y-%m-%d %H:%M') for i in tick_indices]

plt.xticks(ticks=[data_time[i] for i in tick_indices], labels=tick_labels, rotation=45)

plt.title(f"Daily Close Prices for {config['params']['symbol']} - Training vs Validation", fontsize=14)
plt.xlabel('Date', fontsize=12)
plt.ylabel('Price (USD)', fontsize=12)
plt.grid(axis='y', linestyle='--', alpha=0.5)
plt.legend()
plt.tight_layout()
plt.show()

# Prepare dataloaders
dataset_train = TimeSeriesDataset(data_x_train, data_y_train)
dataset_val = TimeSeriesDataset(data_x_val, data_y_val)

print("Train data shape:", dataset_train.x.shape, dataset_train.y.shape)
print("Validation data shape:", dataset_val.x.shape, dataset_val.y.shape)

train_dataloader = DataLoader(dataset_train, batch_size=config["training"]["batch_size"], shuffle=True)
val_dataloader = DataLoader(dataset_val, batch_size=config["training"]["batch_size"], shuffle=False)

# Initialize everything
model = LSTMModel(
    input_size=config["model"]["input_size"],
    hidden_layer_size=config["model"]["lstm_size"],
    num_layers=config["model"]["num_layers"],
    output_size=config["model"]["output_size"],
    dropout=config["model"]["dropout"]
).to(config["training"]["device"])

criterion = nn.MSELoss()
optimizer = optim.Adam(model.parameters(), lr=config["training"]["learning_rate"], betas=(0.9, 0.98), eps=1e-9)
scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=config["training"]["scheduler_step_size"], gamma=0.1)

# Train
for epoch in range(config["training"]["num_epoch"]):
    loss_train = run_epoch(model, train_dataloader, optimizer, scheduler, criterion, is_training=True)
    loss_val = run_epoch(model, val_dataloader, optimizer, scheduler, criterion, is_training=False)
    
    lr = scheduler.get_last_lr()[0]
    print(f"Epoch [{epoch+1}/{config['training']['num_epoch']}] | Train Loss: {loss_train:.6f}, Val Loss: {loss_val:.6f} | LR: {lr:.6f}")

# Re-init dataloaders without shuffle
train_dataloader = DataLoader(dataset_train, batch_size=config["training"]["batch_size"], shuffle=False)
val_dataloader = DataLoader(dataset_val, batch_size=config["training"]["batch_size"], shuffle=False)

model.eval()

# Predict validation
predicted_val = []
for x, _ in val_dataloader:
    x = x.to(config["training"]["device"])
    out = model(x).cpu().detach().numpy()
    predicted_val.extend(out)

# Convert to numpy arrays
predicted_val = np.array(predicted_val)

# Prepare plotting arrays
to_plot_pred_train = np.full(num_data_points, np.nan)
to_plot_pred_val = np.full(num_data_points, np.nan)

ws = config["data"]["window_size"]
inv_pred_val = scaler.inverse_transform(predicted_val.reshape(-1, 1)).flatten()

# Inverse transform the true values
true_train = scaler.inverse_transform(data_y_train.reshape(-1, 1)).flatten()
true_val = scaler.inverse_transform(data_y_val.reshape(-1, 1)).flatten()

# Calculate RMSE
rmse_val = np.sqrt(mean_squared_error(true_val, inv_pred_val))
mape_val = mean_absolute_percentage_error(true_val, inv_pred_val)

print(f"Validation RMSE: {rmse_val:.4f}")
print(f"Validation MAPE: {mape_val:.2f}%")

to_plot_pred_val[split_index + ws:] = inv_pred_val

# Final plot
fig = figure(figsize=(25, 5), dpi=80)
fig.patch.set_facecolor((1.0, 1.0, 1.0))
plt.plot(data_time, data_close_price, label="Actual prices", color=config["plot"]["color_actual"])
plt.plot(data_time, to_plot_pred_val, label="Predicted (val)", color=config["plot"]["color_pred_val"])

# Custom x-ticks
num_ticks = config["plot"]["num_ticks"]
tick_step = max(1, len(data_time) // num_ticks)
tick_indices = range(0, len(data_time), tick_step)
tick_labels = [data_time[i].strftime('%Y-%m-%d %H:%M') for i in tick_indices]
plt.xticks([data_time[i] for i in tick_indices], tick_labels, rotation=45)

plt.title(f"{SYMBOL} - Predicted vs Actual Close Prices", fontsize=14)
plt.xlabel("Date", fontsize=12)
plt.ylabel("Price (USD)", fontsize=12)
plt.grid(axis='y', linestyle='--', alpha=0.5)
plt.legend()
plt.tight_layout()
plt.show()

future_steps = 48  # hours
future_preds = predict_future(model, data_x_unseen, future_steps, scaler, config["training"]["device"])

# Start from last known datetime
last_datetime = data_time[-1]
future_dates = [last_datetime + timedelta(hours=i+1) for i in range(future_steps)]

# Plot
fig = plt.figure(figsize=(25, 5), dpi=80)
plt.plot(data_time, data_close_price, label="Historical Prices", color=config["plot"]["color_actual"])
plt.plot(future_dates, future_preds, label="Forecast (next 24h)", color=config["plot"]["color_pred_test"])

plt.title(f"{SYMBOL} - 24 Hour Price Forecast", fontsize=14)
plt.xlabel("Datetime", fontsize=12)
plt.ylabel("Price (USD)", fontsize=12)
plt.xticks(rotation=45)
plt.grid(axis='y', linestyle='--', alpha=0.5)
plt.legend()
plt.tight_layout()
plt.show()