import pandas as pd
import urllib3
import sklearn
import numpy as np
from sklearn.preprocessing import MinMaxScaler


def E1_E2():
    http = urllib3.PoolManager()
    request = http.request('GET', 'justinshenk.com/share/E1_E2.csv')
    
    with open("E1_E2.csv", 'wb') as data_file:
        data_file.write(request.data)
    
    trjs = pd.read_csv("E1_E2.csv")
    trjs.dropna(subset=['x','y'],inplace=True)
    
    E1_trjs = trjs.loc[trjs['ID'] == 'E1']
    E2_trjs = trjs.loc[trjs['ID'] == 'E2']
    
    axes = ['x', 'y', 'hour', 'day', 'ID']
    
    output_axes = ['x', 'y']
    
    truncate = True
    
    if truncate:
        end_sample = 140000
        E1_trjs = E1_trjs[0:end_sample]
        E2_trjs = E2_trjs[0:end_sample]
    
    
    num_data = len(E1_trjs) + len(E2_trjs)
    
    train_split = 0.9
    
    num_train = int(train_split * num_data)
    
    num_test = num_data - num_train
    
    test_sequence_length = int(num_test / 4)
    start_first_test_sequence = 30000
    
    shift_seconds = 10 #60
    shift_steps = int(shift_seconds / 10)
    
    data_frames = [E1_trjs, E2_trjs]
    
    test_dfs_x = list()
    train_dfs_x = list()
    
    test_dfs_y = list()
    train_dfs_y = list()
    
    for df in data_frames:
    
        # We will also replace the mouse names with numbers, so we can compare multiple patterns in the network.
        df_targets = df[axes].shift(-shift_steps)
        #df_targets = df[axes]
    
        x_data = df[axes][0:-shift_steps].replace(['E1', 'E2'], [0, 1])
        y_data = df_targets[axes][0:-shift_steps].replace(['E1', 'E2'], [0, 1])
    
        #x_data = df[axes].replace(['E1', 'E2'], [0, 1])
        #y_data = df_targets[axes].replace(['E1', 'E2'], [0, 1])
    
        first_test_df_x = x_data[start_first_test_sequence:test_sequence_length]
        first_test_df_y = y_data[start_first_test_sequence:test_sequence_length]
    
        x_data = x_data.drop(x_data.index[start_first_test_sequence:test_sequence_length])
        y_data = y_data.drop(y_data.index[start_first_test_sequence:test_sequence_length])
    
        test_dfs_x.append(first_test_df_x.append(x_data[-test_sequence_length:]))
        test_dfs_y.append(first_test_df_y.append(y_data[-test_sequence_length:]))
    
        train_dfs_x.append(x_data[0:-test_sequence_length])
        train_dfs_y.append(y_data[0:-test_sequence_length])
    
    x_train = pd.concat(train_dfs_x)
    y_train = pd.concat(train_dfs_y)
    
    x_test = pd.concat(test_dfs_x)
    y_test = pd.concat(test_dfs_y)
    
    # Remove unnecessary axes
    y_train = y_train[output_axes]
    y_test = y_test[output_axes]
    
    
    x_scaler = MinMaxScaler()
    
    x_train_scaled = x_scaler.fit_transform(x_train)
    x_test_scaled = x_scaler.transform(x_test)
    
    y_scaler = MinMaxScaler()
    y_train_scaled = y_scaler.fit_transform(y_train)
    y_test_scaled = y_scaler.transform(y_test)
    
    num_x_signals = len(axes)
    num_y_signals = len(output_axes)
    
    def batch_generator(batch_size, sequence_length):
        """
        Generator function for creating random batches of training-data.
        """
    
        # Infinite loop.
        while True:
            # Allocate a new array for the batch of input-signals.
            x_shape = (batch_size, sequence_length, num_x_signals)
            x_batch = np.zeros(shape=x_shape, dtype=np.float16)
    
            # Allocate a new array for the batch of output-signals.
            y_shape = (batch_size, sequence_length, num_y_signals)
            y_batch = np.zeros(shape=y_shape, dtype=np.float16)
    
            # Fill the batch with random sequences of data.
            for i in range(batch_size):
                # Get a random start-index.
                # This points somewhere into the training-data.
                idx = np.random.randint(num_train - sequence_length)
    
                # Copy the sequences of data starting at this index.
                x_batch[i] = x_train_scaled[idx:idx+sequence_length]
                y_batch[i] = y_train_scaled[idx:idx+sequence_length]
    
            yield (x_batch, y_batch)
    
    sequence_length = 6 * 10 # 10 minutes
    sequence_length
    
    batch_size = 256
    
    generator = batch_generator(batch_size=batch_size,
                                sequence_length=sequence_length)

    return (generator, (x_train, x_test, y_train, y_test))
