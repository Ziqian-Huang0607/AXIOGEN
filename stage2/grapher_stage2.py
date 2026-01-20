import pandas as pd
import matplotlib.pyplot as plt
import glob
import os
import sys

# --- PROJECT AXIOGEN: STAGE 2 VISUALIZER ---

def get_latest_stage2_csv():
    """Finds the most recent Stage 2 CSV file."""
    list_of_files = glob.glob('axiogen_stage2_*.csv') 
    if not list_of_files:
        print("Error: No 'axiogen_stage2_*.csv' files found.")
        sys.exit()
    return max(list_of_files, key=os.path.getctime)

def plot_stage2():
    target_file = get_latest_stage2_csv()
    print(f"--- Plotting Stage 2 Data: {target_file} ---")
    
    try:
        df = pd.read_csv(target_file)
    except Exception as e:
        print(f"Error: {e}")
        return

    # Create a figure with two subplots (Top for Fitness, Bottom for Survival)
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True)
    plt.subplots_adjust(hspace=0.3)

    # --- PLOT 1: EXPLORATION SCORE ---
    ax1.plot(df['Generation'], df['Max Exploration'], 
             color='#00ced1', linewidth=2.5, label='Max Exploration (Genius)')
    ax1.plot(df['Generation'], df['Avg Exploration'], 
             color='#1f77b4', linewidth=1.5, linestyle='--', label='Average Exploration')
    
    # Shade the "Diversity Gap"
    ax1.fill_between(df['Generation'], df['Avg Exploration'], df['Max Exploration'], 
                     color='#00ced1', alpha=0.1)
    
    ax1.set_title("Stage 2: Emergence of Curiosity (Exploration Score)", fontsize=14, fontweight='bold')
    ax1.set_ylabel("Grid Sectors Discovered", fontsize=12)
    ax1.legend(loc='upper left')
    ax1.grid(True, linestyle='--', alpha=0.6)

    # --- PLOT 2: SURVIVAL RATE ---
    # We use a step plot or bar to show how many survived the maze/boredom
    ax2.fill_between(df['Generation'], df['Alive Count'], color='#ff7f0e', alpha=0.3)
    ax2.plot(df['Generation'], df['Alive Count'], color='#d62728', linewidth=2, label='Agents Alive')
    
    ax2.set_title("Survival Rate (Maze Navigation & Boredom Limit)", fontsize=14, fontweight='bold')
    ax2.set_xlabel("Generations", fontsize=12)
    ax2.set_ylabel("Alive Count (of 30)", fontsize=12)
    ax2.set_ylim(0, 32)
    ax2.legend(loc='upper left')
    ax2.grid(True, linestyle='--', alpha=0.6)

    # Save the result
    output_png = target_file.replace('.csv', '_analysis.png')
    plt.savefig(output_png, dpi=300)
    print(f"Analysis saved to: {output_png}")
    
    plt.show()

if __name__ == "__main__":
    plot_stage2()