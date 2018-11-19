import numpy as np
import math
import pandas as pd
import matplotlib.pyplot as plt
import tensorflow as tf
import csv

# Global variables
class glb:
    seed = 1234
    df = None       # dataframe
    n_feat = None   # number of features
    n_node = None   # number of neurals in each hidden layer
    n_hidden = None # number of hidden layers
    n_epoch = None  # number of training epochs
    id_2018 = None  # sampleID of the 1st row of 2018's matches in the dataset.
    init_b = None   # initial value of bias
    r_l = None      # learning rate
    X_train = None  # Training inputs
    X_test = None   # Testing inputs
    Y_train = None  # Training outputs
    Y_test = None   # Testing outputs

# Initialization of global variables.
# Input:
#   - @n_feat: int
#        Number of features
#   - @n_node: int
#        Number of neurons in a hidden layer
#   - @n_hidden: int
#        Number of hidden layers
#   - @n_epoch: int
#        Number of epochs
#   - @id_2018: int
#        sampleID of the 1st row of 2018's matches in the dataset.
#   - @init_b: float, default 1.0
#        Initial value of biases
#   - @r_l: float, default 0.1
#        Learning rate
#   - @random: boolean, default False
#        Flag for whether to randomize the rows.
#   - @filename: str, default 'feature.csv'
#        Name of the file that contains the dataset
#
# Output:
#   - N/A
def init(n_feat, n_node, n_hidden, n_epoch, id_2018,
         init_b=1.0, r_l=0.1, random=False, filename='feature.csv'):
    # NP settings: print 250 chars/line; no summarization; always print floats
    np.set_printoptions(linewidth=250, threshold=np.nan, suppress=True)
    df = pd.read_csv(filename, header=0, sep=',', index_col=0)
    # Randomize rows
    if(random):
        df = df.sample(frac=1, random_state=glb.seed)
        df = df.reset_index(drop = True)
    glb.n_feat = n_feat
    glb.n_node = n_node
    glb.n_hidden = n_hidden
    glb.n_epoch = n_epoch
    glb.id_2018 = id_2018
    glb.init_b = init_b
    glb.r_l = r_l
    # Normalize features
    for i in range(n_feat):
        df.iloc[:, i] = ((df.iloc[:, i] - df.iloc[:, i].mean())
                          /df.iloc[:, i].std())
    glb.df = df
    # Split data
    X = glb.df.iloc[:, 0:glb.n_feat].values
    Y = glb.df.iloc[:, glb.n_feat:].values
    glb.X_train = X[0:glb.id_2018,]
    glb.X_test = X[glb.id_2018:,]
    glb.Y_train = Y[0:glb.id_2018,]
    glb.Y_test = Y[glb.id_2018:,]

# Create a new model through training with data from 2011~2017
# Input:
#   - @model_name: str
#        Prefix of the name of the model's files to be saved in
#          './mlp/checkpoints' and './mlp/checkpoints/'.
# Output:
#   - Tensorflow files saved under './mlp/checkpoints'.
def new_model(model_name):
    # input and output layers placeholders
    X = tf.placeholder(tf.float32, [None, glb.n_feat], name='X')
    Y = tf.placeholder(tf.float32, [None, 1], name='Y')

    # Weights, biases, and output function
    W = {}
    b = {}
    y = {}

    # Hidden layers construction
    for i in range(glb.n_hidden):
        # hidden Layer 1: # of inputs (aka # of rows) has to be # of features
        if i == 0:
            n_in = glb.n_feat
        else:
            n_in = glb.n_node

        layer = 'h' + str(i+1)
        W[layer] = tf.get_variable('W'+str(i+1), shape=[n_in, glb.n_node],
                                   initializer=(tf.contrib.layers
                                                .xavier_initializer(
                                                   seed=glb.seed)))
        b[layer] = tf.get_variable('b'+str(i+1),
                                    initializer=(tf.zeros([1, glb.n_node])
                                                 + glb.init_b))

        # Hidden layer 1: Input is X
        if i == 0:
            y[layer] = tf.nn.sigmoid(tf.matmul(X, W[layer]) + b[layer])
        # Other hidden layers: connect from its previous layer y[layer-1]
        else:
            prev_layer = 'h'+str(i)
            y[layer] = tf.nn.sigmoid(tf.matmul(y[prev_layer], W[layer])
                                     + b[layer])

    # Output layer construction
    W['out'] = tf.get_variable('Wout', shape=[glb.n_node, 1],
                               initializer=tf.contrib.layers
                                           .xavier_initializer(seed=glb.seed))
    b['out'] = tf.get_variable('bout', initializer=(tf.zeros([1, 1])
                                                    + glb.init_b))
    y['out'] = tf.nn.sigmoid(tf.matmul(y['h'+str(len(y)-1)], W['out'])
                             + b['out'])

    # Loss function: binary cross entropy with 1e-30 to avoid log(0)
    cross_entropy = -tf.reduce_sum(Y * tf.log(y['out']+1e-30)
                                   + (1-Y) * tf.log(1-y['out']+1e-30),
                                   reduction_indices=[1])
    # Back-propagation
    train_step = (tf.train.GradientDescentOptimizer(glb.r_l)
                  .minimize(cross_entropy))
    init = tf.global_variables_initializer()

    # Get training and testing accuracy
    def get_acc():
        # Compute training accuracy
        Y_pred_tr = sess.run(y['out'], feed_dict={X: glb.X_train})
        acc_tr = tf.reduce_mean(tf.cast(tf.equal(tf.round(Y_pred_tr),
                                                 glb.Y_train), tf.float32))
        # Compute testing accuracy
        Y_pred_ts = sess.run(y['out'], feed_dict={X: glb.X_test})
        acc_ts = tf.reduce_mean(tf.cast(tf.equal(tf.round(Y_pred_ts),
                                                 glb.Y_test), tf.float32))
        return sess.run(acc_tr), sess.run(acc_ts)

    saver = tf.train.Saver()

    # './mlp/datapoints/[model_name]_[n_hidden]_[n_node].csv'
    fmt = '_'.join(['./mlp/datapoints/' + model_name,
                    str(glb.n_hidden), str(glb.n_node) + '.csv'])

    with tf.Session() as sess, open(fmt, 'a') as f:
        sess.run(init)
        writer = csv.writer(f)
        writer.writerow(get_pts_csv_header())

        for epoch in range(glb.n_epoch):
            acc_tr, acc_ts = get_acc()

            line = [epoch]  # Line to be written
            # For every hidden layer
            for i in range(glb.n_hidden):
                layer = 'h' + str(i+1)
                line += sess.run(W[layer]).flatten().tolist()
                line += sess.run(b[layer]).flatten().tolist()
            # Add final layer
            line += sess.run(W['out']).flatten().tolist()
            line += sess.run(b['out']).flatten().tolist()
            # Add accuracy, too
            line += [acc_tr, acc_ts]
            writer.writerow(line)

            print('Epoch', epoch)
            print("Accuracy:\nTraining:\t{}\nTesting:\t{}\n".format(acc_tr,
                                                                    acc_ts))
            # for every sample
            for i in range(glb.X_train.shape[0]):
                sess.run(train_step, feed_dict={X: glb.X_train[i, None],
                                                Y: glb.Y_train[i, None]})
            if epoch % 100 == 0:
                saver.save(sess, "./mlp/checkpoints/"+model_name,
                           global_step = epoch)
                print('Session saved.\n')

        print('Epoch', glb.n_epoch)
        print("Accuracy:\nTraining:\t{}\nTesting:\t{}".format(*get_acc()))
        print()

# Load from the lastest model from './mlp/checkpoints/ and continue training'
# Input:
#   - @model_name: str
#        Prefix of the name of the model's file to be saved in
#          './mlp/checkpoints'.
#   - @meta_name: str
#        Prefix of the '.meta' file to be loaded.
#        E.X.: 'model-100' if the '.meta' file is named 'model-100.meta'
#   - @epoch_start: int
#        Start epoch; pretty much the end epoch of the model to be loaded, so
#          'epoch_start' should be 300 if the model to be loaded was saved at
#          epoch 300 unless user intended to do other testing.
#   - @model_path: str, default './mlp/checkpoints/'
#        Path to the checkpoint directory.
# Output:
#   - Tensorflow files saved under './mlp/checkpoints'.
def continue_model(model_name, meta_name,
                   epoch_start, model_path='./mlp/checkpoints/'):
    # Weights, biases, and output function
    W = {}
    b = {}
    y = {}

    # Get training and testing accuracy
    def get_acc():
        # Compute training accuracy
        Y_pred_tr = sess.run(y['out'], feed_dict={X: glb.X_train})
        acc_tr = tf.reduce_mean(tf.cast(tf.equal(tf.round(Y_pred_tr),
                                                 glb.Y_train), tf.float32))
        # Compute testing accuracy
        Y_pred_ts = sess.run(y['out'], feed_dict={X: glb.X_test})
        acc_ts = tf.reduce_mean(tf.cast(tf.equal(tf.round(Y_pred_ts),
                                                 glb.Y_test), tf.float32))
        return sess.run(acc_tr), sess.run(acc_ts)

    with tf.Session() as sess:
        saver = tf.train.import_meta_graph(model_path + meta_name + '.meta')
        saver.restore(sess, tf.train.latest_checkpoint(model_path))
        graph = tf.get_default_graph()

        # input and output layers placeholders
        X = graph.get_tensor_by_name('X:0')
        Y = graph.get_tensor_by_name('Y:0')

        # Hidden layers construction
        for i in range(glb.n_hidden):
            layer = 'h' + str(i+1)
            W[layer] = graph.get_tensor_by_name('W' + str(i+1) + ':0')
            b[layer] = graph.get_tensor_by_name('b' + str(i+1) + ':0')

            # Hidden layer 1: Input is X
            if i == 0:
                y[layer] = tf.nn.sigmoid(tf.matmul(X, W[layer]) + b[layer])
            # Other hidden layers: connect from its previous layer y[layer-1]
            else:
                prev_layer = 'h'+str(i)
                y[layer] = tf.nn.sigmoid(tf.matmul(y[prev_layer], W[layer])
                                         + b[layer])

        # Output layer construction
        W['out'] = graph.get_tensor_by_name('Wout:0')
        b['out'] = graph.get_tensor_by_name('bout:0')
        y['out'] = tf.nn.sigmoid(tf.matmul(y['h'+str(len(y)-1)], W['out'])
                              + b['out'])

        # Loss function: binary cross entropy with 1e-30 to avoid log(0)
        cross_entropy = -tf.reduce_sum(Y * tf.log(y['out']+1e-30)
                                       + (1-Y) * tf.log(1-y['out']+1e-30),
                                       reduction_indices=[1])
        # Back-propagation
        train_step = (tf.train.GradientDescentOptimizer(glb.r_l)
                      .minimize(cross_entropy))

        for epoch in range(epoch_start, glb.n_epoch):
            print('Epoch', epoch)
            print("Accuracy:\nTraining:\t{}\nTesting:\t{}".format(*get_acc()))
            print()
            # for every sample
            for i in range(glb.X_train.shape[0]):
                sess.run(train_step, feed_dict={X: glb.X_train[i, None],
                                                Y: glb.Y_train[i, None]})
            if epoch % 100 == 0:
                saver.save(sess, "./mlp/checkpoints/"+model_name,
                           global_step = epoch)
                print('Session saved.\n')

        print('Epoch', glb.n_epoch)
        print("Accuracy:\nTraining:\t{}\nTesting:\t{}".format(*get_acc()))
        print()


# Create a header consists of each weight for './mlp/datapoints/*.csv' files
#   with the following format:
#   - Weights: 'W[layer #]_[destination neuron #]_[origin neuron #]'
#   - Bias: 'b[layer #]_[neuron #]
# Example:
#   epoch W1_1_1 W1_2_1 W1_3_1 ... training_acc testing_acc
# Output:
#   - a list with column names of the weights
def get_pts_csv_header():
    # The algorithm might look hedious, and there really isn't an easy way to
    #   explain it soley with comments, but running this snippet line by line
    #   will make it quite obvious.
    csv_header = ['epoch']
    # Get names for weights in each hidden layers
    for i in range(glb.n_hidden):
        # first hidden layer, # of input is # of features
        if i == 0:
            n_in = glb.n_feat
        else:
            n_in = glb.n_node
        n_out = glb.n_node
        # Prefix, i.e., 'W1_' for hidden layer 1, 'W2_' for hidden layer 2, etc
        pfix = ['W' + str(i+1) + '_'] * (n_in*n_out)
        # Column indice in the matrix, i.e., '1_' for column 1
        c = [str(i+1) + '_' for i in range(n_out)] * n_in
        # Row indice in the matrix, i.e., '1_' for row 1
        r = [[str(i+1)] * n_out for i in range(n_in)]
        r = [i for l in r for i in l]   # to flatten the list
        # Combine prefixes and column & row indice together.
        csv_header += [a+b+c for a,b,c in zip(pfix,c,r)]
        # Add biases to the list
        csv_header += ['b' + str(i+1) + '_' + str(j+1) for j in range(n_out)]

    # Add the names for the final layer
    csv_header += ['W' + str(glb.n_hidden + 1) + '_1_'
                    + str(i+1) for i in range(glb.n_node)]
    csv_header += ['b' + str(glb.n_hidden + 1) + '_1']
    csv_header += ['training_acc', 'testing_acc']
    return csv_header


############################## Testing functions ##############################

# Test 'new_model()' using generated data 'fake_feature/feature.csv'.
def test_new_model():
    # MUST RUN FROM TOP DIRECTORY, I.E. YOU'RE RUNNING THIS SCRIPT USING PATH
    #   './mlp/mlp.py'.
    try:
        init(10, 10, 2, 100, 9001, filename='./mlp/fake_feature/feature.csv')
    except Exception as e:
        print(e)
        msg = (
            "\u001b[31mPlease check if you are running the script from the "
            "top directory, i.e., make sure you are running using the path"
            "'./mlp/mlp.py'. \u001b[0m")
        print(msg)
        exit(0)
    new_model('fake_model')

# Assuming 'test_gen()' is invoked beforehand and one single session is saved.
def test_continue_model():
    init(10, 10, 2, 100, 9001, filename='./mlp/fake_feature/feature.csv')
    load_model('fake_model', 'fake_model-0', 1)