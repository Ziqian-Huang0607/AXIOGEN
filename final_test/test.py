import pygame
import sys
import math
import neat
import os
import random
import pickle
import csv
import datetime

# --- PROJECT AXIOGEN: UNIVERSITY (V3 - METABOLIC TEST) ---

timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
log_filename = f"university_report_{timestamp}.csv"

class World:
    def __init__(self, mode):
        self.width, self.height = 800, 600
        self.mode = mode # 0: Harvester, 1: Snake, 2: Hunter
        self.walls = []
        self.foods = []
        self.goal_pos = [700, 300]
        self.setup_environment()

    def setup_environment(self):
        # Global Borders
        self.walls = [
            pygame.Rect(0, 0, 800, 15), pygame.Rect(0, 585, 800, 15),
            pygame.Rect(0, 0, 15, 600), pygame.Rect(785, 0, 15, 600)
        ]
        
        if self.mode == 0: # HARVESTER
            for _ in range(50):
                self.foods.append([random.randint(50, 750), random.randint(50, 550)])
        
        elif self.mode == 1: # THE SNAKE
            self.walls.append(pygame.Rect(0, 150, 600, 25))
            self.walls.append(pygame.Rect(200, 350, 600, 25))
            self.goal_pos = [100, 500]

        elif self.mode == 2: # THE HUNTER
            self.goal_pos = [random.randint(100, 700), random.randint(100, 500)]

    def update_hunter(self, frame):
        if self.mode == 2 and frame % 120 == 0:
            self.goal_pos = [random.randint(100, 700), random.randint(100, 500)]

class Agent:
    def __init__(self, x, y, genome, config):
        self.x, self.y = x, y
        self.angle = 0
        self.vel = 0
        self.alive = True
        self.score = 0
        
        # --- STAGE 4 GROUNDED STATES ---
        self.max_energy = 1000
        self.energy = 1000
        self.pain = 0.0
        self.has_key = True # Unlock logic for general navigation
        
        self.net = neat.nn.FeedForwardNetwork.create(genome, config)

    def drive(self, world):
        if not self.alive: return

        # 1. SENSE (12 Inputs for Stage 4 Brain)
        angles = [-45, -20, 0, 20, 45]
        radars = []
        for a in angles:
            radar_angle = math.radians(self.angle + a)
            end = (self.x + math.cos(radar_angle)*150, self.y + math.sin(radar_angle)*150)
            d = 150
            for w in world.walls:
                clip = w.clipline((self.x, self.y), end)
                if clip: d = min(d, math.hypot(clip[0][0]-self.x, clip[0][1]-self.y))
            radars.append(d)

        target = world.goal_pos if world.mode != 0 else (world.foods[0] if world.foods else [400,300])
        dist_t = math.hypot(target[0]-self.x, target[1]-self.y)
        ang_t = math.atan2(target[1]-self.y, target[0]-self.x) - math.radians(self.angle)
        
        # Assemble 12 Inputs: Radars(1-5), TargetDist(6), TargetAng(7), Aux(8-9), Key(10), Pain(11), Energy(12)
        inputs = [
            *[(150-r)/150 for r in radars], 
            dist_t/800, math.sin(ang_t), 
            0, 0, 
            1.0, 
            self.pain, 
            self.energy/self.max_energy
        ]
        
        # 2. THINK & MOVE
        out = self.net.activate(inputs)
        self.angle += out[1] * 10
        self.vel = max(-1, min(8, self.vel + out[0]*2))
        
        dx, dy = math.cos(math.radians(self.angle))*self.vel, math.sin(math.radians(self.angle))*self.vel
        self.pain = 0
        
        if pygame.Rect(self.x+dx-10, self.y+dy-10, 20, 20).collidelist(world.walls) == -1:
            self.x += dx
            self.y += dy
        else:
            self.vel = -2
            self.pain = 1.0 # Collision pain
        
        self.vel *= 0.92

        # 3. ENERGY LOGIC (The Sentinel Base Code)
        self.energy -= 1.5 # Constant metabolic drain
        if self.energy <= 0:
            self.alive = False

        # 4. SCORING & REFUELING
        if world.mode == 0: # Harvester
            for f in world.foods[:]:
                if math.hypot(f[0]-self.x, f[1]-self.y) < 25:
                    world.foods.remove(f)
                    self.score += 1
                    self.energy = min(self.max_energy, self.energy + 250) # Refuel!
        else: # Snake and Hunter
            if dist_t < 35:
                self.score += 1
                self.energy = min(self.max_energy, self.energy + 500) # Refuel!
                if world.mode == 2: world.update_hunter(120)

def run_test():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 20)

    try:
        with open('stage4_brain.pkl', 'rb') as f:
            brain_genome = pickle.load(f)
    except:
        print("Error: stage4_brain.pkl not found in this folder!")
        return

    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'config-feedforward.txt')
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                neat.DefaultSpeciesSet, neat.DefaultStagnation, config_path)

    results = []
    modes = ["PLANET A: HARVESTER", "PLANET B: SNAKE", "PLANET C: HUNTER"]
    
    with open(log_filename, mode='w', newline='') as f:
        csv.writer(f).writerow(["Planet", "Final Score", "Survival"])

    for m_idx in range(3):
        world = World(m_idx)
        agent = Agent(400, 500, brain_genome, config) # Spawn at bottom
        
        run_planet = True
        frame = 0
        while run_planet and frame < 1500:
            screen.fill((5, 5, 10))
            for event in pygame.event.get():
                if event.type == pygame.QUIT: pygame.quit(); sys.exit()

            world.update_hunter(frame)
            agent.drive(world)

            # Draw Walls
            for w in world.walls: pygame.draw.rect(screen, (60, 60, 80), w)
            # Draw Food/Goal
            for f in world.foods: pygame.draw.circle(screen, (255, 255, 0), f, 5)
            if world.mode != 0: pygame.draw.circle(screen, (0, 255, 100), world.goal_pos, 20)
            
            # Draw Agent (Color shows Energy level)
            health_color = int((agent.energy / agent.max_energy) * 255)
            color = (255 - health_color, health_color, 255) if agent.pain == 0 else (255, 0, 0)
            pygame.draw.circle(screen, color, (int(agent.x), int(agent.y)), 12)

            # UI - Energy Bar
            pygame.draw.rect(screen, (50, 50, 50), (20, 110, 200, 15))
            pygame.draw.rect(screen, (0, 255, 0), (20, 110, int(200 * (agent.energy/agent.max_energy)), 15))

            screen.blit(font.render(modes[m_idx], True, (255, 255, 255)), (20, 20))
            screen.blit(font.render(f"Score: {agent.score}", True, (255, 255, 0)), (20, 50))
            screen.blit(font.render(f"Life Support: {'ACTIVE' if agent.alive else 'OFFLINE'}", True, (0, 200, 255)), (20, 80))

            pygame.display.flip()
            clock.tick(60)
            frame += 1
            if not agent.alive: run_planet = False

        # Results
        status = "GRADUATED" if agent.alive and agent.score > 0 else "FAILED"
        results.append([modes[m_idx], agent.score, status])
        with open(log_filename, mode='a', newline='') as f:
            csv.writer(f).writerow([modes[m_idx], agent.score, status])

    print("\n--- AXIOGEN UNIVERSITY: DIPLOMA REPORT ---")
    for r in results:
        print(f"{r[0]}: Score {r[1]} | {r[2]}")
    pygame.quit()

if __name__ == "__main__":
    run_test()