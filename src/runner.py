import gymnasium as gym
import numpy as np
import os
from matplotlib import pyplot as plt
from parser import Parser
from sklearn.preprocessing import normalize
from datetime import datetime
import logging
import sl

#Constants
FILES_PATH = 'src/files'
RESULTS_PATH = 'src/results'
NUM_EXPERIMENTS = 10
MAX_EPISODES = 250
MAP_SIZE = 8
MAP_NAME = f'{MAP_SIZE}x{MAP_SIZE}'
SLIPPERY = False
ALPHA = 0.9
GAMMA = 1
ENVIRONMENT = gym.make('FrozenLake-v1', map_name=MAP_NAME, is_slippery=SLIPPERY)
SEED = 100


logging.basicConfig(format='[%(levelname)s] %(message)s')
logging.getLogger().setLevel(logging.INFO)


def get_human_input():
    file = os.path.abspath(f'{FILES_PATH}/opinions.txt')
    parser = Parser()
    
    return parser.parse(file)

def get_advice_matrix(human_input):
    # TODO: develop this properly
    pass

def fuseMatrices(matrix1, matrix2):
    # TODO: this is an untested sketch based on the previous version of the code. Kyanna plz finish this one.
    num_states = ENVIRONMENT.observation_space.n
    num_actions = ENVIRONMENT.action_space.n
    
    assert(matrix1.shape == matrix2.shape == (num_states, num_actions))
    
    fused_matrix = np.zeros((num_states, num_actions), dtype = "f, f, f, f")
    for state in range(num_states):
        for action in range(num_actions):
            opinion1 = [matrix1[state, action][slparam] for slparam in range(4)]
            opinion2 = [matrix2[state, action][slparam] for slparam in range(4)]
            
            fused_opinion = sl.beliefConstraintFusion(opinion1, opinion2)
            
            for slparam in range(4):
                fused_matrix[state, action][slparam] = fused_opinion[slparam]
    
    return fused_matrix

def update_policy(policy, ep_states, ep_actions, ep_probs, ep_returns):
    for t in range(0, len(ep_states)):
        state = ep_states[t]
        action = ep_actions[t]
        prob = ep_probs[t]
        action_return = ep_returns[t]

        phi = np.zeros([1, ENVIRONMENT.action_space.n])
        phi[0, action] = 1

        score = phi - prob
        policy[state, :] = policy[state, :] + ALPHA * action_return * score

    return policy

def calculate_return(rewards):
    # https://stackoverflow.com/questions/65233426/discount-reward-in-reinforce-deep-reinforcement-learning-algorithm
    ep_rewards = np.asarray(rewards)
    t_steps = np.arange(ep_rewards.size)
    ep_returns = ep_rewards * GAMMA**t_steps
    ep_returns = ep_returns[::-1].cumsum()[::-1] / GAMMA**t_steps
    return ep_returns.tolist()
    
def get_action_probabilities(state, policy):
    logits = np.zeros(ENVIRONMENT.action_space.n)
    for action in range(ENVIRONMENT.action_space.n):
        logit = np.exp(policy[state, action])
        logits[action] = logit
        
    return logits / np.sum(logits)

def discrete_policy_grad(initial_policy):
    policy = initial_policy

    total_reward, total_successes = [], 0
    for episode in range(MAX_EPISODES):
        state = ENVIRONMENT.reset(seed=SEED)[0]
        ep_states, ep_actions, ep_probs, ep_rewards, total_ep_rewards = [], [], [], [], 0
        terminated, truncated = False, False

        # gather trajectory
        while not terminated and not truncated:
            ep_states.append(state)         # add state to ep_states list
            
            action_probs = get_action_probabilities(state, policy) # pass state thru policy to get action_probs
            ep_probs.append(action_probs)   # add action probabilities to action_probs list
            
            action = np.random.choice(np.array([0, 1, 2, 3]), p=action_probs)   # choose an action
            ep_actions.append(action)       # add action to ep_actions list
            
            state, reward, terminated, truncated, __ = ENVIRONMENT.step(action) # take step in environment
            ep_rewards.append(reward)       # add reward to ep_rewards list
            
            total_ep_rewards += reward
            if reward == 1:
                total_successes += 1

        ep_returns = calculate_return(ep_rewards) # calculate episode return & add total episode reward to totalReward
        total_reward.append(sum(ep_rewards))

        # update policy
        policy = update_policy(policy, ep_states, ep_actions, ep_probs, ep_returns)

    ENVIRONMENT.close()

    # success rate
    success_rate = (total_successes / MAX_EPISODES) * 100

    return success_rate

def evaluate(initial_policy):
    success_rates = []
    for i in range(NUM_EXPERIMENTS):
        iteration = discrete_policy_grad(initial_policy)
        success_rates.append(iteration)
    return success_rates

def get_file_name():
    now = datetime.now()
    return f'{MAP_NAME}-e{MAX_EPISODES}-{now.strftime("%Y%m%d-%H%M%S")}'

def save_data(no_advice_success_rates, advice_success_rates):
    np.savetxt(f'{RESULTS_PATH}/{get_file_name()}-no-advice.csv', no_advice_success_rates, delimiter=",")
    np.savetxt(f'{RESULTS_PATH}/{get_file_name()}-advice.csv', advice_success_rates, delimiter=",")
    
def plot(no_advice_success_rates, advice_success_rates):
    plt.plot(no_advice_success_rates, label='No advice')
    plt.plot(advice_success_rates, label='Advice')
    plt.title(f'Training on a {MAP_NAME} map for {str(MAX_EPISODES)} episodes; is_slippery = {str(SLIPPERY)}.')
    plt.xlabel('Iteration')
    plt.ylabel('Success Rate %')
    plt.legend()
    
    plt.savefig(f'{RESULTS_PATH}/{get_file_name()}.pdf', format='pdf', bbox_inches='tight')
    plt.show()



'''''''''''''''''''''''''''''''''''''''''''''
Main
'''''''''''''''''''''''''''''''''''''''''''''
human_input = get_human_input()
assert human_input.map_size == MAP_SIZE
advice = get_advice_matrix(human_input)

# evaluate without advice
logging.info('running evaluation without advice')
initial_policy = np.zeros((ENVIRONMENT.observation_space.n, ENVIRONMENT.action_space.n))
no_advice_success_rates = evaluate(initial_policy)

# evaluate with advice
logging.info('running evaluation with advice')
initial_policy = np.loadtxt(f'{FILES_PATH}/human_advised_policy', delimiter=",")
advice_success_rates =  evaluate(initial_policy)

save_data(no_advice_success_rates, advice_success_rates)
plot(no_advice_success_rates, advice_success_rates)