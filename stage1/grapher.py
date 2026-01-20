import pandas as pd
import matplotlib.pyplot as plt
import glob
import os
import sys

# --- PROJECT AXIOGEN: AUTOMATED GRAPHER ---

def get_latest_csv():
    """Finds the most recent CSV file in the current directory."""
    # Look for files matching the pattern
    list_of_files = glob.glob('axiogen_*.csv') 
    
    if not list_of_files:
        print("Error: No 'axiogen_*.csv' files found in this folder.")
        sys.exit()
        
    # Sort by creation time to get the newest one
    latest_file = max(list_of_files, key=os.path.getctime)
    return latest_file

def generate_graph():
    # 1. Load the Data
    target_file = get_latest_csv()
    print(f"--- Analyzing Data Source: {target_file} ---")
    
    try:
        df = pd.read_csv(target_file)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return

    # 2. Setup the Plot Style (Professional/Scientific)
    plt.style.use('ggplot') # 'seaborn-darkgrid' is also good if installed
    plt.figure(figsize=(12, 6)) # Width, Height in inches

    # 3. Plot the Lines
    # The 'Champion' (Max Fitness)
    plt.plot(df['Generation'], df['Max Fitness'], 
             color='#d62728', linewidth=2, label='Champion Fitness (Max)')
    
    # The 'Population' (Average Fitness)
    plt.plot(df['Generation'], df['Avg Fitness'], 
             color='#1f77b4', linewidth=2, linestyle='--', label='Average Population Fitness')

    # 4. Fill the area between them (Visualizing the "Skill Gap")
    plt.fill_between(df['Generation'], df['Avg Fitness'], df['Max Fitness'], 
                     color='gray', alpha=0.1)

    # 5. Add Labels and Titles
    plt.title(f"Evolutionary Trajectory: {target_file}", fontsize=14)
    plt.xlabel("Generations (Time)", fontsize=12)
    plt.ylabel("Fitness Score (Intelligence)", fontsize=12)
    plt.legend(loc='upper left')
    plt.grid(True, which='both', linestyle='--', linewidth=0.5)
    
    # Add a zero line for reference (in case fitness dips below zero)
    plt.axhline(0, color='black', linewidth=1)

    # 6. Save and Show
    output_filename = target_file.replace('.csv', '_graph.png')
    plt.savefig(output_filename, dpi=300) # 300 DPI is print quality for papers
    print(f"Graph saved to: {output_filename}")
    
    plt.show() # Pop up the window

if __name__ == "__main__":
    generate_graph()