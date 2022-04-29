import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
 

def plot_this(filename):
    df = pd.read_csv(filename)

    #print(df[['Reboot Period','non-secboot sched']].head())
    sns.set(font_scale=3, rc={'figure.figsize':(14,7.5)})
    sns.set_style('ticks')
    plot = sns.lineplot(data=df[['normal reboot sched', 'secboot sched']],
                 dashes=False, palette=['C1', 'C0'])
    plot.set(xlabel="Percent Overhead", ylabel='Weighted Schedulability')
    plot.set_xlim(0, 100)
    plot.legend(labels=['NormalReboot', 'SecureReboot'])
    plot.set_xticks([10*i for i in range(11)])
    plot.set_ylim(0, 1.1)
    plot.set_yticks([round(i,1) for i in np.arange(0.1, 1.1, 0.1)])
    plt.tight_layout()

    plt.savefig("RM_weight_sched_var_e_overhead.eps", format='eps')

    #sns.lineplot(data=df, x='Reboot Period', y='non-secboot sched')
    plt.show()

plot_this("weighted_var_e_rm.csv")
