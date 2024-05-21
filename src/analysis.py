import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import numpy as np
from enum import Enum
from map_tools import MapTools
import argparse
import os
import shutil
import logging

episodes = [5000, 7500, 10000]
#episodes = [7500]
size = 12
seed = 63
filename = f'{size}x{size}-seed{seed}'
inputFolder = './experiments/02-full'
resultsPath = './analysis-output'
experiments_input_path = './input'

class DataKind(Enum):
    REWARD = 'reward'
    POLICY = 'policy'
    
class ExperimentKind(Enum):
    SYNTHETIC_ALL = 'all'
    SYNTHETIC_HOLES = 'holes'
    HUMAN_5 = 'human5'
    HUMAN_10 = 'human10'

def loadData(experiment_kind, episode_number, data_kind):
    df_random = pd.read_csv(f'{inputFolder}/{experiment_kind}/{episode_number}/{data_kind.value}_data/random/{filename}.csv', header=None)
    df_no_advice = pd.read_csv(f'{inputFolder}/{experiment_kind}/{episode_number}/{data_kind.value}_data/noadvice/{filename}.csv', header=None)
    df_advice_00 = pd.read_csv(f'{inputFolder}/{experiment_kind}/{episode_number}/{data_kind.value}_data/advice/{filename}-u-0.01.csv', header=None)
    df_advice_02 = pd.read_csv(f'{inputFolder}/{experiment_kind}/{episode_number}/{data_kind.value}_data/advice/{filename}-u-0.2.csv', header=None)
    df_advice_04 = pd.read_csv(f'{inputFolder}/{experiment_kind}/{episode_number}/{data_kind.value}_data/advice/{filename}-u-0.4.csv', header=None)
    df_advice_06 = pd.read_csv(f'{inputFolder}/{experiment_kind}/{episode_number}/{data_kind.value}_data/advice/{filename}-u-0.6.csv', header=None)
    df_advice_08 = pd.read_csv(f'{inputFolder}/{experiment_kind}/{episode_number}/{data_kind.value}_data/advice/{filename}-u-0.8.csv', header=None)
    df_advice_10 = pd.read_csv(f'{inputFolder}/{experiment_kind}/{episode_number}/{data_kind.value}_data/advice/{filename}-u-1.0.csv', header=None)
    
    return {
        'random': df_random,
        'no_advice': df_no_advice,
        'advice_00': df_advice_00,
        'advice_02': df_advice_02,
        'advice_04': df_advice_04,
        'advice_06': df_advice_06,
        'advice_08': df_advice_08,
        'advice_10': df_advice_10
    }
    
def savefig(plot_name):
    plt.gcf().tight_layout()
    plt.savefig(f'{resultsPath}/{plot_name}.pdf')

def cumulative_reward():
    folder_name = 'cumulative_reward'
    os.mkdir(f'{resultsPath}/{folder_name}')
    
    for experiment_kind in ExperimentKind:
        experiment_kind = experiment_kind.value
        
        logging.info(f'Running analysis cumulative_reward with experiment kind {experiment_kind}')
        
        os.mkdir(f'{resultsPath}/{folder_name}/{experiment_kind}')
    
        for episode_number in episodes:
            logging.info(f'Running analysis cumulative_reward with episode_number {episode_number}')
            
            dfs = loadData(experiment_kind, episode_number, DataKind.REWARD)
            
            fig = plt.figure()
            ax = plt.gca()
            
            for df_name, df in dfs.items():
                mean = df.mean()
                #std = df.std()
                x = np.arange(len(mean))
                plt.plot(x, mean, label=df_name)
                #plt.fill_between(x, mean - std, mean + std, alpha=0.2)
            
            plt.xlabel('Episode')
            plt.ylabel('Cumulative Reward')
            plt.legend()
            #plt.show()
            
            logging.info('\tSave linear plot')
            savefig(f'{folder_name}/{experiment_kind}/cumulative_reward-{experiment_kind}-{episode_number}-linear')
            
            logging.info('\tSave log plot')
            plt.yscale('log')
            savefig(f'{folder_name}/{experiment_kind}/cumulative_reward-{experiment_kind}-{episode_number}-log')

def heatmap():

    folder_name = 'heatmaps'
    os.mkdir(f'{resultsPath}/{folder_name}')
    
    for episode_number in episodes:
        logging.info(f'Running analysis heatmap with episode_number {episode_number}')
    
        dfs = loadData(episode_number, DataKind.POLICY)
        
        logging.debug(dfs['advice_00'])
        df = dfs['advice_00'].mean().to_frame() # TODO: should process every dataframe (rand, unadvised, and every advised (every level of u))
        
        jss = []
        for i in range(0, 144):
            jss.append([i, i, i, i])
        cellids = [j for js in jss for j in js]
        
        df.insert(0, 'cellid', cellids)
        df.columns.values[1] = 'prob'
        
        dss = []
        for d in range(0, 144):
            dss.append(['←', '↓', '→', '↑'])
            #dss.append(['L', 'D', 'R', 'U'])
        directions = [d for ds in dss for d in ds]
        
        df['direction'] = directions
        
        logging.debug(df)
        
        df = df.sort_values('prob', ascending=False).drop_duplicates(['cellid'])
        df = df.sort_values('cellid', ascending=True).reset_index(drop=True)
        #df = df.drop(['cellid'], axis=1)
        
        size = 12
        seed = 63
        
        df = df.assign(row = lambda x: (x['cellid'] // 12))
        df = df.assign(col = lambda x: (x['cellid'] % 12))
        
        map_description = MapTools(experiments_input_path).parse_map(size, seed)
        logging.debug(map_description)
        
        terminals = []
        for rid, row in enumerate(map_description):
            for cell in range(0, len(row)):
                #logging.debug(row[cell])
                if row[cell] in ('H', 'G'):
                    terminals.append(size*rid+cell)
                    
        for t in terminals:
            df.loc[t, 'prob'] = 0.0
            df.loc[t, 'direction'] = ''
            
        df = df.loc[df['prob'] !=0.25]
        df = df.loc[df['prob'] !=0.0]
        
        logging.debug(df)
        
        result = df.pivot(index='row', columns='col', values='prob')
        logging.debug(result)
        
        directions = df.pivot(index='row', columns='col', values='direction')
        logging.debug(directions)

        sns.heatmap(
            result,
            linewidths=0.001,
            linecolor='gray',
            annot=directions,
            fmt='',
            cmap=sns.color_palette("Blues", as_cmap=True),
            vmin=0.0,
            vmax=1.0,
            xticklabels=[],
            yticklabels=[],
            annot_kws={"fontsize": "x-large"}
        )
        #plt.show()
        logging.info('\tSave heatmap')
        savefig(f'{folder_name}/heatmap-{episode_number}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', type=str)
    parser.add_argument('-s','--stash', help='Stash results folder.', )
    
    parser.add_argument(
        "-log",
        "--log",
        default="warning",
        help=("Provide logging level. "
              "Example '--log debug', default='warning'."
              )
        )
    options = parser.parse_args()
    
    levels = {
        'critical': logging.CRITICAL,
        'error': logging.ERROR,
        'warn': logging.WARNING,
        'warning': logging.WARNING,
        'info': logging.INFO,
        'debug': logging.DEBUG
    }
    level = levels.get(options.log.lower())
    
    logging.basicConfig(format='[%(levelname)s] %(message)s')
    logging.getLogger().setLevel(level)
        
    if options.stash:
        logging.info('Previous analysis output folder will be stashed.')
        if os.path.exists(resultsPath) and os.path.isdir(resultsPath):
            shutil.rmtree(resultsPath)
        os.mkdir(resultsPath)
    
    all_analyses = ['cumulative_reward', 'heatmap']
    
    if not options.a:
        logging.info('Running all')
        for analysis in all_analyses:
            exec(f'{analysis}()')
        
    else:
        logging.info(f'Running analysis {options.a}.')
        exec(f'{options.a}()')


"""
    def plot_success_rate(self, no_advice_success_rates, advice_success_rates, human_input):
        logging.getLogger().setLevel(logging.INFO)
        plt.plot(no_advice_success_rates, label='No advice')
        plt.plot(advice_success_rates, label='Advice')
        plt.title(f'Map: {self._MAP_NAME}; eps={str(self._MAX_EPISODES)}; exps={str(self._NUM_EXPERIMENTS)}; u={round(human_input.u, 4)}.')
        plt.xlabel('Iteration')
        plt.ylabel('Success Rate %')
        plt.legend()
        
        filename = f'{self.get_file_name(extension="pdf", advice_explicit=False, u_explicit=True, human_input=human_input, extra="SUCCESSRATE")}'
        
        plt.savefig(filename, format='pdf', bbox_inches='tight')
        #plt.show()
        
    def plot_steps(self, all_steps, human_input):
        logging.debug(f'all_steps: {all_steps}')
        w = wilcoxon(all_steps.iloc[:, 0], all_steps.iloc[:, 1])
        logging.debug(f'Wilcoxon: {w}')
        
        logging.getLogger().setLevel(logging.INFO)
        
        fig = plt.figure()
        
        ax = fig.add_subplot(111)
        ax.boxplot(all_steps)
        
        ax.set_title(f'Map: {self._MAP_NAME}; eps={str(self._MAX_EPISODES)}; exps={str(self._NUM_EXPERIMENTS)}; ; u={round(human_input.u, 4)}; p={round(w.pvalue, 4)}.')
        ax.set_xlabel('Mode')
        ax.set_ylabel('Steps')
        ax.set_xticklabels(all_steps.columns)
        
        filename = f'{self.get_file_name(extension="pdf", advice_explicit=False, u_explicit=True, human_input=human_input, extra="STEPS")}'
        
        plt.savefig(filename, format='pdf', bbox_inches='tight')
        #plt.show()
"""
    
    

