from environment import VisualBananaEnvironment, BananaEnvironment
from agent import DQNAgent, DDQNAgent, DQNAgentPER, DDQNAgentPER
from neural_net import MlpQNetwork, ConvQNetwork
from dqn import DQN
import argparse
import random
import matplotlib.pyplot as plt
import torch
import datetime
import numpy as np
import matplotlib as mpl
mpl.use('TkAgg')  # Mac OS specific


def train(**kwargs):
    kwargs['worker_id'] = 0
    if kwargs['env_type'] == 'visual':
        env = VisualBananaEnvironment(file_name=kwargs['env_file'], num_stacked_frames=kwargs['num_stacked_frames'], worker_id=kwargs['worker_id'])
    elif kwargs['env_type'] == 'simple':
        env = BananaEnvironment(file_name=kwargs['env_file'], worker_id=kwargs['worker_id'])
    else:
        raise KeyError('unknown env type')
    state_dim = env.get_state_dim()
    action_dim = env.get_action_dim()

    kwargs['device'] = "cuda:0" if torch.cuda.is_available() and kwargs['use_gpu'] else "cpu"
    torch.manual_seed(0)
    torch.cuda.manual_seed_all(0)
    random.seed(0)
    np.random.seed(0)
    if kwargs['env_type'] == 'visual':
        net = ConvQNetwork(state_dim, action_dim).to(kwargs['device'])
        target_net = ConvQNetwork(state_dim, action_dim).to(kwargs['device'])
    elif kwargs['env_type'] == 'simple':
        net = MlpQNetwork(state_dim, action_dim).to(kwargs['device'])
        target_net = MlpQNetwork(state_dim, action_dim).to(kwargs['device'])
    else:
        raise KeyError('unknown env type')

    kwargs['action_dim'] = action_dim

    if kwargs['agent_type'] == 'ddqn':
        agent = DDQNAgentPER(net, target_net, **kwargs) if kwargs['use_prioritized_buffer'] else DDQNAgent(net, target_net, **kwargs)
    elif kwargs['agent_type'] == 'dqn':
        agent = DQNAgentPER(net, target_net, **kwargs) if kwargs['use_prioritized_buffer'] else DQNAgent(net, target_net, **kwargs)
    else:
        raise KeyError('Unknown agent type')

    dqn = DQN(env=env, agent=agent, **kwargs)
    scores, losses = dqn.train(kwargs['num_episodes'])

    # save agent
    dt = str(datetime.datetime.now().strftime("%m_%d_%Y_%I_%M_%p"))
    per = 'PER' if kwargs['use_prioritized_buffer'] else ''
    model_fname = kwargs['model_dir']+'/'+kwargs['env_type']+'/{}_agent_{}_{}.pt'.format(kwargs['agent_type'], per, dt)
    agent.save(model_fname)

    # save scores
    scores_fname = kwargs['reports_dir']+'/'+kwargs['env_type']+'/{}_agent_{}_{}'.format(kwargs['agent_type'], per, dt)
    np.save(scores_fname, np.array(scores))

    # save scores
    losses_fname = kwargs['reports_dir']+'/'+kwargs['env_type']+'/{}_agent_{}_loss_{}'.format(kwargs['agent_type'], per, dt)
    np.save(scores_fname, np.array(losses_fname))

    env.close()
    pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('run_name', type=str, default='Visual Banana Collector',
                        help='tag for current run')
    parser.add_argument('--env_file', type=str,
                        help='file path of Unity environment')
    parser.add_argument('--env_type', type=str,
                        help='visual or simple env')
    parser.add_argument('--model_dir', type=str, default='../data/models',
                        help='basedir for saving model weights')
    parser.add_argument('--reports_dir', type=str, default='../reports',
                        help='basedir for saving training reports')
    # train params
    parser.add_argument('--agent_type', type=str, default='dqn',
                        help='number of episodes to train an agent')
    parser.add_argument('--num_episodes', type=int, default=1000,
                        help='number of episodes to train an agent')
    parser.add_argument('--batch_size', type=int, default=64,
                        help='batch size')
    parser.add_argument('--lr', type=float, default=5e-4,
                        help='learning rate')
    parser.add_argument('--num_stacked_frames', type=int, default=4,
                        help='number of frames to stack for state representation')
    # replay buffer params
    parser.add_argument('--replay_buffer_size', type=int, default=10000,
                        help='size of the replay buffer')
    parser.add_argument('--use_prioritized_buffer', type=bool, default=False,
                        help='if set True, use prioritized experience replay buffer')
    parser.add_argument('--alpha', type=float, default=0.6,
                        help='alpha param for prioritized replay buffer')
    parser.add_argument('--beta', type=float, default=0.0,
                        help='beta param for prioritized replay buffer')
    parser.add_argument('--e', type=float, default=1e-8,
                        help='additive constant for priorities in prioritized replay buffer')
    # dqn params
    parser.add_argument('--tau', type=float, default=1e-3,
                        help='soft update for target networks')
    parser.add_argument('--update_every', type=int, default=4,
                        help='update target networks each n steps')
    # agent params
    parser.add_argument('--init_epsilon', type=float, default=1.0,
                        help='initial epsilon of the e-greedy policy')
    parser.add_argument('--epsilon_decay', type=float, default=0.995,
                        help='epsilon decay')
    parser.add_argument('--min_epsilon', type=float, default=0.01,
                        help='minimum of the epsilon')
    parser.add_argument('-gamma', type=float, default=0.99,
                        help='discount factor')
    # q_net params
    parser.add_argument('--hidden_size', type=int, default=128,
                        help='size of the hidden layer')
    parser.add_argument('--use_gpu', type=bool, default=True,
                        help='whether use gpu or not')

    args = parser.parse_args()
    train(**vars(args))

