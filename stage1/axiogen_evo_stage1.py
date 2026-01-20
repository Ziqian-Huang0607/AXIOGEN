#better to crash than starve
# Trotsky Protocol: Hunger is constant. Stagnation is death.
# Continued Revolution: The goalpost moves immediately!
import pygame
import xml.etree.ElementTree as ET
import sys
import math
import neat
import os
import random
import pickle
import csv
import datetime

# --- PROJECT AXIOGEN: STAGE 1 (FAIL-SAFE EDITION) ---

timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
log_filename = f"axiogen_stage1_{timestamp}.csv"
# We use a constant filename for the autosave so it updates every gen
autosave_filename = f"axiogen_stage1_AUTOSAVE.pkl" 

with open(log_filename, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["Generation", "Max Fitness", "Avg Fitness", "Alive Count"])

print("--- STAGE 1: FAIL-SAFE PROTOCOL ---")
print(f" > Model will AUTO-SAVE every generation to: {autosave_filename}")

class World:
    def __init__(self, xml_file):
        self.tree = ET.parse(xml_file)
        self.root = self.tree.getroot()
        self.width = int(self.root.get('width', 800))
        self.height = int(self.root.get('height', 600))
        physics_params = self.root.find('physics')
        self.friction = float(physics_params.get('friction', 0.95))
        
        self.foods = []
        for _ in range(40): 
            self.foods.append([
                random.randint(20, self.width - 20),
                random.randint(20, self.height - 20)
            ])

    def respawn_food(self, index):
        self.foods[index] = [
            random.randint(20, self.width - 20),
            random.randint(20, self.height - 20)
        ]

class Agent:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 12
        self.angle = random.randint(0, 360) 
        self.vel = 0
        self.alive = True
        self.max_energy = 400 
        self.energy = self.max_energy
        self.color = (0, 255, 0)
        self.radars = [] 

    def move(self, friction, speed_output, turn_output):
        if not self.alive: return
        self.angle += turn_output * 10 
        self.vel += speed_output * 3    
        if self.vel > 10: self.vel = 10 
        if self.vel < -2: self.vel = -2 
        rad = math.radians(self.angle)
        self.x += math.cos(rad) * self.vel
        self.y += math.sin(rad) * self.vel
        self.vel *= friction
        self.energy -= 1.5 
        if self.energy <= 0: self.alive = False 
        green_val = max(0, min(255, int((self.energy / self.max_energy) * 255)))
        red_val = 255 - green_val
        self.color = (red_val, green_val, 0)

    def sense(self, world):
        angles = [-40, -20, 0, 20, 40]
        self.radars = []
        for a in angles:
            radar_angle = math.radians(self.angle + a)
            reading = 250 
            for food in world.foods:
                dist = math.hypot(food[0] - self.x, food[1] - self.y)
                if dist < 250:
                    food_angle = math.atan2(food[1] - self.y, food[0] - self.x)
                    diff = abs(food_angle - radar_angle)
                    while diff > math.pi: diff -= 2*math.pi
                    while diff < -math.pi: diff += 2*math.pi
                    if abs(diff) < 0.2: 
                        if dist < reading: reading = dist
            self.radars.append(reading)

    def draw(self, screen):
        if not self.alive: return
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
        nose_x = self.x + math.cos(math.radians(self.angle)) * self.radius
        nose_y = self.y + math.sin(math.radians(self.angle)) * self.radius
        pygame.draw.line(screen, (255, 255, 255), (int(self.x), int(self.y)), (nose_x, nose_y), 2)

generation = 0
best_genome = None

def eval_genomes(genomes, config):
    global generation, best_genome
    generation += 1
    
    pygame.init()
    # Check for World File
    if not os.path.exists('world_alpha.xml'):
        # Fallback if file missing
        with open('world_alpha.xml', 'w') as f:
            f.write('<world width="800" height="600"><physics friction="0.95"/><entities><food x="100" y="100" energy="50"/></entities></world>')

    world = World('world_alpha.xml')
    screen = pygame.display.set_mode((world.width, world.height))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 18)

    nets = []
    ge = []
    agents = []

    for genome_id, genome in genomes:
        genome.fitness = 0 
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        nets.append(net)
        ge.append(genome)
        spawn_x = (world.width // 2) + random.randint(-200, 200)
        spawn_y = (world.height // 2) + random.randint(-200, 200)
        agents.append(Agent(spawn_x, spawn_y))

    for frame in range(1200): 
        screen.fill((10, 10, 10))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        alive_agents = 0
        for i, agent in enumerate(agents):
            if not agent.alive: continue
            alive_agents += 1
            agent.sense(world)
            inputs = [(250.0 - x) / 250.0 for x in agent.radars]
            output = nets[i].activate(inputs)
            agent.move(world.friction, output[0], output[1])
            if agent.vel < 3: 
                ge[i].fitness -= 0.1 
                agent.energy -= 2    
            for idx, food in enumerate(world.foods):
                dist = math.hypot(agent.x - food[0], agent.y - food[1])
                if dist < 20: 
                    ge[i].fitness += 10 
                    agent.energy = agent.max_energy 
                    world.respawn_food(idx)
                    break
            if agent.x < 5 or agent.x > world.width-5 or agent.y < 5 or agent.y > world.height-5:
                ge[i].fitness -= 5 
                agent.alive = False

        if alive_agents == 0: break

        for food in world.foods:
            pygame.draw.circle(screen, (255, 215, 0), (food[0], food[1]), 5)
        for agent in agents:
            agent.draw(screen)
        
        # Display Stats
        text = font.render(f"Gen: {generation} | Alive: {alive_agents}", True, (255, 255, 255))
        screen.blit(text, (10, 10))
        pygame.display.flip()
        clock.tick(60)

    # --- SAVE STATS & MODEL EVERY GENERATION ---
    current_best = max(ge, key=lambda x: x.fitness)
    
    # Save CSV
    all_fitness = [g.fitness for g in ge]
    if len(all_fitness) > 0:
        max_fit = max(all_fitness)
        avg_fit = sum(all_fitness) / len(all_fitness)
    else: max_fit, avg_fit = 0, 0
    
    with open(log_filename, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([generation, max_fit, avg_fit, alive_agents])
    
    # AUTO-SAVE MODEL
    print(f" > Gen {generation} Complete. Saving backup...")
    with open(autosave_filename, 'wb') as f:
        pickle.dump(current_best, f)

def run(config_path):
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                neat.DefaultSpeciesSet, neat.DefaultStagnation,
                                config_path)
    p = neat.Population(config)
    p.add_reporter(neat.StdOutReporter(True))
    p.add_reporter(neat.StatisticsReporter())

    try:
        # Run safely
        winner = p.run(eval_genomes, 100)
        
        # Final Save
        final_name = f"axiogen_stage1_FINAL_{timestamp}.pkl"
        with open(final_name, 'wb') as f:
            pickle.dump(winner, f)
        print(f"VICTORY. Saved to {final_name}")
        
    except Exception as e:
        print(f"\nSimulation Stopped: {e}")
        print(f"Don't worry! The latest model is saved in: {autosave_filename}")

if __name__ == "__main__":
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'config-feedforward.txt')
    run(config_path)