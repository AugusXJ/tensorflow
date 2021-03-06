"""
15年版本DQN玩CartPole
"""

import gym
import tensorflow as tf
import numpy as np
import random
from collections import deque

ENV_NAME = 'CartPole-v0'
EPISODE = 10000  # Episode limitation
STEP = 300  # Step limitation in an episode
TEST = 10

GAMMA = 0.9  # discount factor for target Q
INITIAL_EPSILON = 0.5  # starting value of epsilon
FINAL_EPSILON = 0.01  # final value of epsilon
REPLAY_SIZE = 10000  # experience replay buffer size
BATCH_SIZE = 32  # size of minibatch


class DQN:
    # DQN agent
    def __init__(self, env):
        # init experience replay
        self.replay_buffer = deque()
        # init some parameters
        self.time_step = 0
        self.epsilon = INITIAL_EPSILON
        self.state_dim = env.observation_space.shape[0]
        self.action_dim = env.action_space.n
        self.state_input = tf.placeholder("float", [None, self.state_dim])      # 输入空间
        self.action_input = tf.placeholder("float", [None, self.action_dim])  # 动作空间
        # Q网络参数
        self.w1 = self.weight_variable([self.state_dim, 20])
        self.b1 = self.bias_variable([20])
        self.w2 = self.weight_variable([20, self.action_dim])
        self.b2 = self.bias_variable([self.action_dim])
        # target网络参数
        self.t_w1 = self.w1
        self.t_b1 = self.b1
        self.t_w2 = self.w2
        self.t_b2 = self.b2
        self.Q_value = self.create_q_network()                                  # 神经网络计算的Q值
        self.target_value = self.create_target_network()                        # target 网络
        self.y_input = tf.placeholder("float", [None])                          # targetQ值
        self.optimizer = self.create_training_method()                          # 训练启动器
        # Init session
        self.session = tf.InteractiveSession()
        self.session.run(tf.global_variables_initializer())

    def create_q_network(self):
        # network weights
        self.w1 = self.weight_variable([self.state_dim, 20])
        self.b1 = self.bias_variable([20])
        self.w2 = self.weight_variable([20, self.action_dim])
        self.b2 = self.bias_variable([self.action_dim])
        # hidden layers
        h_layer = tf.nn.relu(tf.matmul(self.state_input, self.w1) + self.b1)
        # Q Value layer
        return tf.matmul(h_layer, self.w2) + self.b2

    def create_target_network(self):
        # hidden layers
        h_layer = tf.nn.relu(tf.matmul(self.state_input, self.t_w1) + self.t_b1)
        # Q Value layer
        return tf.matmul(h_layer, self.t_w2) + self.t_b2

    @staticmethod
    def weight_variable(shape):
        initial = tf.truncated_normal(shape)
        return tf.Variable(initial)

    @staticmethod
    def bias_variable(shape):
        initial = tf.constant(0.01, shape=shape)
        return tf.Variable(initial)

    def create_training_method(self):
        q_action = tf.reduce_sum(tf.multiply(self.Q_value, self.action_input), reduction_indices=1)
        cost = tf.reduce_mean(tf.square(self.y_input - q_action))
        return tf.train.AdamOptimizer(0.0001).minimize(cost)

    def perceive(self, state, action, reward, next_state, done):
        """
        存储信息
        :param state: 
        :param action: 
        :param reward: 
        :param next_state: 
        :param done: 
        :return: 
        """
        one_hot_action = np.zeros(self.action_dim)
        one_hot_action[action] = 1
        self.replay_buffer.append((state, one_hot_action, reward, next_state, done))
        if len(self.replay_buffer) > REPLAY_SIZE:
            self.replay_buffer.popleft()

        if len(self.replay_buffer) > BATCH_SIZE:
            self.train_q_network()

    def renew_target_network(self):
        self.t_w1 = self.w1
        self.t_b1 = self.b1
        self.t_w2 = self.w2
        self.t_b2 = self.b2

    def train_q_network(self):
        self.time_step += 1
        # Step 1: obtain random minibatch from replay memory
        minibatch = random.sample(self.replay_buffer, BATCH_SIZE)
        state_batch = [data[0] for data in minibatch]
        action_batch = [data[1] for data in minibatch]
        reward_batch = [data[2] for data in minibatch]
        next_state_batch = [data[3] for data in minibatch]

        # Step 2: calculate y
        y_batch = []
        q_value_batch = self.Q_value.eval(feed_dict={self.state_input: next_state_batch})
        for i in range(0, BATCH_SIZE):
            done = minibatch[i][4]
            if done:
                y_batch.append(reward_batch[i])
            else:
                y_batch.append(reward_batch[i] + GAMMA * np.max(q_value_batch[i]))

        self.optimizer.run(feed_dict={
            self.y_input: y_batch,
            self.action_input: action_batch,
            self.state_input: state_batch
        })

        # 更新target网络
        if self.time_step % 2 == 0:
            self.renew_target_network()

    def egreedy_action(self, state):
        q_value = self.Q_value.eval(feed_dict={
            self.state_input: [state]
        })[0]
        if random.random() <= self.epsilon:
            return random.randint(0, self.action_dim - 1)
        else:
            return np.argmax(q_value)
        # self.epsilon -= (INITIAL_EPSILON - FINAL_EPSILON) / 10000

    def action(self, state):
        return np.argmax(self.Q_value.eval(feed_dict={
            self.state_input: [state]
        })[0])


def main():
    # initialize OpenAI Gym env and dqn agent
    env = gym.make(ENV_NAME)
    agent = DQN(env)

    for episode in range(EPISODE):
        # initialize task
        state = env.reset()
        # Train
        for step in range(STEP):
            action = agent.egreedy_action(state)  # e-greedy action for train
            next_state, reward, done, _ = env.step(action)
            # Define reward for agent
            reward_agent = -1 if done else 0.1
            agent.perceive(state, action, reward, next_state, done)
            state = next_state
            if done:
                break
        # Test every 100 episodes
        if episode % 100 == 0:
            total_reward = 0
            for i in range(TEST):
                state = env.reset()
                for j in range(STEP):
                    env.render()
                    action = agent.action(state)  # direct action for test
                    state, reward, done, _ = env.step(action)
                    total_reward += reward
                    if done:
                        break
                ave_reward = total_reward / TEST
            print('episode: ', episode, 'Evaluation Average Reward:', ave_reward)
            if ave_reward >= 200:
                break
if __name__ == '__main__':
    main()