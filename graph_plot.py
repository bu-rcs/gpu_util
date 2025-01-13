#%%
import pandas as pd
import seaborn as sns
from matplotlib import style
import matplotlib.pyplot as plt




#%%
def plot_job_classification(x, title, subtitle):
    # Create a plot

    # parameters
    plt.rcParams['font.family'] = "roboto"
    style.use('fivethirtyeight')
    sns.set(style="whitegrid")
    ax = sns.barplot(x=x.index.astype(str), 
                 y=x.values, 
                 palette="Set2", 
                 hue=x.index.astype(str), 
                 legend=False)
  
    # Add text labels to each bar
    for i, value in enumerate(x.values):
        percent = round(100*value/x.values.sum())
        ax.text(i, 
            value + 0.05, 
            f'{value:,}' + " (" + str(percent) + "%)" , 
            ha='center', 
            va='bottom', 
            fontsize=12)

        plt.ylim(0, x.values.max()*1.1)

    # Set the main title
    plt.suptitle(
        title,  
        fontsize=18,  # Set the font size
        color="black",  # Set the color
        x=0.51,  # Adjust this to align with the subtitle
        y=1.01,  # Adjust this to align with the subtitle
    )

    # Set the subtitle
    plt.title(
        subtitle,  
        fontsize=14,  # Set the font size
        color="grey",  # Set the color
    )

    plt.xlabel("Type of Job")
    plt.ylabel("Count")
    plt.xticks([0, 1], labels=['Batch', 'Interactive'])  # Labeling True and False explicitly
    plt.show()

#%%


#%%
def plot_job_time_classification(x, title, subtitle):
    # Create a plot

    # parameters
    plt.rcParams['font.family'] = "roboto"
    style.use('fivethirtyeight')
    sns.set(style="whitegrid")
    ax = sns.barplot(x= x.index.astype(str), 
                 y= x.values, 
                 palette= "Set2", 
                 hue= x.index.astype(str), 
                 legend= False)
  
    # Add text labels to each bar
    for i, value in enumerate(x.values):
        percent = round(100*value/x.values.sum())
        ax.text(i, 
            value + 0.05, 
            f'{value:,}' + " (" + str(percent) + "%)" , 
            ha='center', 
            va='bottom', 
            fontsize=12)

        plt.ylim(0, x.values.max()*1.1)

    # Set the main title
    plt.suptitle(
        title,  
        fontsize=18,  # Set the font size
        color="black",  # Set the color
        x=0.51,  # Adjust this to align with the subtitle
        y=1.01,  # Adjust this to align with the subtitle
    )

    # Set the subtitle
    plt.title(
        subtitle,  
        fontsize=14,  # Set the font size
        color="grey",  # Set the color
    )

    plt.xlabel("Type of Job")
    plt.ylabel("Time, hours")
    plt.xticks([0, 1], labels=['Batch', 'Interactive'])  # Labeling True and False explicitly
    plt.show()

