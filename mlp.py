#!/usr/bin/env python

import tensorflow as tf
import numpy as np

import open_snp_data
import os

import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns


LOG_DIR = "./logdir-mlp"

train, test = open_snp_data.load_data("opensnp_data_gwas_subset/", small=False, include_metadata=True)

input_dims = len(train.snps[0])

learning_rate = 0.001
training_epochs = 1
batch_size = 100
display_step = 1
checkpoint_step = 5
DETAILED_VISUALIZATION = True

n_hidden_1 = 1000
n_hidden_2 = 1000

n_input = input_dims

x = tf.placeholder("float", [None, n_input])
y = tf.placeholder("float", [None])

# Create model
def multilayer_perceptron(x, weights, biases):
    # Hidden layer with RELU activation
    layer_1 = tf.add(tf.matmul(x, weights['h1']), biases['b1'])
    #layer_1 = tf.nn.relu(layer_1)
    layer_1 = tf.nn.tanh(layer_1)
    if DETAILED_VISUALIZATION:
        # Create a summary to visualize the first layer ReLU activation
        #tf.histogram_summary("relu1", layer_1)
        tf.histogram_summary("tanh1", layer_1)
    # Hidden layer with RELU activation
    layer_2 = tf.add(tf.matmul(layer_1, weights['h2']), biases['b2'])
    #layer_2 = tf.nn.relu(layer_2)
    layer_2 = tf.nn.tanh(layer_2)
    if DETAILED_VISUALIZATION:
        # Create another summary to visualize the second layer ReLU activation
        #tf.histogram_summary("relu2", layer_2)
        tf.histogram_summary("tanh2", layer_2)
    # Output layer with linear activation
    out_layer = tf.matmul(layer_2, weights['out']) + biases['out']
    return out_layer

# Store layers weight & bias
# with tf.device("/cpu:0"):
weights = {
	'h1': tf.Variable(tf.random_normal([n_input, n_hidden_1])),
	'h2': tf.Variable(tf.random_normal([n_hidden_1, n_hidden_2])),
	'out': tf.Variable(tf.random_normal([n_hidden_2, 1]))
}
biases = {
	'b1': tf.Variable(tf.random_normal([n_hidden_1])),
	'b2': tf.Variable(tf.random_normal([n_hidden_2])),
	'out': tf.Variable(tf.random_normal([1]))
}

with tf.name_scope("Model"):
		pred = multilayer_perceptron(x, weights, biases)

with tf.name_scope("Loss"):
		cost = tf.reduce_sum(tf.pow(pred-y, 2))/(2*batch_size)

with tf.name_scope("AdamOptimizer"):
        optimizer = tf.train.AdamOptimizer(learning_rate=learning_rate).minimize(cost)
        if DETAILED_VISUALIZATION:
            grads = tf.gradients(cost, tf.trainable_variables())
            grads = list(zip(grads, tf.trainable_variables()))

# Create a summary to monitor cost tensor
tf.scalar_summary("loss", cost)

if DETAILED_VISUALIZATION:
    # Create summaries to visualize weights
    for var in tf.trainable_variables():
        tf.histogram_summary(var.name, var)
    # Summarize all gradients
    for grad, var in grads:
        tf.histogram_summary(var.name + '/gradient', grad)

# Merge all summaries into a single op
merged_summary_op = tf.merge_all_summaries()

saver = tf.train.Saver()

# Launch the graph
sess = tf.Session()
ckpt = tf.train.get_checkpoint_state('checkpoints/')
if ckpt and ckpt.model_checkpoint_path:
    # if checkpoint exists, restore the parameters and set epoch_n and i_iter
    saver.restore(sess, ckpt.model_checkpoint_path)
    epoch_n = int(ckpt.model_checkpoint_path.split('-')[1])
    i_iter = (epoch_n+1) * (train.num_examples/batch_size)
    print "Restored Epoch ", epoch_n
else:
    # no checkpoint exists. create checkpoints directory if it does not exist.
    if not os.path.exists('checkpoints'):
        os.makedirs('checkpoints')
    epoch_n = 0
    init = tf.initialize_all_variables()
    sess.run(init)
summary_writer = tf.train.SummaryWriter(LOG_DIR, tf.get_default_graph())
# Training cycle
for epoch in range(epoch_n + 1, training_epochs):
    avg_cost = 0.
    total_batch = int(train.num_examples/batch_size)
    # Loop over all batches
    for i in range(total_batch):
        batch_x, batch_y = train.next_batch(batch_size)
        # Run optimization op (backprop) and cost op (to get loss value)
        _, c, summary = sess.run(	[optimizer, cost, merged_summary_op],
									feed_dict={x: batch_x, y: batch_y}
								)
        summary_writer.add_summary(summary, epoch * total_batch + i)
        # Compute average loss
        avg_cost += c / total_batch
    # Display logs per epoch step
    if epoch % display_step == 0:
        print "Epoch:", '%04d' % (epoch+1), "cost=", \
            "{:.9f}".format(avg_cost)
    if epoch % checkpoint_step == 0:
        print "Saving checkpoint...."
        saver.save(sess, 'checkpoints/model.ckpt', epoch)
print "Optimization Finished!"
#Predicting heights
M_PREDS = []
M_TRUE = []
F_PREDS = []
F_TRUE = []
total_batch = int(test.num_examples/batch_size)
print "TOTAL_BATCH : ", total_batch
for i in range(total_batch):
    batch_xs, batch_ys = test.next_batch(batch_size)
    _predictions = sess.run([pred], feed_dict={x: batch_xs, y: batch_ys})
    _predictions = _predictions[0]
    for predictions in _predictions:
        print "i", i
        print "Predictions : ", predictions
        print "prediction shape : ", predictions.shape
        gender = batch_xs[0:, 1]
        y_pred = predictions.tolist()
        y_true = batch_ys.tolist()
        for _idx, _female in enumerate(gender):
            if _female == True:
                F_PREDS.append(y_pred[_idx])
                F_TRUE.append(y_true[_idx])
            else:
                M_PREDS.append(y_pred[_idx])
                M_TRUE.append(y_true[_idx])

total_batch = int(train.num_examples/batch_size)
print "TOTAL_BATCH : ", total_batch
for i in range(total_batch):
    batch_xs, batch_ys = train.next_batch(batch_size)
    _predictions = sess.run([pred], feed_dict={x: batch_xs, y: batch_ys})
    _predictions = _predictions[0]
    for predictions in _predictions:
        print "i", i
        print "Predictions : ", predictions
        print "prediction shape : ", predictions.shape
        gender = batch_xs[0:, 1]
        y_pred = predictions.tolist()
        y_true = batch_ys.tolist()

        for _idx, _female in enumerate(gender):
            if _female == True:
                F_PREDS.append(y_pred[_idx])
                F_TRUE.append(y_true[_idx])
            else:
                M_PREDS.append(y_pred[_idx])
                M_TRUE.append(y_true[_idx])
    print len(M_PREDS)
plt.clf()
plt.scatter(M_TRUE, M_PREDS, color='b')
plt.scatter(F_TRUE, F_PREDS, color='r')

np.save("M_PREDS.npy", M_PREDS)
np.save("M_TRUE.npy", M_TRUE)
np.save("F_PREDS.npy", F_PREDS)
np.save("F_TRUE.npy", F_TRUE)


plt.xlabel("Actual Heights")
plt.ylabel("Predicted Heights")
plt.savefig(LOG_DIR+"/mlp-scatter-"+str(n_hidden_1)+"-"+str(n_hidden_2)+"_e"+str(training_epochs)+".png")
